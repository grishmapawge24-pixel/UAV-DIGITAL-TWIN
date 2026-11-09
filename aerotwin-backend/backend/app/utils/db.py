"""
app/utils/db.py
=================
Very small SQLite helper. Not an ORM on purpose - this is a hackathon
backend and the only thing we actually persist is:

  - simulated "missions" created via POST /api/missions/simulate

Everything else (flight header, telemetry) is read live from the
NGAFID files / processed cache each request, so it doesn't need a table.

The database file lives at data/aerotwin.db (created automatically,
never shipped in the zip, safe to delete any time to reset the demo).
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


_initialized = False


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    global _initialized
    if not _initialized:
        # Defensive: normally init_db() runs once at FastAPI startup, but we
        # also lazily ensure the table exists here so this module works
        # correctly even if something calls it before the startup event runs
        # (e.g. tests, or a script that imports these helpers directly).
        init_db()
        _initialized = True
    conn = sqlite3.connect(str(settings.SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they don't exist yet. Safe to call on every startup.
    Connects directly (not via get_connection()) to avoid a circular call
    with the lazy-init check in get_connection()."""
    conn = sqlite3.connect(str(settings.SQLITE_PATH))
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS missions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                name TEXT,
                base_flight_id INTEGER,
                params_json TEXT,
                result_json TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
    logger.info("SQLite ready at %s", settings.SQLITE_PATH)


def save_mission(name: Optional[str], base_flight_id: Optional[int],
                  params: Dict[str, Any], result: Dict[str, Any]) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO missions (created_at, name, base_flight_id, params_json, result_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                name,
                base_flight_id,
                json.dumps(params),
                json.dumps(result),
            ),
        )
        return cur.lastrowid


def list_missions(limit: int = 50) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, created_at, name, base_flight_id, params_json, result_json "
            "FROM missions ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    missions = []
    for r in rows:
        missions.append(
            {
                "id": r["id"],
                "created_at": r["created_at"],
                "name": r["name"],
                "base_flight_id": r["base_flight_id"],
                "params": json.loads(r["params_json"]) if r["params_json"] else {},
                "result": json.loads(r["result_json"]) if r["result_json"] else {},
            }
        )
    return missions


def get_mission(mission_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        r = conn.execute(
            "SELECT id, created_at, name, base_flight_id, params_json, result_json "
            "FROM missions WHERE id = ?",
            (mission_id,),
        ).fetchone()
    if not r:
        return None
    return {
        "id": r["id"],
        "created_at": r["created_at"],
        "name": r["name"],
        "base_flight_id": r["base_flight_id"],
        "params": json.loads(r["params_json"]) if r["params_json"] else {},
        "result": json.loads(r["result_json"]) if r["result_json"] else {},
    }
