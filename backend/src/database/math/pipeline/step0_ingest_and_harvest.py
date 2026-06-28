# backend/src/utils/math/step0_ingest_and_harvest.py

import sys
import re
import sqlite3
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[3]  # backend/src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DB_PATH, PLANETMATH_CACHE_DIR
from database.math.pipeline.math_data_manager import run_github_sync

TARGET_DIR = PLANETMATH_CACHE_DIR

# Handle folder crawler imports dynamically out of the current directory
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.append(str(CURRENT_DIR))
from math_data_manager import run_github_sync


def check_and_populate_local_directory():
    is_populated = False

    if TARGET_DIR.exists() and any(TARGET_DIR.rglob("*.tex")):
        is_populated = True

    if not is_populated:
        print("🔍 Local PlanetMath directory is missing or empty!")
        print("🚀 Invoking math_data_manager to clone universe from GitHub...")
        run_github_sync()
    else:
        print("🧠 Local cache detected. Skipping GitHub crawl!")


def run_ingest_and_harvest():
    check_and_populate_local_directory()

    print("\n[STEP 0] Scanning local files to stage personal portfolio content...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Staging table now has a stable row id for the current pipeline run.
    # math_concepts.source_staging_id will point back here.
    cursor.execute("DROP TABLE IF EXISTS stg_math_import;")
    cursor.execute("""
        CREATE TABLE stg_math_import (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            raw_content TEXT NOT NULL
        );
    """)

    # Rebuild document type lookup from all scanned PlanetMath files.
    cursor.execute("DROP TABLE IF EXISTS math_types;")
    cursor.execute("""
        CREATE TABLE math_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_name TEXT UNIQUE NOT NULL
        );
    """)

    global_types = set()
    my_staging_count = 0
    total_files_scanned = 0

    if TARGET_DIR.exists():
        # Sorting makes staging id assignment deterministic for a given file set.
        for file_path in sorted(TARGET_DIR.rglob("*.tex")):
            total_files_scanned += 1

            try:
                content = file_path.read_text(encoding="utf-8")

                type_match = re.search(r"\\pmtype\{([^}]+)\}", content)
                if type_match:
                    global_types.add(type_match.group(1).strip().capitalize())

                if "\\pmauthor{CWoo}" in content or "\\pmowner{CWoo}" in content:
                    cursor.execute("""
                        INSERT INTO stg_math_import (file_name, raw_content)
                        VALUES (?, ?);
                    """, (file_path.name, content))

                    my_staging_count += 1

            except Exception as e:
                print(f"⚠️ Skipping unreadable file: {file_path} ({e})")
                continue

    print(f"Scanned {total_files_scanned} total files across local directory.")
    print(f"Seeding {len(global_types)} unique global structural Document Types...")

    for t_name in sorted(global_types):
        cursor.execute(
            "INSERT OR IGNORE INTO math_types (type_name) VALUES (?);",
            (t_name,)
        )

    conn.commit()
    conn.close()

    print(f"✅ [STEP 0] Complete: Staged {my_staging_count} personal files.")


if __name__ == "__main__":
    run_ingest_and_harvest()