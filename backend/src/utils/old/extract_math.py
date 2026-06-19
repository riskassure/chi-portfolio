import os
import sqlite3
import sys

# Add src to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import DB_PATH

# 1. Update this to your local path
PLANETMATH_REPO_PATH = r"C:\path\to\your\cloned\planetmath" 

def extract_to_staging():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Create staging table
    cursor.execute("DROP TABLE IF EXISTS stg_math_import;")
    cursor.execute("""
        CREATE TABLE stg_math_import (
            file_name TEXT,
            raw_content TEXT
        );
    """)

    print(f"🔍 Crawling {PLANETMATH_REPO_PATH}...")
    
    count = 0
    for root, dirs, files in os.walk(PLANETMATH_REPO_PATH):
        for file in files:
            if file.endswith(".tex"):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Only keep files authored by you
                if "\\pmauthor{CWoo}{3771}" in content:
                    cursor.execute("INSERT INTO stg_math_import (file_name, raw_content) VALUES (?, ?)", 
                                   (file, content))
                    count += 1
    
    conn.commit()
    conn.close()
    print(f"✅ Extraction complete. {count} files staged in database.")

if __name__ == "__main__":
    extract_to_staging()