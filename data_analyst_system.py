import dspy
import openai
import numpy as np
import pandas as pd
from httpx import Client
import os

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
    Agent_desc = dspy.InputField(desc= "The agents available in the system")
    goal = dspy.InputField(desc="The user defined goal ")
    plan = dspy.OutputField(desc="The plan that would achieve the user defined goal")
    plan_desc= dspy.OutputField(desc="The reasoning behind the chosen plan")

class preprocessing_agent(dspy.Signature):
    """ You are a Data Pre-processing Agent. Using Numpy and Pandas, create an EDA pipeline based on a user-defined goal and the available datasets. Clean the data (handle missing values, outliers, duplicates), transform it (scaling, encoding), and generate basic analysis (summary statistics, correlations, visualizations if needed). Output the Python code for the full pipeline, with brief comments explaining each step."""
    dataset = dspy.InputField(desc="Available datasets loaded in the system, use this df_name,columns  set df as copy of df_name")
    goal = dspy.InputField(desc="The user defined goal ")
    code = dspy.OutputField(desc ="The code that does the data preprocessing and introductory analysis")

class statistical_analytics_agent(dspy.Signature):
    """ You are a Statistical Analytics Agent. Using Statsmodels, analyze the dataset to achieve the user-defined goal. Choose the appropriate statistical method (e.g., regression, hypothesis testing), preprocess the data if needed, and generate Python code for model fitting and analysis (e.g., p-values, confidence intervals). Include comments explaining each step."""
    dataset = dspy.InputField(desc="Available datasets loaded in the system, use this df_name,columns  set df as copy of df_name")
    goal = dspy.InputField(desc="The user defined goal for the analysis to be performed")
    commentary = dspy.OutputField(desc="The comments about what analysis is being performed")
    code = dspy.OutputField(desc ="The code that does the statistical analysis using statsmodel")

class Data_Viz(dspy.Signature):
    """
    You are an AI Agent using Plotly to create visualizations based on a user-defined goal and dataset. Identify the relevant data, generate the appropriate visualizations (e.g., bar charts, scatter plots), and output the Python code with necessary customizations. If required data is missing, state:  
    "The dataset does not contain the necessary columns or information to generate the requested visualization."
    """
    dataset = dspy.InputField(desc=" Provides information about the data in the data frame. Only use column names and dataframe_name as in this context")
    goal = dspy.InputField(desc="user defined goal which includes information about data and chart they want to plot")
    commentary = dspy.OutputField(desc="The comments about what analysis is being performed")
    code= dspy.OutputField(desc="Plotly code that visualizes what the user needs according to the query & dataframe_index & styling_context")

class code_combiner_agent(dspy.Signature):
    """ You are a Code Combine Agent. Combine Python code from multiple agents into a single, error-free script. Fix any syntax, logical, or compatibility issues, optimize for efficiency, and remove redundancy. Output the final, well-commented Python code. """
    agent_code_list =dspy.InputField(desc="A list of code given by each agent")
    code = dspy.OutputField(desc="Refined complete code base")


class DataAnalyst(dspy.Module):
    def __init__(self, agents):
        self.agents = {}
        self.agent_desc = []
        for agent in agents:
            name = agent.__pydantic_core_schema__['schema']['model_name']
            self.agents[name] = dspy.ChainOfThought(agent)
            self.agent_desc.append(str(agent.__pydantic_core_schema__['cls']))
        self.planner = dspy.ChainOfThought(PlannerAgent)
        self.combiner = dspy.ChainOfThought(code_combiner_agent)

    def forward(self, dataset, query):

        original_client_init = Client.__init__
        def patched_client_init(self, *args, **kwargs):
            kwargs.pop("proxies", None)
            original_client_init(self, *args, **kwargs)
        Client.__init__ = patched_client_init

        plan_input = {
            'Agent_desc': str(self.agent_desc),
            'goal': query
        }
        
        execution_plan = self.planner(plan_input)
        agent_list = execution_plan.plan.split('->')
        combined_code = ""
        agent_outputs = {}

        for agent_name in agent_list:
            name = agent_name.strip()
            agent = self.agents[name]
            result = agent(dataset=dataset.to_string(), goal=query)
            agent_outputs[name] = result
            combined_code += result.code

        final_code = self.combiner(agent_code_list=combined_code)
        return final_code.code, agent_outputs