import sqlite3
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[3]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DB_PATH

from routes.admin_math import (
    compare_pstricks_hashes,
    render_tex_reusing_existing_diagrams,
)

from services.math.render_helper import (
    extract_all_pstricks_diagram_blocks,
)


TEST_CONCEPT_IDS = [696, 832]


def main():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    total_errors = 0

    for concept_id in TEST_CONCEPT_IDS:
        cursor.execute("""
            SELECT slug, title, cleaned_tex
            FROM math_concepts
            WHERE id = ?;
        """, (concept_id,))

        row = cursor.fetchone()

        if row is None:
            print(f"Concept {concept_id}: NOT FOUND")
            total_errors += 1
            continue

        slug, title, cleaned_tex = row
        cleaned_tex = cleaned_tex or ""

        blocks = extract_all_pstricks_diagram_blocks(cleaned_tex)

        comparison = compare_pstricks_hashes(
            cleaned_tex,
            cleaned_tex,
        )

        rendered_tex = render_tex_reusing_existing_diagrams(
            concept_id=concept_id,
            cleaned_tex=cleaned_tex,
            cursor=cursor,
        )

        img_count = rendered_tex.count(
            'class="math-diagram"'
        )

        raw_pspicture = "\\begin{pspicture}" in rendered_tex
        raw_pstree = "\\pstree" in rendered_tex

        errors = []

        if comparison["pstricks_changed"]:
            errors.append(
                "unchanged TeX was incorrectly marked as changed"
            )

        if comparison["old_count"] != len(blocks):
            errors.append(
                "comparison block count does not match combined extractor"
            )

        if img_count != len(blocks):
            errors.append(
                f"expected {len(blocks)} diagram images, found {img_count}"
            )

        if raw_pspicture:
            errors.append("raw pspicture remained in rendered output")

        if raw_pstree:
            errors.append("raw pstree remained in rendered output")

        print()
        print(f"Concept {concept_id}: {slug}")
        print(f"Title: {title}")
        print(f"Supported blocks: {len(blocks)}")
        print(f"Rendered diagram images: {img_count}")
        print(
            "Unchanged comparison: "
            f"{comparison['pstricks_changed']}"
        )

        if errors:
            total_errors += len(errors)

            for error in errors:
                print(f"ERROR: {error}")
        else:
            print("Result: PASS")

    conn.close()

    print()
    print(f"Total errors: {total_errors}")


if __name__ == "__main__":
    main()