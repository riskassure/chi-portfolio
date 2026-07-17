import sqlite3
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[3]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DB_PATH

from services.math.render_helper import (
    extract_standalone_pstree_diagram_blocks,
    hash_pstricks_block,
)


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, slug, cleaned_tex
        FROM math_concepts
        WHERE cleaned_tex LIKE '%\\pstree%'
        ORDER BY id;
    """)

    rows = cursor.fetchall()

    block_mismatches = 0
    total_blocks = 0

    for concept_id, slug, cleaned_tex in rows:
        cleaned_tex = cleaned_tex or ""

        shared_blocks = extract_standalone_pstree_diagram_blocks(
            cleaned_tex
        )

        for block_index, block in enumerate(
            shared_blocks,
            start=1,
        ):
            total_blocks += 1

            expected_hash = hash_pstricks_block(
                block["conversion_source"]
            )

            if block["source_hash"] != expected_hash:
                block_mismatches += 1
                print(
                    f"[HASH MISMATCH] concept={concept_id} "
                    f"slug={slug} "
                    f"block={block_index}"
                )

    conn.close()

    print()
    print("PSTree shared extractor diagnostic")
    print(f"Concepts checked: {len(rows)}")
    print(f"Blocks checked: {total_blocks}")
    print(f"Hash mismatches: {block_mismatches}")


if __name__ == "__main__":
    main()