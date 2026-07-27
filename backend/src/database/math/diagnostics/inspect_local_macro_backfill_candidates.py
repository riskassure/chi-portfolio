# backend/src/database/math/diagnostics/
# inspect_local_macro_backfill_candidates.py

from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[3]

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from config import DB_PATH
from services.math.local_macro_helper import (
    LocalMacroDefinition,
    extract_local_newcommands,
)


COMMAND_RE = re.compile(
    r"^\\[A-Za-z@]+(?:\*)?$"
)

# Only inspect the beginning of cleaned_tex for existing local definitions.
# This avoids mistaking an example shown later in prose or verbatim text for
# the actual concept prelude.
CLEANED_PRELUDE_SCAN_LIMIT = 8000


def table_exists(
    conn: sqlite3.Connection,
    table_name: str,
) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?;
        """,
        (table_name,),
    ).fetchone()

    return row is not None


def get_latest_completed_audit_run(
    conn: sqlite3.Connection,
) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT *
        FROM math_audit_runs
        WHERE completed_at IS NOT NULL
        ORDER BY completed_at DESC, id DESC
        LIMIT 1;
        """
    ).fetchone()

    if row is None:
        raise RuntimeError(
            "No completed MathJax audit run was found."
        )

    return row


def load_problematic_concepts(
    conn: sqlite3.Connection,
    run_id: int,
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
            result.concept_id,
            result.issue_summary,
            concept.slug,
            concept.title,
            concept.cleaned_tex,
            concept.source_staging_id,
            staging.raw_content
        FROM math_concept_audit_results result
        JOIN math_concepts concept
          ON concept.id = result.concept_id
        LEFT JOIN stg_math_import staging
          ON staging.id = concept.source_staging_id
        WHERE result.run_id = ?
          AND result.status = 'problematic'
        ORDER BY concept.slug, concept.id;
        """,
        (run_id,),
    ).fetchall()


def load_unresolved_commands(
    issue_summary: str,
) -> dict[str, int]:
    try:
        parsed = json.loads(
            issue_summary or ""
        )
    except (
        TypeError,
        json.JSONDecodeError,
    ):
        return {}

    if not isinstance(parsed, dict):
        return {}

    commands: dict[str, int] = {}

    for raw_command, raw_count in parsed.items():
        command = str(
            raw_command or ""
        ).strip()

        if not COMMAND_RE.fullmatch(command):
            continue

        try:
            count = int(raw_count or 0)
        except (
            TypeError,
            ValueError,
        ):
            count = 0

        commands[command] = count

    return commands


def make_existing_definition_pattern(
    token: str,
) -> re.Pattern[str]:
    """
    Detect either:

        \\newcommand{\\foo}
        \\newcommand*{\\foo}
        \\newcommand\\foo
        \\newcommand*\\foo

    We do not parse the replacement here. A definition with the same name
    but different source text is classified as a conflict for manual review.
    """

    escaped_token = re.escape(token)

    return re.compile(
        rf"""
        \\newcommand
        \*?
        \s*
        (?:
            \{{\s*{escaped_token}\s*\}}
            |
            {escaped_token}
        )
        (?=
            \s
            |
            \[
            |
            \{{
        )
        """,
        re.VERBOSE,
    )


def classify_definition(
    definition: LocalMacroDefinition,
    cleaned_tex: str,
) -> str:
    """
    Return one of:

        already_present
        conflict
        safe_to_prepend
    """

    cleaned_prefix = (
        cleaned_tex
        or ""
    ).lstrip()[:CLEANED_PRELUDE_SCAN_LIMIT]

    if definition.source_text in cleaned_prefix:
        return "already_present"

    existing_pattern = (
        make_existing_definition_pattern(
            definition.token
        )
    )

    if existing_pattern.search(cleaned_prefix):
        return "conflict"

    return "safe_to_prepend"


def format_command_counts(
    commands: dict[str, int],
) -> str:
    return ", ".join(
        f"{command} ({count})"
        for command, count in sorted(
            commands.items(),
            key=lambda item: item[0].lower(),
        )
    )


def print_concept_report(
    row: sqlite3.Row,
) -> dict[str, int]:
    unresolved = load_unresolved_commands(
        row["issue_summary"]
    )

    raw_content = row["raw_content"] or ""
    cleaned_tex = row["cleaned_tex"] or ""

    counts = {
        "problematic_concepts": 1,
        "concepts_with_matching_definitions": 0,
        "concepts_safe_to_backfill": 0,
        "safe_definitions": 0,
        "already_present_definitions": 0,
        "conflicting_definitions": 0,
        "commands_without_source_definition": 0,
        "unsupported_constructs": 0,
        "missing_raw_source": 0,
    }

    print()
    print("=" * 96)
    print(
        f'{row["concept_id"]}: '
        f'{row["title"]} '
        f'[{row["slug"]}]'
    )
    print("=" * 96)

    print(
        "Audit commands: "
        + (
            format_command_counts(unresolved)
            or "[none]"
        )
    )

    if not raw_content:
        print("STATUS: no linked raw source")
        counts["missing_raw_source"] += 1
        counts[
            "commands_without_source_definition"
        ] += len(unresolved)

        return counts

    harvest = extract_local_newcommands(
        raw_content
    )

    harvested_by_token = {
        definition.token: definition
        for definition in harvest.definitions
    }

    matching_definitions = [
        harvested_by_token[command]
        for command in unresolved
        if command in harvested_by_token
    ]

    commands_without_definition = {
        command: count
        for command, count in unresolved.items()
        if command not in harvested_by_token
    }

    safe_definitions = []
    already_present_definitions = []
    conflicting_definitions = []

    for definition in matching_definitions:
        classification = classify_definition(
            definition,
            cleaned_tex,
        )

        if classification == "safe_to_prepend":
            safe_definitions.append(definition)

        elif classification == "already_present":
            already_present_definitions.append(
                definition
            )

        else:
            conflicting_definitions.append(
                definition
            )

    if matching_definitions:
        counts[
            "concepts_with_matching_definitions"
        ] += 1

    if safe_definitions:
        counts[
            "concepts_safe_to_backfill"
        ] += 1

    counts["safe_definitions"] += len(
        safe_definitions
    )

    counts[
        "already_present_definitions"
    ] += len(
        already_present_definitions
    )

    counts[
        "conflicting_definitions"
    ] += len(
        conflicting_definitions
    )

    counts[
        "commands_without_source_definition"
    ] += len(
        commands_without_definition
    )

    counts["unsupported_constructs"] += len(
        harvest.unsupported
    )

    print()
    print(
        "Supported definitions harvested from raw source: "
        f"{len(harvest.definitions)}"
    )

    if safe_definitions:
        print()
        print("SAFE TO PREPEND:")

        for definition in safe_definitions:
            print(
                f"  {definition.token}: "
                f"{definition.source_text}"
            )

    if already_present_definitions:
        print()
        print("ALREADY PRESENT:")

        for definition in already_present_definitions:
            print(
                f"  {definition.token}: "
                f"{definition.source_text}"
            )

    if conflicting_definitions:
        print()
        print("CONFLICT — MANUAL REVIEW REQUIRED:")

        for definition in conflicting_definitions:
            print(
                f"  {definition.token}"
            )
            print(
                f"    raw source: "
                f"{definition.source_text}"
            )

    if commands_without_definition:
        print()
        print(
            "NO MATCHING SUPPORTED DEFINITION "
            "IN THIS CONCEPT'S RAW PREAMBLE:"
        )

        for command, count in sorted(
            commands_without_definition.items(),
            key=lambda item: item[0].lower(),
        ):
            print(
                f"  {command}: {count} audit hit(s)"
            )

    if harvest.unsupported:
        print()
        print("UNSUPPORTED DEFINITION-LIKE CONSTRUCTS:")

        for unsupported in harvest.unsupported:
            print(
                f"  {unsupported.command}: "
                f"{unsupported.reason}"
            )
            print(
                f"    {unsupported.source_text}"
            )

    if (
        not safe_definitions
        and not already_present_definitions
        and not conflicting_definitions
    ):
        print()
        print(
            "STATUS: no automatically usable local "
            "definition for the audit commands."
        )

    return counts


def add_counts(
    total: dict[str, int],
    current: dict[str, int],
) -> None:
    for key, value in current.items():
        total[key] = total.get(key, 0) + value


def main() -> None:
    conn = sqlite3.connect(
        str(DB_PATH)
    )

    conn.row_factory = sqlite3.Row

    totals: dict[str, int] = {}

    try:
        required_tables = {
            "math_audit_runs",
            "math_concept_audit_results",
            "math_concepts",
            "stg_math_import",
        }

        missing_tables = sorted(
            table_name
            for table_name in required_tables
            if not table_exists(
                conn,
                table_name,
            )
        )

        if missing_tables:
            raise RuntimeError(
                "Missing required table(s): "
                + ", ".join(missing_tables)
            )

        audit_run = (
            get_latest_completed_audit_run(
                conn
            )
        )

        rows = load_problematic_concepts(
            conn,
            audit_run["id"],
        )

        print(
            "Local macro backfill candidate inspection"
        )
        print(f"Database: {DB_PATH}")
        print(
            f'Audit run: {audit_run["id"]} '
            f'({audit_run["audit_version"]})'
        )
        print("Read-only: yes")

        for row in rows:
            concept_counts = (
                print_concept_report(row)
            )

            add_counts(
                totals,
                concept_counts,
            )

        print()
        print("=" * 96)
        print("SUMMARY")
        print("=" * 96)

        summary_order = (
            "problematic_concepts",
            "concepts_with_matching_definitions",
            "concepts_safe_to_backfill",
            "safe_definitions",
            "already_present_definitions",
            "conflicting_definitions",
            "commands_without_source_definition",
            "unsupported_constructs",
            "missing_raw_source",
        )

        for key in summary_order:
            print(
                f"{key}: "
                f"{totals.get(key, 0)}"
            )

        print()
        print(
            "No database rows were inserted, "
            "updated, or deleted."
        )

    finally:
        conn.close()


if __name__ == "__main__":
    main()