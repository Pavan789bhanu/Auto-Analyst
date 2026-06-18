import json
import os
import sys
from typing import Any

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_analyst_system import (
    DataAnalyst,
    Data_Viz,
    preprocessing_agent,
    statistical_analytics_agent,
)

_analyst: DataAnalyst | None = None


def get_analyst() -> DataAnalyst:
    global _analyst
    if _analyst is None:
        _analyst = DataAnalyst(
            [preprocessing_agent, statistical_analytics_agent, Data_Viz]
        )
    return _analyst


def configure_openai() -> None:
    import dspy
    import openai

    from config import OPENAI_API_KEY

    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not set. Add it to your environment to run analyses."
        )
    openai.api_key = OPENAI_API_KEY
    lm = dspy.OpenAI(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY)
    dspy.settings.configure(lm=lm)


def serialize_prediction(prediction: Any) -> dict[str, Any]:
    if hasattr(prediction, "toDict"):
        return prediction.toDict()
    if hasattr(prediction, "__dict__"):
        return {
            key: value
            for key, value in prediction.__dict__.items()
            if not key.startswith("_")
        }
    return {"value": str(prediction)}


def run_analysis(dataset_path: str, query: str) -> dict[str, Any]:
    configure_openai()
    dataset = pd.read_csv(dataset_path)
    analyst = get_analyst()
    output, agent_outputs = analyst.forward(dataset, query)

    serialized_outputs = {
        name: serialize_prediction(result) for name, result in agent_outputs.items()
    }

    plan = None
    plan_desc = None
    planner_output = serialized_outputs.get("PlannerAgent") or serialized_outputs.get(
        "planner"
    )
    if isinstance(planner_output, dict):
        plan = planner_output.get("plan")
        plan_desc = planner_output.get("plan_desc")

    return {
        "output": output,
        "agent_outputs": serialized_outputs,
        "plan": plan,
        "plan_desc": plan_desc,
        "dataset_preview": {
            "rows": len(dataset),
            "columns": list(dataset.columns),
            "sample": json.loads(
                dataset.head(5).to_json(orient="records", date_format="iso")
            ),
        },
    }
