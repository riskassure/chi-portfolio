# backend/src/database/math/diagnostics/verify_psset_diagram_conversion.py

import re
import sys
import sqlite3
from pathlib import Path


THIS_FILE = Path(__file__).resolve()

# Expected location:
# backend/src/database/math/diagnostics/verify_psset_diagram_conversion.py
SRC_DIR = THIS_FILE.parents[3]      # backend/src
BACKEND_DIR = THIS_FILE.parents[4]  # backend

for path in (SRC_DIR, BACKEND_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from config import DB_PATH


IMMEDIATE_PSSET_RENDERED_RE = re.compile(
    r"\\psset\s*\{[^{}]*\}\s*\\begin\{pspicture\}",
    re.IGNORECASE,
)


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM math_concept_diagrams
        WHERE source_tex LIKE '%\\psset%';
    """)
    diagrams_with_psset = cursor.fetchone()[0]

    cursor.execute("""
        SELECT concept_id, block_index, source_hash, substr(source_tex, 1, 160)
        FROM math_concept_diagrams
        WHERE source_tex LIKE '%\\psset%'
        ORDER BY concept_id, block_index;
    """)
    source_examples = cursor.fetchall()

    cursor.execute("""
        SELECT id, slug, title, rendered_tex
        FROM math_concepts
        WHERE rendered_tex LIKE '%\\psset%';
    """)
    rendered_rows = cursor.fetchall()

    immediate_rendered_leftovers = []

    for concept_id, slug, title, rendered_tex in rendered_rows:
        text = rendered_tex or ""
        if IMMEDIATE_PSSET_RENDERED_RE.search(text):
            immediate_rendered_leftovers.append((concept_id, slug, title))

    conn.close()

    print("Verify PSTricks psset conversion")
    print("================================")
    print(f"Diagram rows whose source_tex includes \\psset: {diagrams_with_psset}")
    print(f"Concepts whose rendered_tex still contains \\psset: {len(rendered_rows)}")
    print(f"Immediate \\psset + pspicture leftovers in rendered_tex: {len(immediate_rendered_leftovers)}")
    print()

    print("Diagram source_tex examples with \\psset")
    print("---------------------------------------")
    for concept_id, block_index, source_hash, snippet in source_examples[:20]:
        print(f"{concept_id} block {block_index} | {source_hash}")
        print(f"  {snippet.replace(chr(10), '\\n')}")
        print()

    print("Immediate rendered_tex leftovers")
    print("--------------------------------")
    if not immediate_rendered_leftovers:
        print("[none]")
    else:
        for concept_id, slug, title in immediate_rendered_leftovers:
            print(f"{concept_id} | {slug} | {title}")


if __name__ == "__main__":
    main()