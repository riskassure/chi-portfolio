# backend/src/utils/math/math_classification_lookup.py

import sys
import re
import sqlite3
from pathlib import Path

# Locate backend/src/ to find config.py cleanly
SRC_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(SRC_DIR))
from config import DB_PATH, SOURCE_CSV_PATH

def migrate_and_populate_classifications():
    print("🎬 Starting Local MSC High-Fidelity Schema Migration...")
    
    if not SOURCE_CSV_PATH.exists():
        print(f"❌ Error: Cannot find master source file at:\n   {SOURCE_CSV_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🛠️ Dropping old structure and building high-fidelity table framework...")
    cursor.execute("DROP TABLE IF EXISTS math_classifications;")
    cursor.execute("""
    CREATE TABLE math_classifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        text TEXT NOT NULL,
        description TEXT
    );""")
    conn.commit()

    print("📖 Reading and tokenizing master source rows...")
    line_pattern = re.compile(r'^(\S+)\s+"([^"]*)"\s+"([^"]*)"')
    insert_payload = []
    seen_codes = set()

    with SOURCE_CSV_PATH.open(mode='r', encoding='latin-1') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("code"): 
                continue
                
            match = line_pattern.match(line)
            if match:
                # 🛠️ CORRECTIVE MEASURE: Clean out any literal quotes slipping past tokenization
                code = match.group(1).strip().replace('"', '').upper()
                text_col = match.group(2).strip().replace('"', '')
                desc_col = match.group(3).strip().replace('"', '')
                
                if code not in seen_codes:
                    insert_payload.append((code, text_col, desc_col))
                    seen_codes.add(code)
            else:
                short_pattern = re.match(r'^(\S+)\s+"([^"]*)"', line)
                if short_pattern:
                    # 🛠️ CORRECTIVE MEASURE: Clean out any literal quotes here as well
                    code = short_pattern.group(1).strip().replace('"', '').upper()
                    text_col = short_pattern.group(2).strip().replace('"', '')
                    if code not in seen_codes:
                        insert_payload.append((code, text_col, ""))
                        seen_codes.add(code)

    print(f"⚡ Streaming {len(insert_payload)} processed definitions directly into SQLite...")
    cursor.executemany("""
        INSERT INTO math_classifications (code, text, description)
        VALUES (?, ?, ?);
    """, insert_payload)
    
    conn.commit()
    conn.close()
    print(f"🎉 Success! Your master lookup table is fully loaded.")


if __name__ == "__main__":
    migrate_and_populate_classifications()