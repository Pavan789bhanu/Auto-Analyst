"""Unit tests for the analysis engine helpers and the DB migration.

The heavy `dspy` dependency is replaced with a lightweight stub so these tests
run anywhere, while still exercising the real bug-prone logic: prediction
serialization, dataset summarization, planner-output propagation, and the
is_admin migration.
"""
from __future__ import annotations

import importlib
import pathlib
import sqlite3
import sys
import types

import pytest

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
# Backend must come first so `import app` resolves to backend/app.py (the root
# also has an app.py). Root is appended only so data_analyst_system is found.
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))


class FakePrediction:
    """Mimics a dspy.Prediction: attribute access + items() over a _store."""

    def __init__(self, **fields):
        self._store = dict(fields)
        for key, value in fields.items():
            setattr(self, key, value)

    def items(self):
        return self._store.items()


def _make_dspy_stub():
    dspy = types.ModuleType("dspy")
    dspy.InputField = lambda *a, **k: None
    dspy.OutputField = lambda *a, **k: None
    dspy.Signature = type("Signature", (), {})
    dspy.Module = type("Module", (), {})
    dspy.LM = lambda **k: object()
    dspy.configure = lambda **k: None

    def chain_of_thought(signature):
        name = getattr(signature, "__name__", "")

        def run(**kwargs):
            if name == "PlannerAgent":
                return FakePrediction(
                    plan="preprocessing_agent", plan_desc="clean then analyze"
                )
            if name == "code_combiner_agent":
                return FakePrediction(code="# FINAL\nprint('done')")
            return FakePrediction(code=f"# {name} code", commentary=f"did {name}")

        return run

    dspy.ChainOfThought = chain_of_thought
    return dspy


@pytest.fixture
def engine(monkeypatch):
    monkeypatch.setitem(sys.modules, "dspy", _make_dspy_stub())
    monkeypatch.setitem(sys.modules, "openai", types.ModuleType("openai"))

    import data_analyst_system

    importlib.reload(data_analyst_system)
    import analyst_service

    importlib.reload(analyst_service)
    return data_analyst_system, analyst_service


# --------------------------------------------------------------------------- #
# Serialization (was returning {} for real dspy predictions)
# --------------------------------------------------------------------------- #
def test_to_jsonable(engine):
    _, analyst_service = engine
    assert analyst_service._to_jsonable("x") == "x"
    assert analyst_service._to_jsonable(5) == 5
    assert analyst_service._to_jsonable(None) is None
    assert analyst_service._to_jsonable({"a": 1}) == "{'a': 1}"


def test_serialize_prediction_reads_store(engine):
    _, analyst_service = engine
    pred = FakePrediction(code="print(1)", commentary="hi")
    out = analyst_service.serialize_prediction(pred)
    assert out == {"code": "print(1)", "commentary": "hi"}


def test_serialize_prediction_handles_plain_object(engine):
    _, analyst_service = engine

    class Bare:
        pass

    obj = Bare()
    obj.code = "x"
    out = analyst_service.serialize_prediction(obj)
    assert out.get("code") == "x"


# --------------------------------------------------------------------------- #
# Dataset summary (replaced the token-blowing df.to_string())
# --------------------------------------------------------------------------- #
def test_summarize_dataset(engine):
    data_analyst_system, _ = engine
    import pandas as pd

    df = pd.DataFrame({"month": ["jan", "feb"], "revenue": [100, 200]})
    summary = data_analyst_system.summarize_dataset(df)
    assert "2 rows x 2 columns" in summary
    assert "month" in summary and "revenue" in summary


# --------------------------------------------------------------------------- #
# Planner output is now propagated (was silently lost)
# --------------------------------------------------------------------------- #
def test_forward_includes_planner_and_runs_agents(engine):
    data_analyst_system, _ = engine
    import pandas as pd

    analyst = data_analyst_system.DataAnalyst(
        [
            data_analyst_system.preprocessing_agent,
            data_analyst_system.statistical_analytics_agent,
            data_analyst_system.Data_Viz,
        ]
    )
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    output, agent_outputs = analyst.forward(df, "analyze it")

    assert output.startswith("# FINAL")
    assert "PlannerAgent" in agent_outputs
    assert "preprocessing_agent" in agent_outputs
    assert agent_outputs["PlannerAgent"].plan == "preprocessing_agent"


# --------------------------------------------------------------------------- #
# is_admin migration for databases created by older builds
# --------------------------------------------------------------------------- #
def test_is_admin_migration(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy.db"

    # Legacy schema: no is_admin column, with a pre-existing user.
    con = sqlite3.connect(db_path)
    con.executescript(
        """
        CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE, email TEXT UNIQUE,
            password_hash TEXT, created_at TEXT);
        """
    )
    con.commit()
    con.close()

    monkeypatch.setenv("PRYSM_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DATABASE_PATH", str(db_path))

    import config
    import models

    importlib.reload(config)
    importlib.reload(models)

    # Seed a legacy user with the (now) standard hashing, then migrate.
    with models.get_connection() as conn:
        conn.execute(
            "INSERT INTO users (username, email, password_hash, created_at) VALUES (?,?,?,?)",
            ("old", "old@e.com", models.hash_password("password123"), "2026-01-01"),
        )

    models.init_db()  # runs the migration

    cols = {row[1] for row in sqlite3.connect(db_path).execute("PRAGMA table_info(users)")}
    assert "is_admin" in cols
    assert models.verify_user("old", "password123") is not None
