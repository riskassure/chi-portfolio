# backend/src/database/math/diagnostics/rerender_pmlinkname_concepts.py

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path


THIS_FILE = Path(__file__).resolve()
SRC_DIR = THIS_FILE.parents[3]  # backend/src

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DB_PATH
from services.math.render_helper import render_prose_latex_to_html


PMLINKNAME_COMMAND = r"\PMlinkname"
PSPICTURE_COMMAND = r"\begin{pspicture}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Selectively regenerate rendered_tex for concepts whose "
            "cleaned_tex contains \\PMlinkname."
        )
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Write regenerated rendered_tex values to the database. "
            "Without this option, the script performs a dry run."
        ),
    )

    return parser.parse_args()


def load_target_concepts(
    connection: sqlite3.Connection,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            id,
            slug,
            title,
            cleaned_tex,
            rendered_tex
        FROM math_concepts
        WHERE cleaned_tex LIKE '%\\PMlinkname%'
        ORDER BY id;
        """
    ).fetchall()


def main() -> None:
    args = parse_args()

    mode = "APPLY" if args.apply else "DRY RUN"

    print(r"\PMlinkname selective re-render")
    print("=" * 80)
    print(f"Mode: {mode}")
    print(f"Database: {DB_PATH}")
    print()

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        rows = load_target_concepts(connection)

        eligible_rows: list[sqlite3.Row] = []
        skipped_pstricks: list[sqlite3.Row] = []

        for row in rows:
            cleaned_tex = row["cleaned_tex"] or ""

            if PSPICTURE_COMMAND in cleaned_tex:
                skipped_pstricks.append(row)
            else:
                eligible_rows.append(row)

        print(f"Concepts containing {PMLINKNAME_COMMAND}: {len(rows)}")
        print(f"Eligible for selective re-render: {len(eligible_rows)}")
        print(f"Skipped because of PSTricks: {len(skipped_pstricks)}")
        print()

        if skipped_pstricks:
            print("Skipped PSTricks concepts")
            print("-" * 80)

            for row in skipped_pstricks:
                print(
                    f'{row["id"]} | '
                    f'{row["slug"]} | '
                    f'{row["title"]}'
                )

            print()

        changed_rows: list[tuple[str, int]] = []
        unchanged_rows: list[sqlite3.Row] = []
        failed_rows: list[tuple[sqlite3.Row, Exception]] = []

        for row in eligible_rows:
            cleaned_tex = row["cleaned_tex"] or ""
            existing_rendered_tex = row["rendered_tex"] or ""

            try:
                regenerated_tex = render_prose_latex_to_html(
                    cleaned_tex
                )
            except Exception as exc:
                failed_rows.append((row, exc))
                continue

            if regenerated_tex == existing_rendered_tex:
                unchanged_rows.append(row)
                continue

            changed_rows.append(
                (
                    regenerated_tex,
                    row["id"],
                )
            )

        print("Re-render analysis")
        print("-" * 80)
        print(f"Would change: {len(changed_rows)}")
        print(f"Already current: {len(unchanged_rows)}")
        print(f"Rendering failures: {len(failed_rows)}")
        print()

        if failed_rows:
            print("Rendering failures")
            print("-" * 80)

            for row, exc in failed_rows:
                print(
                    f'{row["id"]} | '
                    f'{row["slug"]} | '
                    f'{row["title"]}'
                )
                print(f"  {type(exc).__name__}: {exc}")

            print()

        if not args.apply:
            print("Dry run complete. No database rows were updated.")
            print()
            print("Run again with --apply to update rendered_tex:")
            print(
                "python "
                r".\backend\src\database\math\diagnostics"
                r"\rerender_pmlinkname_concepts.py --apply"
            )
            return

        if failed_rows:
            raise RuntimeError(
                "One or more concepts failed to render. "
                "No database changes were applied."
            )

        if not changed_rows:
            print("No rendered_tex values require updating.")
            return

        try:
            connection.execute("BEGIN;")

            connection.executemany(
                """
                UPDATE math_concepts
                SET rendered_tex = ?
                WHERE id = ?;
                """,
                changed_rows,
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        print(
            f"Successfully updated rendered_tex for "
            f"{len(changed_rows)} concepts."
        )

    except Exception as exc:
        connection.rollback()

        print()
        print("ERROR")
        print("-" * 80)
        print(f"{type(exc).__name__}: {exc}")
        print("All pending database changes were rolled back.")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()