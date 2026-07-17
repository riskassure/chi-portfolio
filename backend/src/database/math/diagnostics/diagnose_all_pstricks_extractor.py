import sqlite3
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[3]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DB_PATH

from services.math.render_helper import (
    extract_all_pstricks_diagram_blocks,
)


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, slug, cleaned_tex
        FROM math_concepts
        WHERE cleaned_tex LIKE '%\\begin{pspicture}%'
           OR cleaned_tex LIKE '%\\pstree%'
        ORDER BY id;
    """)

    rows = cursor.fetchall()

    total_blocks = 0
    pspicture_blocks = 0
    pstree_blocks = 0
    ordering_errors = 0
    overlap_errors = 0

    for concept_id, slug, cleaned_tex in rows:
        cleaned_tex = cleaned_tex or ""

        blocks = extract_all_pstricks_diagram_blocks(cleaned_tex)

        previous_start = -1
        previous_end = -1

        for block_index, block in enumerate(blocks, start=1):
            total_blocks += 1

            if block["kind"] == "pspicture":
                pspicture_blocks += 1
            elif block["kind"] == "pstree":
                pstree_blocks += 1

            if block["start"] < previous_start:
                ordering_errors += 1
                print(
                    f"[ORDER ERROR] concept={concept_id} "
                    f"slug={slug} "
                    f"block={block_index}"
                )

            if previous_end > block["start"]:
                overlap_errors += 1
                print(
                    f"[OVERLAP ERROR] concept={concept_id} "
                    f"slug={slug} "
                    f"block={block_index}"
                )

            previous_start = block["start"]
            previous_end = block["end"]

    conn.close()

    print()
    print("Combined PSTricks extractor diagnostic")
    print(f"Concepts checked: {len(rows)}")
    print(f"Total blocks: {total_blocks}")
    print(f"pspicture blocks: {pspicture_blocks}")
    print(f"pstree blocks: {pstree_blocks}")
    print(f"Ordering errors: {ordering_errors}")
    print(f"Overlap errors: {overlap_errors}")


if __name__ == "__main__":
    main()