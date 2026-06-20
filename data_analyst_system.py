from __future__ import annotations

import dspy
import openai
import numpy as np
import pandas as pd
from httpx import Client
import os

# ---------------------------------------------------------------------------
# httpx compatibility shim (applied once at import time).
# Some dspy/openai versions pass a now-unsupported `proxies` kwarg to
# httpx.Client. Patching once here avoids re-wrapping Client.__init__ on every
# request (the old per-call patch stacked wrappers and leaked memory).
# ---------------------------------------------------------------------------
if not getattr(Client, "_prysm_proxies_patched", False):
    _original_client_init = Client.__init__

    def _patched_client_init(self, *args, **kwargs):
        kwargs.pop("proxies", None)
        _original_client_init(self, *args, **kwargs)

    Client.__init__ = _patched_client_init
    Client._prysm_proxies_patched = True


def summarize_dataset(dataset: "pd.DataFrame", sample_rows: int = 8) -> str:
    """Build a compact, token-safe textual summary of a dataframe.

    Passing an entire dataset via ``df.to_string()`` to every agent blows past
    the model context window for anything but tiny CSVs. Instead we give the
    agents the column names, dtypes, and a small sample of rows so they can
    write correct code against a dataframe named ``df``.
    """
    lines = [
        "Dataframe name: df",
        f"Shape: {dataset.shape[0]} rows x {dataset.shape[1]} columns",
        "",
        "Columns (name: dtype):",
    ]
    for column in dataset.columns:
        lines.append(f"  - {column}: {dataset[column].dtype}")
    lines.append("")
    lines.append(f"Sample rows (first {min(sample_rows, len(dataset))}):")
    lines.append(dataset.head(sample_rows).to_string())
    return "\n".join(lines)


class PlannerAgent(dspy.Signature):
    """ You are a data analytics planner agent. Your task is to create a strategic plan for achieving a user-defined goal using the user defined goal and agents. You have access to two key inputs:
          Data Agent Descriptions: A list of available data agents, each with a specific function or capability.
          User-Defined Goal: The end objective that the user wants to accomplish using the available datasets and agents.

        Task:
          1. Develop a comprehensive plan to achieve the user-defined goal. You will determine which agents and datasets to use in a sequence that best achieves the goal.
          2. If the goal appears infeasible or unclear, request further clarification or additional details from the user to refine the goal.

        output format:
          plan: Agent1 -> Agent2 -> Agent3 (e.g., Agent1 -> Agent3)
          plan_desc: Provide a detailed explanation of why each agent is selected in sequence. Describe how each agent contributes to achieving the goal.
          You are not required to use all the agents available in every response. Use only the relevant agents necessary for achieving the goal.

    """
    Agent_desc = dspy.InputField(desc="The agents available in the system")
    goal = dspy.InputField(desc="The user defined goal ")
    plan = dspy.OutputField(desc="The plan that would achieve the user defined goal")
    plan_desc = dspy.OutputField(desc="The reasoning behind the chosen plan")


class preprocessing_agent(dspy.Signature):
    """ You are a Data Pre-processing Agent. Using Numpy and Pandas, create an EDA pipeline based on a user-defined goal and the available datasets. Clean the data (handle missing values, outliers, duplicates), transform it (scaling, encoding), and generate basic analysis (summary statistics, correlations, visualizations if needed). Output the Python code for the full pipeline, with brief comments explaining each step."""
    dataset = dspy.InputField(desc="Available datasets loaded in the system, use this df_name,columns  set df as copy of df_name")
    goal = dspy.InputField(desc="The user defined goal ")
    code = dspy.OutputField(desc="The code that does the data preprocessing and introductory analysis")


class statistical_analytics_agent(dspy.Signature):
    """ You are a Statistical Analytics Agent. Using Statsmodels, analyze the dataset to achieve the user-defined goal. Choose the appropriate statistical method (e.g., regression, hypothesis testing), preprocess the data if needed, and generate Python code for model fitting and analysis (e.g., p-values, confidence intervals). Include comments explaining each step."""
    dataset = dspy.InputField(desc="Available datasets loaded in the system, use this df_name,columns  set df as copy of df_name")
    goal = dspy.InputField(desc="The user defined goal for the analysis to be performed")
    commentary = dspy.OutputField(desc="The comments about what analysis is being performed")
    code = dspy.OutputField(desc="The code that does the statistical analysis using statsmodel")


class Data_Viz(dspy.Signature):
    """
    You are an AI Agent using Plotly to create visualizations based on a user-defined goal and dataset. Identify the relevant data, generate the appropriate visualizations (e.g., bar charts, scatter plots), and output the Python code with necessary customizations. If required data is missing, state:
    "The dataset does not contain the necessary columns or information to generate the requested visualization."
    """
    dataset = dspy.InputField(desc=" Provides information about the data in the data frame. Only use column names and dataframe_name as in this context")
    goal = dspy.InputField(desc="user defined goal which includes information about data and chart they want to plot")
    commentary = dspy.OutputField(desc="The comments about what analysis is being performed")
    code = dspy.OutputField(desc="Plotly code that visualizes what the user needs according to the query & dataframe_index & styling_context")


class code_combiner_agent(dspy.Signature):
    """ You are a Code Combine Agent. Combine Python code from multiple agents into a single, error-free script. Fix any syntax, logical, or compatibility issues, optimize for efficiency, and remove redundancy. Output the final, well-commented Python code. """
    agent_code_list = dspy.InputField(desc="A list of code given by each agent")
    code = dspy.OutputField(desc="Refined complete code base")


class DataAnalyst(dspy.Module):
    def __init__(self, agents):
        self.agents = {}
        self.agent_desc = []
        for agent in agents:
            # Use the class __name__ — simple and reliable
            name = agent.__name__
            self.agents[name] = dspy.ChainOfThought(agent)
            # Use the docstring as the description so the planner knows what each agent does
            doc = (agent.__doc__ or "").strip().replace("\n", " ")
            self.agent_desc.append(f"{name}: {doc}")
        self.planner = dspy.ChainOfThought(PlannerAgent)
        self.combiner = dspy.ChainOfThought(code_combiner_agent)

    def _resolve_agent_name(self, raw_name: str) -> str | None:
        """Find the closest matching agent key (case-insensitive, strip spaces)."""
        name = raw_name.strip()
        # Exact match first
        if name in self.agents:
            return name
        # Case-insensitive match
        lower = name.lower()
        for key in self.agents:
            if key.lower() == lower:
                return key
        # Partial / substring match
        for key in self.agents:
            if lower in key.lower() or key.lower() in lower:
                return key
        return None

    def forward(self, dataset, query):
        # Compact, token-safe view of the data shared with every agent.
        dataset_summary = summarize_dataset(dataset)

        # Step 1: Planner decides which agents to run and in what order
        execution_plan = self.planner(
            Agent_desc="\n".join(self.agent_desc),
            goal=query,
        )

        agent_list = execution_plan.plan.split("->")
        combined_code = ""
        # Expose the planner result so the API/UI can render the execution plan.
        agent_outputs = {"PlannerAgent": execution_plan}

        # Step 2: Run each agent in the planned sequence
        for raw_name in agent_list:
            resolved = self._resolve_agent_name(raw_name)
            if resolved is None:
                # Planner hallucinated a name — skip gracefully
                continue
            agent = self.agents[resolved]
            result = agent(dataset=dataset_summary, goal=query)
            agent_outputs[resolved] = result
            combined_code += getattr(result, "code", "") + "\n\n"

        # Step 3: Combine all agent code into one clean script
        final_code = self.combiner(agent_code_list=combined_code)
        return final_code.code, agent_outputs
