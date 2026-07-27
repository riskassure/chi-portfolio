# backend/src/database/math/diagnostics/inspect_local_macro_harvest.py

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[3]

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from config import DB_PATH
from services.math.local_macro_helper import (
    extract_local_newcommands,
)

from database.math.pipeline.step1_load_relational import (
    transform_latex_content,
)

TARGET_SLUGS = (
    "octonion",
    "axiom-of-dependent-choices",
)


def print_section(title: str) -> None:
    print()
    print("=" * 88)
    print(title)
    print("=" * 88)


def inspect_concept(row: sqlite3.Row) -> None:
    slug = row["slug"]
    title = row["title"]
    raw_content = row["raw_content"] or ""
    existing_cleaned_tex = row["cleaned_tex"] or ""

    print_section(
        f'{row["id"]}: {title} [{slug}]'
    )

    if not raw_content:
        print("ERROR: No linked stg_math_import.raw_content was found.")
        return

    result = extract_local_newcommands(raw_content)

    transformed = transform_latex_content(
        raw_content
    )

    step1_cleaned_tex = (
        transformed["cleaned_tex"]
        if transformed
        else ""
    )

    print(
        f"Harvested supported definitions: "
        f"{len(result.definitions)}"
    )

    for definition in result.definitions:
        print()
        print(
            f"  {definition.token}"
            f"  arguments={definition.argument_count}"
        )
        print(
            f"  replacement={definition.replacement!r}"
        )
        print(
            f"  source={definition.source_text}"
        )

    print()
    print(
        f"Unsupported definition-like constructs: "
        f"{len(result.unsupported)}"
    )

    for unsupported in result.unsupported:
        print()
        print(f"  command={unsupported.command}")
        print(f"  reason={unsupported.reason}")
        print(f"  source={unsupported.source_text}")

    print()
    print(
        f"Document body length: "
        f"{len(result.document_body):,}"
    )
    print(
        f"Existing cleaned_tex length: "
        f"{len(existing_cleaned_tex):,}"
    )
    print(
        f"Used-definition cleaned preview length: "
        f"{len(result.used_cleaned_tex_preview):,}"
    )

    print()
    print("Harvested prelude:")
    print("-" * 88)

    if result.prelude_tex:
        print(result.prelude_tex)
    else:
        print("[none]")

    print()
    print(
        "Definitions actually referenced by the document body: "
        f"{len(result.used_definitions)}"
    )
    print("-" * 88)

    if result.used_definitions:
        for definition in result.used_definitions:
            print(
                f"{definition.token}: "
                f"{definition.source_text}"
            )
    else:
        print("[none]")

    print()
    print("Beginning of used-definition cleaned_tex preview:")
    print("-" * 88)
    print(
        result.used_cleaned_tex_preview[:1200]
        or "[empty]"
    )

    print()
    print(
        "Existing cleaned_tex already starts with "
        "the used-definition prelude:"
    )

    already_present = (
        bool(result.used_prelude_tex)
        and existing_cleaned_tex
        .lstrip()
        .startswith(
            result.used_prelude_tex.strip()
        )
    )

    print(already_present)

    print()
    print(
        "Step 1 transformed cleaned_tex matches "
        "the used-definition preview:"
    )

    print(
        step1_cleaned_tex
        == result.used_cleaned_tex_preview
    )


def main() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    try:
        placeholders = ", ".join(
            "?"
            for _slug in TARGET_SLUGS
        )

        rows = conn.execute(
            f"""
            SELECT
                concept.id,
                concept.slug,
                concept.title,
                concept.cleaned_tex,
                concept.source_staging_id,
                staging.raw_content
            FROM math_concepts concept
            LEFT JOIN stg_math_import staging
              ON staging.id = concept.source_staging_id
            WHERE concept.slug IN ({placeholders})
            ORDER BY concept.slug;
            """,
            TARGET_SLUGS,
        ).fetchall()

        found_slugs = {
            row["slug"]
            for row in rows
        }

        missing_slugs = [
            slug
            for slug in TARGET_SLUGS
            if slug not in found_slugs
        ]

        if missing_slugs:
            raise RuntimeError(
                "Concept slug(s) not found: "
                + ", ".join(missing_slugs)
            )

        print("Local macro harvest diagnostic")
        print(f"Database: {DB_PATH}")
        print("Read-only: yes")

        for row in rows:
            inspect_concept(row)

        print_section("DIAGNOSTIC COMPLETE")
        print(
            "No database rows were inserted, updated, or deleted."
        )

    finally:
        conn.close()


if __name__ == "__main__":
    main()