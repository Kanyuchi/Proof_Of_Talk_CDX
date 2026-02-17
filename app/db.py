from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "matchmaking.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS intro_actions (
                from_id TEXT NOT NULL,
                to_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                notes TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL,
                PRIMARY KEY (from_id, to_id)
            )
            """
        )
        conn.commit()


def upsert_action(from_id: str, to_id: str, status: str, notes: str, updated_at: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO intro_actions (from_id, to_id, status, notes, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(from_id, to_id) DO UPDATE SET
                status=excluded.status,
                notes=excluded.notes,
                updated_at=excluded.updated_at
            """,
            (from_id, to_id, status, notes, updated_at),
        )
        conn.commit()


def get_all_actions() -> List[Dict[str, str]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT from_id, to_id, status, notes, updated_at
            FROM intro_actions
            ORDER BY updated_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def action_map() -> Dict[str, Dict[str, str]]:
    mapping: Dict[str, Dict[str, str]] = {}
    for row in get_all_actions():
        key = f"{row['from_id']}::{row['to_id']}"
        mapping[key] = row
    return mapping
