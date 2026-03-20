from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


DB_PATH = os.getenv("OXIA_DB_PATH", "oxia.sqlite3")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meals (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                user_id TEXT
            )
            """
        )

        # Evolve meals table if an older DB exists.
        meals_cols = [r["name"] for r in conn.execute("PRAGMA table_info(meals)").fetchall()]
        if "user_id" not in meals_cols:
            conn.execute("ALTER TABLE meals ADD COLUMN user_id TEXT;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_results (
                meal_id TEXT PRIMARY KEY,
                analysis_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (meal_id) REFERENCES meals(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_turns (
                id TEXT PRIMARY KEY,
                meal_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                focus_metric TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (meal_id) REFERENCES meals(id) ON DELETE CASCADE
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS nutritional_cache (
                cache_key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def store_analysis(meal_id: str, analysis: dict[str, Any], user_id: str | None = None) -> None:
    created_at = _utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meals (id, created_at, user_id) VALUES (?, ?, ?)",
            (meal_id, created_at, user_id),
        )
        conn.execute(
            """
            INSERT INTO analysis_results (meal_id, analysis_json, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(meal_id) DO UPDATE SET
                analysis_json=excluded.analysis_json,
                created_at=excluded.created_at
            """,
            (meal_id, json.dumps(analysis, ensure_ascii=False), created_at),
        )


def get_analysis(meal_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT analysis_json FROM analysis_results WHERE meal_id = ?", (meal_id,)).fetchone()
        if not row:
            return None
        return json.loads(row["analysis_json"])


def get_meal_user_id(meal_id: str) -> str | None:
    with get_conn() as conn:
        row = conn.execute("SELECT user_id FROM meals WHERE id = ?", (meal_id,)).fetchone()
        if not row:
            return None
        return row["user_id"]


def get_user_by_username(username: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if not row:
            return None
        return dict(row)


def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        return dict(row)


def delete_meal(meal_id: str, user_id: str | None = None) -> bool:
    """
    Delete a meal + its analysis + chat turns (cascades via FK).
    Returns False if the meal doesn't exist or doesn't belong to `user_id`.
    """
    with get_conn() as conn:
        row = conn.execute("SELECT user_id FROM meals WHERE id = ?", (meal_id,)).fetchone()
        if not row:
            return False
        if user_id and row["user_id"] != user_id:
            return False
        conn.execute("DELETE FROM meals WHERE id = ?", (meal_id,))
        return True


def store_user(*, user_id: str, username: str, password_hash: str) -> None:
    created_at = _utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (user_id, username, password_hash, created_at),
        )


def get_recent_analyses(limit: int = 10, user_id: str | None = None) -> list[dict[str, Any]]:
    with get_conn() as conn:
        if user_id:
            rows = conn.execute(
                """
                SELECT ar.analysis_json
                FROM analysis_results ar
                JOIN meals m ON m.id = ar.meal_id
                WHERE m.user_id = ?
                ORDER BY ar.created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT analysis_json
                FROM analysis_results
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [json.loads(r["analysis_json"]) for r in rows]


def store_chat_turn(
    turn_id: str,
    meal_id: str,
    question: str,
    answer: str,
    focus_metric: str | None,
) -> None:
    created_at = _utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO chat_turns (id, meal_id, question, answer, focus_metric, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (turn_id, meal_id, question, answer, focus_metric, created_at),
        )


def get_nutritional_cache(cache_key: str) -> Any | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT value_json FROM nutritional_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
        if not row:
            return None
        return json.loads(row["value_json"])


def set_nutritional_cache(cache_key: str, value: Any) -> None:
    created_at = _utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO nutritional_cache (cache_key, value_json, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                value_json=excluded.value_json,
                created_at=excluded.created_at
            """,
            (cache_key, json.dumps(value, ensure_ascii=False), created_at),
        )

