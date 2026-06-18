import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash

from config import DB_PATH, DATA_DIR


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_key TEXT NOT NULL,
                size_bytes INTEGER DEFAULT 0,
                row_count INTEGER DEFAULT 0,
                column_count INTEGER DEFAULT 0,
                columns_json TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                dataset_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                plan TEXT,
                plan_desc TEXT,
                output TEXT,
                agent_outputs_json TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (dataset_id) REFERENCES datasets (id)
            );
            """
        )


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_user(username: str, email: str, password: str) -> dict[str, Any]:
    password_hash = generate_password_hash(password)
    created_at = utc_now()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (username, email, password_hash, created_at),
        )
        user_id = cursor.lastrowid
    return get_user_by_id(user_id)


def get_user_by_username(username: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    return dict(row) if row else None


def get_user_by_email(email: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def verify_user(username: str, password: str) -> dict[str, Any] | None:
    user = get_user_by_username(username)
    if not user or not check_password_hash(user["password_hash"], password):
        return None
    return user


def create_dataset(
    user_id: int,
    filename: str,
    file_key: str,
    size_bytes: int,
    row_count: int,
    column_count: int,
    columns: list[str],
) -> dict[str, Any]:
    created_at = utc_now()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO datasets (
                user_id, filename, file_key, size_bytes, row_count,
                column_count, columns_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                filename,
                file_key,
                size_bytes,
                row_count,
                column_count,
                json.dumps(columns),
                created_at,
            ),
        )
        dataset_id = cursor.lastrowid
    return get_dataset_by_id(dataset_id)


def get_dataset_by_id(dataset_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM datasets WHERE id = ?", (dataset_id,)
        ).fetchone()
    if not row:
        return None
    data = dict(row)
    data["columns"] = json.loads(data.pop("columns_json") or "[]")
    return data


def list_datasets_for_user(user_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM datasets WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()
    datasets = []
    for row in rows:
        data = dict(row)
        data["columns"] = json.loads(data.pop("columns_json") or "[]")
        datasets.append(data)
    return datasets


def create_analysis(user_id: int, dataset_id: int, query: str) -> dict[str, Any]:
    created_at = utc_now()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO analyses (user_id, dataset_id, query, status, created_at)
            VALUES (?, ?, ?, 'processing', ?)
            """,
            (user_id, dataset_id, query, created_at),
        )
        analysis_id = cursor.lastrowid
    return get_analysis_by_id(analysis_id)


def update_analysis(
    analysis_id: int,
    *,
    status: str,
    plan: str | None = None,
    plan_desc: str | None = None,
    output: str | None = None,
    agent_outputs: dict | None = None,
    error_message: str | None = None,
) -> dict[str, Any] | None:
    completed_at = utc_now() if status in {"completed", "failed"} else None
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE analyses
            SET status = ?, plan = ?, plan_desc = ?, output = ?,
                agent_outputs_json = ?, error_message = ?, completed_at = ?
            WHERE id = ?
            """,
            (
                status,
                plan,
                plan_desc,
                output,
                json.dumps(agent_outputs) if agent_outputs is not None else None,
                error_message,
                completed_at,
                analysis_id,
            ),
        )
    return get_analysis_by_id(analysis_id)


def get_analysis_by_id(analysis_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT a.*, d.filename, d.file_key, d.row_count, d.column_count
            FROM analyses a
            JOIN datasets d ON d.id = a.dataset_id
            WHERE a.id = ?
            """,
            (analysis_id,),
        ).fetchone()
    if not row:
        return None
    data = dict(row)
    data["agent_outputs"] = json.loads(data.pop("agent_outputs_json") or "{}")
    return data


def list_analyses_for_user(user_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT a.*, d.filename, d.file_key, d.row_count, d.column_count
            FROM analyses a
            JOIN datasets d ON d.id = a.dataset_id
            WHERE a.user_id = ?
            ORDER BY a.created_at DESC
            """,
            (user_id,),
        ).fetchall()
    analyses = []
    for row in rows:
        data = dict(row)
        data["agent_outputs"] = json.loads(data.pop("agent_outputs_json") or "{}")
        analyses.append(data)
    return analyses


def get_user_stats(user_id: int) -> dict[str, int]:
    with get_connection() as conn:
        dataset_count = conn.execute(
            "SELECT COUNT(*) FROM datasets WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
        analysis_count = conn.execute(
            "SELECT COUNT(*) FROM analyses WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
        completed_count = conn.execute(
            """
            SELECT COUNT(*) FROM analyses
            WHERE user_id = ? AND status = 'completed'
            """,
            (user_id,),
        ).fetchone()[0]
    return {
        "datasets": dataset_count,
        "analyses": analysis_count,
        "completed_analyses": completed_count,
    }
