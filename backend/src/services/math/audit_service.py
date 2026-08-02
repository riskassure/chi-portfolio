# backend/src/services/math/audit_service.py

import sqlite3
from datetime import datetime


def get_now_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def normalize_audit_mode(value) -> str:
    mode = (value or "all").strip().lower()

    if mode not in {"all", "problematic"}:
        return "all"

    return mode


def get_latest_completed_audit_run_id(cursor):
    cursor.execute("""
        SELECT id
        FROM math_audit_runs
        WHERE completed_at IS NOT NULL
        ORDER BY completed_at DESC, id DESC
        LIMIT 1;
    """)

    row = cursor.fetchone()

    if not row:
        return None

    return row["id"] if isinstance(row, sqlite3.Row) else row[0]