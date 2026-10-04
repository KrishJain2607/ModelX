from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from app.config.settings import settings


def _db_path() -> Path:
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(_db_path(), timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS paper_trades (
                trade_id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS approvals (
                approval_id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS app_state (
                state_key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_paper_trades() -> dict[str, dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute("SELECT trade_id, data FROM paper_trades").fetchall()
    return {row["trade_id"]: json.loads(row["data"]) for row in rows}


def save_paper_trade(trade: dict[str, Any]) -> None:
    trade_id = str(trade["trade_id"])
    timestamp = _now()
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO paper_trades(trade_id, data, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(trade_id) DO UPDATE SET
                data=excluded.data,
                updated_at=excluded.updated_at
            """,
            (trade_id, json.dumps(trade, separators=(",", ":")), timestamp, timestamp),
        )


def load_approvals() -> dict[str, dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute("SELECT approval_id, data FROM approvals").fetchall()
    return {row["approval_id"]: json.loads(row["data"]) for row in rows}


def save_approval(record: dict[str, Any]) -> None:
    approval_id = str(record["approval_id"])
    timestamp = _now()
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO approvals(approval_id, data, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(approval_id) DO UPDATE SET
                data=excluded.data,
                updated_at=excluded.updated_at
            """,
            (approval_id, json.dumps(record, separators=(",", ":")), timestamp, timestamp),
        )


def load_state(state_key: str) -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute(
            "SELECT data FROM app_state WHERE state_key = ?",
            (state_key,),
        ).fetchone()
    return json.loads(row["data"]) if row else None


def save_state(state_key: str, state: dict[str, Any]) -> None:
    timestamp = _now()
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO app_state(state_key, data, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(state_key) DO UPDATE SET
                data=excluded.data,
                updated_at=excluded.updated_at
            """,
            (state_key, json.dumps(state, separators=(",", ":")), timestamp),
        )


def database_status() -> dict[str, Any]:
    path = _db_path()
    with connection() as conn:
        paper_count = conn.execute("SELECT COUNT(*) FROM paper_trades").fetchone()[0]
        approval_count = conn.execute("SELECT COUNT(*) FROM approvals").fetchone()[0]
        state_count = conn.execute("SELECT COUNT(*) FROM app_state").fetchone()[0]
    return {
        "enabled": True,
        "path": str(path),
        "paper_trades": paper_count,
        "approvals": approval_count,
        "state_records": state_count,
    }


# Initialize the schema before routers import persisted state.
init_db()
