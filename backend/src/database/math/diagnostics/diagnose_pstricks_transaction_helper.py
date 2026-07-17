import sqlite3
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[3]

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
    
from config import DB_PATH

from database.math.pipeline.step2_build_diagrams import (
    process_pstricks_diagrams_in_transaction,
)


TEST_CONCEPT_IDS = [696, 832]


def main():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    total_errors = 0

    try:
        cursor.execute("BEGIN;")

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

            result = process_pstricks_diagrams_in_transaction(
                cursor=cursor,
                concept_id=concept_id,
                cleaned_tex=cleaned_tex,
            )

            rendered_tex = result["rendered_tex"]

            img_count = rendered_tex.count(
                'class="math-diagram"'
            )

            errors = []

            if result["failure_count"] != 0:
                errors.append(
                    f"expected 0 failures, found "
                    f"{result['failure_count']}"
                )

            if img_count != result["success_count"]:
                errors.append(
                    f"success count {result['success_count']} "
                    f"does not match image count {img_count}"
                )

            if "\\begin{pspicture}" in rendered_tex:
                errors.append(
                    "raw pspicture remained in rendered output"
                )

            if "\\pstree" in rendered_tex:
                errors.append(
                    "raw pstree remained in rendered output"
                )

            cursor.execute("""
                SELECT COUNT(*)
                FROM math_concept_diagrams
                WHERE concept_id = ?;
            """, (concept_id,))

            success_rows = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*)
                FROM math_concept_diagram_failures
                WHERE concept_id = ?;
            """, (concept_id,))

            failure_rows = cursor.fetchone()[0]

            if success_rows != result["success_count"]:
                errors.append(
                    f"expected {result['success_count']} success rows, "
                    f"found {success_rows}"
                )

            if failure_rows != result["failure_count"]:
                errors.append(
                    f"expected {result['failure_count']} failure rows, "
                    f"found {failure_rows}"
                )

            print()
            print(f"Concept {concept_id}: {slug}")
            print(f"Title: {title}")
            print(f"Blocks: {result['block_count']}")
            print(f"Successes: {result['success_count']}")
            print(f"Failures: {result['failure_count']}")
            print(f"Rendered images: {img_count}")
            print(f"Success rows: {success_rows}")
            print(f"Failure rows: {failure_rows}")

            if errors:
                total_errors += len(errors)

                for error in errors:
                    print(f"ERROR: {error}")
            else:
                print("Result: PASS")

    finally:
        conn.rollback()
        conn.close()

    print()
    print("Transaction rolled back.")
    print(f"Total errors: {total_errors}")


if __name__ == "__main__":
    main()