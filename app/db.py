from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SQLITE_PATH = ROOT / "data" / "matchmaking.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH}"


@dataclass
class DbConfig:
    kind: str
    url: str


def _database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL).strip()


def _parse_database_url(url: Optional[str] = None) -> DbConfig:
    raw = (url or _database_url()).strip()
    parsed = urlparse(raw)
    scheme = parsed.scheme.lower()

    if scheme in {"", "sqlite"}:
        return DbConfig(kind="sqlite", url=raw)
    if scheme in {"postgres", "postgresql"}:
        return DbConfig(kind="postgres", url=raw)
    if scheme in {"mysql", "mysql+pymysql"}:
        return DbConfig(kind="mysql", url=raw)

    raise ValueError(f"Unsupported DATABASE_URL scheme: {scheme}")


def backend_summary() -> Dict[str, str]:
    cfg = _parse_database_url()
    return {"backend": cfg.kind, "database_url": cfg.url}


def _sqlite_db_path(sqlite_url: str) -> str:
    if sqlite_url.startswith("sqlite:///"):
        path = sqlite_url.replace("sqlite:///", "", 1)
        return str(Path(path))
    if sqlite_url == "sqlite://":
        return str(DEFAULT_SQLITE_PATH)
    return str(DEFAULT_SQLITE_PATH)


def _connect_sqlite(cfg: DbConfig) -> sqlite3.Connection:
    db_path = _sqlite_db_path(cfg.url)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _connect_postgres(cfg: DbConfig):
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PostgreSQL selected but dependency missing. Install psycopg[binary] to use postgres DATABASE_URL."
        ) from exc
    return psycopg.connect(cfg.url, autocommit=True)


def _connect_mysql(cfg: DbConfig):
    try:
        import pymysql
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "MySQL selected but dependency missing. Install pymysql to use mysql DATABASE_URL."
        ) from exc

    parsed = urlparse(cfg.url)
    params = parse_qs(parsed.query)
    ssl_enabled = params.get("ssl", ["false"])[0].lower() in {"1", "true", "yes"}

    connect_kwargs: Dict[str, Any] = {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": parsed.path.lstrip("/"),
        "autocommit": True,
        "cursorclass": pymysql.cursors.DictCursor,
    }
    if ssl_enabled:
        connect_kwargs["ssl"] = {"ssl": True}

    return pymysql.connect(**connect_kwargs)


def _connect():
    cfg = _parse_database_url()
    if cfg.kind == "sqlite":
        return cfg.kind, _connect_sqlite(cfg)
    if cfg.kind == "postgres":
        return cfg.kind, _connect_postgres(cfg)
    if cfg.kind == "mysql":
        return cfg.kind, _connect_mysql(cfg)
    raise ValueError(f"Unsupported database backend: {cfg.kind}")


def _init_sqlite(conn) -> None:
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


def _init_postgres(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
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


def _init_mysql(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS intro_actions (
                from_id VARCHAR(255) NOT NULL,
                to_id VARCHAR(255) NOT NULL,
                status VARCHAR(32) NOT NULL DEFAULT 'pending',
                notes TEXT NOT NULL,
                updated_at VARCHAR(64) NOT NULL,
                PRIMARY KEY (from_id, to_id)
            )
            """
        )


def init_db() -> None:
    kind, conn = _connect()
    try:
        if kind == "sqlite":
            _init_sqlite(conn)
        elif kind == "postgres":
            _init_postgres(conn)
        elif kind == "mysql":
            _init_mysql(conn)
    finally:
        conn.close()


def upsert_action(from_id: str, to_id: str, status: str, notes: str, updated_at: str) -> None:
    kind, conn = _connect()
    try:
        if kind == "sqlite":
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
            return

        if kind == "postgres":
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO intro_actions (from_id, to_id, status, notes, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (from_id, to_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        notes = EXCLUDED.notes,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (from_id, to_id, status, notes, updated_at),
                )
            return

        if kind == "mysql":
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO intro_actions (from_id, to_id, status, notes, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        status = VALUES(status),
                        notes = VALUES(notes),
                        updated_at = VALUES(updated_at)
                    """,
                    (from_id, to_id, status, notes, updated_at),
                )
            return
    finally:
        conn.close()


def get_all_actions() -> List[Dict[str, str]]:
    kind, conn = _connect()
    try:
        if kind == "sqlite":
            rows = conn.execute(
                """
                SELECT from_id, to_id, status, notes, updated_at
                FROM intro_actions
                ORDER BY updated_at DESC
                """
            ).fetchall()
            return [dict(row) for row in rows]

        if kind == "postgres":
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT from_id, to_id, status, notes, updated_at
                    FROM intro_actions
                    ORDER BY updated_at DESC
                    """
                )
                rows = cur.fetchall()
                cols = [d.name for d in cur.description]
            return [dict(zip(cols, row)) for row in rows]

        if kind == "mysql":
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT from_id, to_id, status, notes, updated_at
                    FROM intro_actions
                    ORDER BY updated_at DESC
                    """
                )
                rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()

    return []


def action_map() -> Dict[str, Dict[str, str]]:
    mapping: Dict[str, Dict[str, str]] = {}
    for row in get_all_actions():
        key = f"{row['from_id']}::{row['to_id']}"
        mapping[key] = row
    return mapping
