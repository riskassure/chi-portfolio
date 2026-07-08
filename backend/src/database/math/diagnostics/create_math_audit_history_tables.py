# backend/src/database/math/diagnostics/create_math_audit_history_tables.py

import sys
import sqlite3
from pathlib import Path


THIS_FILE = Path(__file__).resolve()

# Expected location:
# backend/src/database/math/diagnostics/create_math_audit_history_tables.py
SRC_DIR = THIS_FILE.parents[3]      # backend/src
BACKEND_DIR = THIS_FILE.parents[4]  # backend

for path in (SRC_DIR, BACKEND_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from config import DB_PATH


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS math_audit_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            audit_version TEXT NOT NULL,
            mode TEXT NOT NULL,
            total_scanned INTEGER NOT NULL DEFAULT 0,
            total_problematic INTEGER NOT NULL DEFAULT 0,
            total_errors INTEGER NOT NULL DEFAULT 0
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS math_concept_audit_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            concept_id INTEGER NOT NULL,
            rendered_tex_hash TEXT NOT NULL,
            status TEXT NOT NULL,
            issue_count INTEGER NOT NULL DEFAULT 0,
            issue_summary TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(run_id)
                REFERENCES math_audit_runs(id)
                ON DELETE CASCADE,
            FOREIGN KEY(concept_id)
                REFERENCES math_concepts(id)
                ON DELETE CASCADE,
            UNIQUE(run_id, concept_id)
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_math_concept_audit_results_run_id
        ON math_concept_audit_results(run_id);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_math_concept_audit_results_concept_status
        ON math_concept_audit_results(concept_id, status);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_math_audit_runs_completed_at
        ON math_audit_runs(completed_at);
    """)

    conn.commit()
    conn.close()

    print("Created/verified math audit history tables.")
    print(f"Database: {DB_PATH}")


if __name__ == "__main__":
    main()