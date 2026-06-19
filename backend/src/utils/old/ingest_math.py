import sys
import os
import sqlite3
import re

# Add the 'src' directory to the system path so we can import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import DB_PATH  # 📥 Import your centralized DB_PATH

# Update this path to where your local Git clone of the PlanetMath files is
PLANETMATH_REPO_PATH = r"C:\path\to\your\cloned\planetmath" 

def ingest():
    conn = sqlite3.connect(str(DB_PATH)) # Uses your central config path
    cursor = conn.cursor()
    
    # Ensure our new math structure is ready
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS math_concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pm_canonical_name TEXT UNIQUE,
            title TEXT,
            msc_code TEXT,
            raw_latex TEXT
        )
    """)

    # Walk the directory structure
    for root, dirs, files in os.walk(PLANETMATH_REPO_PATH):
        for file in files:
            if file.endswith(".tex"):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for your author identity
                if "\\pmauthor{CWoo}{3771}" in content:
                    print(f"Ingesting: {file}")
                    
                    # Extraction
                    canonical = re.search(r'\\pmcanonicalname\{(.*?)\}', content)
                    title = re.search(r'\\pmtitle\{(.*?)\}', content)
                    msc = re.search(r'\\pmclassification\{msc\}\{(.*?)\}', content)
                    
                    # Get body content
                    body = ""
                    if "\\begin{document}" in content:
                        body = content.split("\\begin{document}")[1].split("\\end{document}")[0].strip()

                    cursor.execute("""
                        INSERT OR REPLACE INTO math_concepts 
                        (pm_canonical_name, title, msc_code, raw_latex) 
                        VALUES (?, ?, ?, ?)
                    """, (
                        canonical.group(1) if canonical else file,
                        title.group(1) if title else "Untitled",
                        msc.group(1) if msc else None,
                        body
                    ))

    conn.commit()
    conn.close()
    print("✅ Ingestion successfully synced with portfolio.db!")

if __name__ == "__main__":
    ingest()