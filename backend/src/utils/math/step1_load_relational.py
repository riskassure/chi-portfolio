# backend/src/utils/math/step1_load_relational.py

import sys
import re
import sqlite3
from pathlib import Path
from datetime import datetime

SRC_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(SRC_DIR))
from config import DB_PATH

def generate_slug(canonical_name):
    if not canonical_name: return None
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', canonical_name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1)
    return s2.lower().replace('_', '-').replace('--', '-')

def normalize_to_iso_datetime(date_string):
    """
    Normalizes mixed legacy date configurations from PlanetMath macro blocks
    into a uniform 'YYYY-MM-DD HH:MM:SS' string format.
    """
    if not date_string:
        return None
        
    # Strip literal double/single quotes, commas, or outer spaces
    cleaned = date_string.strip().strip('"').strip("'").strip()
    
    # Try parsing: YYYY-MM-DD HH:MM:SS
    try:
        dt = datetime.strptime(cleaned, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    # Try parsing shorter style: YYYY-MM-DD
    try:
        dt = datetime.strptime(cleaned, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d 00:00:00")
    except ValueError:
        pass

    # Fallback to python-dateutil smart parsing if arbitrary text strings are hit
    try:
        from dateutil import parser
        dt = parser.parse(cleaned)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        # Final fallback: return current clock string if completely unparsable
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def transform_latex_content(raw_content):
    """Processes a raw LaTeX string and extracts its semantic layers."""
    metadata = {
        "canonical_name": None, "slug": None, "title": None, "created": None,
        "modified": None, "owner": None, "types": [], "defines": [], 
        "synonyms": [], "classifications": [], "escaped_words": []
    }
    try:
        header_match = re.search(r'\\documentclass.*\\endmetadata', raw_content, re.DOTALL)
        if not header_match: return None
        header_block = header_match.group(0)
        
        canon_match = re.search(r'\\pmcanonicalname\{([^}]+)\}', header_block)
        title_match = re.search(r'\\pmtitle\{([^}]+)\}', header_block)
        owner_match = re.search(r'\\pmowner\{([^}]+)\}', header_block) or re.search(r'\\pmauthor\{([^}]+)\}', header_block)
        created_match = re.search(r'\\pmcreated\{([^}]+)\}', header_block)
        
        # 🌟 NEW ELEMENT EXTRACTION: Capture the updated modification macro
        modified_match = re.search(r'\\pmmodified\{([^}]+)\}', header_block)
        
        if canon_match: metadata["canonical_name"] = canon_match.group(1).strip()
        if title_match: metadata["title"] = title_match.group(1).strip()
        if owner_match: metadata["owner"] = owner_match.group(1).strip()
        
        # Normalize timelines into strict ISO layout formats right during extraction
        if created_match: 
            metadata["created"] = normalize_to_iso_datetime(created_match.group(1))
            
        if modified_match:
            metadata["modified"] = normalize_to_iso_datetime(modified_match.group(1))
        else:
            # Fallback policy: if no explicit modification tag is found, synchronize with creation
            metadata["modified"] = metadata["created"]
            
        metadata["slug"] = generate_slug(metadata["canonical_name"])
        
        # 1. Multi-Type Extract: Find all \pmtype{...} entries (e.g., Theorem, Proof)
        for t in re.findall(r'\\pmtype\{([^}]+)\}', header_block):
            metadata["types"].append(t.strip().capitalize())
            
        # 2. Multi-Classification Extract: Handle exact \pmclassification{msc}{CODE} syntax
        for cl_type, cl_code in re.findall(r'\\pmclassification\{([^}]+)\}\s*\{([^}]+)\}', header_block):
            # 🌟 CLEAN FIX: Strip literal quote quotes out of classification keys
            clean_code = cl_code.strip().replace('"', '').replace("'", "").upper()
            if clean_code:
                metadata["classifications"].append(clean_code)

        # Fallback Check: Handle alternative legacy \pmclass block variants if present
        for cl_block in re.findall(r'\\pmclass\{([^}]+)\}', header_block):
            for raw_code in cl_block.split(','):
                # 🌟 CLEAN FIX: Strip literal quote codes out here too
                stripped_code = raw_code.strip().replace('"', '').replace("'", "")
                clean_code = re.sub(r'^(msc|msc2000|msc2010):', '', stripped_code, flags=re.IGNORECASE)
                if clean_code:
                    metadata["classifications"].append(clean_code.upper())

        # Collect side arrays
        for d in re.findall(r'\\pmdefines\{([^}]+)\}', header_block):
            metadata["defines"].append(d.strip())
        for s in re.findall(r'\\pmsynonym\{([^}]+)\}', header_block):
            metadata["synonyms"].append(s.strip())
        for esc in re.findall(r'\\pmnolink\{([^}]+)\}', header_block):
            metadata["escaped_words"].append(esc.strip())
            
        content_match = re.search(r'\\begin\{document\}(.*)\\end\{document\}', raw_content, re.DOTALL)
        metadata["cleaned_tex"] = content_match.group(1).strip() if content_match else ""
        
        return metadata
    except Exception as e:
        print(f"⚠️ Parsing optimization failure: {e}")
        return None

def build_relational_tables():
    print("[STEP 1] Rebuilding application tables and running relational transformations...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Drop and recreate relational tables cleanly (Leaving math_types untouched!)
    cursor.execute("DROP TABLE IF EXISTS math_concept_classifications;")
    cursor.execute("DROP TABLE IF EXISTS math_concept_types;")
    cursor.execute("DROP TABLE IF EXISTS math_synonyms;")
    cursor.execute("DROP TABLE IF EXISTS math_definitions;")
    cursor.execute("DROP TABLE IF EXISTS math_link_exclusions;")
    cursor.execute("DROP TABLE IF EXISTS math_concepts;")
    
    # 1. Primary Concept Table (Upgraded for Phase 2 tracking)
    cursor.execute("""
        CREATE TABLE math_concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_name TEXT NOT NULL UNIQUE,
            slug TEXT NOT NULL,                  -- 🌟 Removed UNIQUE constraint for Phase 2 flexibility
            title TEXT NOT NULL,
            created_at TEXT,                     -- Strict deterministic ISO string format
            updated_at TEXT,                     -- 🌟 New modification log column added
            owner TEXT,
            cleaned_tex TEXT
        );
    """)
    
    # 2. Many-to-Many Bridge Table: Concepts to Multiple Document Types
    cursor.execute("""
        CREATE TABLE math_concept_types (
            concept_id INTEGER,
            type_id INTEGER,
            PRIMARY KEY (concept_id, type_id),
            FOREIGN KEY (concept_id) REFERENCES math_concepts(id) ON DELETE CASCADE,
            FOREIGN KEY (type_id) REFERENCES math_types(id) ON DELETE CASCADE
        );
    """)
    
    # 3. Many-to-Many Bridge Table: Concepts to Classifications
    cursor.execute("""
        CREATE TABLE math_concept_classifications (
            concept_id INTEGER,
            classification_id INTEGER,
            PRIMARY KEY (concept_id, classification_id),
            FOREIGN KEY (concept_id) REFERENCES math_concepts(id) ON DELETE CASCADE,
            FOREIGN KEY (classification_id) REFERENCES math_classifications(id) ON DELETE CASCADE
        );
    """)
    
    # Meta Tables
    cursor.execute("CREATE TABLE math_synonyms (id INTEGER PRIMARY KEY, concept_id INTEGER, synonym_text TEXT, FOREIGN KEY(concept_id) REFERENCES math_concepts(id) ON DELETE CASCADE);")
    cursor.execute("CREATE TABLE math_definitions (id INTEGER PRIMARY KEY, concept_id INTEGER, defined_term TEXT, FOREIGN KEY(concept_id) REFERENCES math_concepts(id) ON DELETE CASCADE);")
    cursor.execute("CREATE TABLE math_link_exclusions (id INTEGER PRIMARY KEY, concept_id INTEGER, word TEXT, FOREIGN KEY(concept_id) REFERENCES math_concepts(id) ON DELETE CASCADE);")
    
    # Process staging items
    cursor.execute("SELECT file_name, raw_content FROM stg_math_import;")
    staged_rows = cursor.fetchall()
    processed_count = 0
    
    for file_name, raw_content in staged_rows:
        item = transform_latex_content(raw_content)
        if not item or not item["canonical_name"]: 
            continue
            
        # 🌟 UPDATED SEED INGESTION: Passes both 'created' and 'modified' ISO values safely
        cursor.execute("""
            INSERT INTO math_concepts (canonical_name, slug, title, created_at, updated_at, owner, cleaned_tex)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (item["canonical_name"], item["slug"], item["title"], item["created"], item["modified"], item["owner"], item["cleaned_tex"]))
        concept_id = cursor.lastrowid
        
        # Populate Meta Tables
        for syn in item["synonyms"]:
            cursor.execute("INSERT INTO math_synonyms (concept_id, synonym_text) VALUES (?, ?)", (concept_id, syn))
        for d_term in item["defines"]:
            cursor.execute("INSERT INTO math_definitions (concept_id, defined_term) VALUES (?, ?)", (concept_id, d_term))
        for word in item["escaped_words"]:
            cursor.execute("INSERT INTO math_link_exclusions (concept_id, word) VALUES (?, ?)", (concept_id, word))
            
        # Map Multiple Document Types via Bridge Table using Step 0's on-the-fly master table
        for t_name in item["types"]:
            cursor.execute("SELECT id FROM math_types WHERE type_name = ?", (t_name,))
            t_row = cursor.fetchone()
            if t_row:
                cursor.execute("INSERT OR IGNORE INTO math_concept_types (concept_id, type_id) VALUES (?, ?)", (concept_id, t_row[0]))
                
        # Map Classifications directly using clean flat code lookup
        for clean_code in item["classifications"]:
            # Action Plan 1: Attempt exact string hit matching
            cursor.execute("SELECT id FROM math_classifications WHERE code = ?", (clean_code,))
            row = cursor.fetchone()
            
            # Action Plan 2: Fallback handling to clear punctuation artifacts if needed
            if not row:
                fallback_code = re.sub(r'[^A-Z0-9]', '', clean_code)
                cursor.execute("SELECT id FROM math_classifications WHERE code = ?", (fallback_code,))
                row = cursor.fetchone()
                
            if row:
                cursor.execute("""
                    INSERT OR IGNORE INTO math_concept_classifications (concept_id, classification_id)
                    VALUES (?, ?)
                """, (concept_id, row[0]))
                
        processed_count += 1

    conn.commit()
    conn.close()
    print(f"✅ [STEP 1] Complete: Relational transformation completed for {processed_count} files.")

if __name__ == "__main__":
    build_relational_tables()