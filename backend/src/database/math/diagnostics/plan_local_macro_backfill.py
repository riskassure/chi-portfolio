# backend/src/database/math/diagnostics/plan_local_macro_backfill.py

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

# Existing local definitions should occur at the beginning of cleaned_tex.
# Limiting the scan avoids treating examples later in the article as active
# prelude definitions.
CLEANED_PRELUDE_SCAN_LIMIT = 12000


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

        # Exclude non-command findings such as:
        #
        #   [PMMATHPROSEBLOCK_LEAK]
        #
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
    Match a leading local definition using either form:

        \\newcommand{\\foo}{...}
        \\newcommand\\foo{...}

    Starred definitions and argument-count groups are also accepted.
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


def classify_existing_definition(
    definition: LocalMacroDefinition,
    cleaned_tex: str,
) -> str:
    """
    Return one of:

        already_present
        conflict
        missing
    """

    cleaned_prefix = (
        cleaned_tex
        or ""
    ).lstrip()[:CLEANED_PRELUDE_SCAN_LIMIT]

    if definition.source_text in cleaned_prefix:
        return "already_present"

    pattern = make_existing_definition_pattern(
        definition.token
    )

    if pattern.search(cleaned_prefix):
        return "conflict"

    return "missing"


def build_proposed_cleaned_tex(
    cleaned_tex: str,
    missing_definitions: list[LocalMacroDefinition],
) -> str:
    """
    Prepend missing definitions while preserving the current cleaned_tex body
    exactly apart from existing outer leading whitespace.

    The existing body is never replaced with the original raw document body.
    """

    prelude = "\n".join(
        definition.source_text
        for definition in missing_definitions
    ).strip()

    existing = (
        cleaned_tex
        or ""
    ).lstrip()

    parts = [
        part
        for part in (
            prelude,
            existing,
        )
        if part
    ]

    return "\n\n".join(parts)


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


def print_definition_list(
    title: str,
    definitions: list[LocalMacroDefinition],
) -> None:
    if not definitions:
        return

    print()
    print(title)

    for definition in definitions:
        print(
            f"  {definition.token}: "
            f"{definition.source_text}"
        )


def inspect_concept(
    row: sqlite3.Row,
) -> dict[str, int]:
    unresolved = load_unresolved_commands(
        row["issue_summary"]
    )

    raw_content = row["raw_content"] or ""
    cleaned_tex = row["cleaned_tex"] or ""

    counts = {
        "problematic_concepts_scanned": 1,
        "concepts_with_recoverable_red_commands": 0,
        "concepts_ready_for_backfill": 0,
        "concepts_already_complete": 0,
        "concepts_skipped_for_conflict": 0,
        "recoverable_red_commands": 0,
        "definitions_to_prepend": 0,
        "red_definitions_to_prepend": 0,
        "companion_definitions_to_prepend": 0,
        "missing_raw_sources": 0,
    }

    if not unresolved:
        return counts

    if not raw_content:
        counts["missing_raw_sources"] += 1

        print()
        print("=" * 96)
        print(
            f'{row["concept_id"]}: '
            f'{row["title"]} '
            f'[{row["slug"]}]'
        )
        print("=" * 96)
        print("STATUS: no linked raw source")

        return counts

    harvest = extract_local_newcommands(
        raw_content
    )

    used_definitions = harvest.used_definitions

    used_by_token = {
        definition.token: definition
        for definition in used_definitions
    }

    recoverable_commands = {
        command: count
        for command, count in unresolved.items()
        if command in used_by_token
    }

    # The concept is outside this backfill when none of its current red
    # commands has a supported, used definition in the original source.
    if not recoverable_commands:
        return counts

    counts[
        "concepts_with_recoverable_red_commands"
    ] += 1

    counts["recoverable_red_commands"] += len(
        recoverable_commands
    )

    already_present: list[
        LocalMacroDefinition
    ] = []

    missing: list[
        LocalMacroDefinition
    ] = []

    conflicts: list[
        LocalMacroDefinition
    ] = []

    # Once a concept qualifies for backfill, retain all supported definitions
    # actually used by that document—not only the definitions whose commands
    # happen to be red in the current audit.
    for definition in used_definitions:
        status = classify_existing_definition(
            definition,
            cleaned_tex,
        )

        if status == "already_present":
            already_present.append(
                definition
            )

        elif status == "conflict":
            conflicts.append(
                definition
            )

        else:
            missing.append(
                definition
            )

    print()
    print("=" * 96)
    print(
        f'{row["concept_id"]}: '
        f'{row["title"]} '
        f'[{row["slug"]}]'
    )
    print("=" * 96)

    print(
        "Recoverable red commands: "
        + format_command_counts(
            recoverable_commands
        )
    )

    print(
        "Used local definitions in raw source: "
        f"{len(used_definitions)}"
    )

    red_missing = [
        definition
        for definition in missing
        if definition.token in recoverable_commands
    ]

    companion_missing = [
        definition
        for definition in missing
        if definition.token not in recoverable_commands
    ]

    print_definition_list(
        "ALREADY PRESENT:",
        already_present,
    )

    print_definition_list(
        "RED DEFINITIONS — PROPOSED FOR PREPEND:",
        red_missing,
    )

    print_definition_list(
        "COMPANION DEFINITIONS — ALSO USED BY THIS BODY:",
        companion_missing,
    )

    print_definition_list(
        "CONFLICT — CONCEPT WILL BE SKIPPED:",
        conflicts,
    )

    if conflicts:
        counts[
            "concepts_skipped_for_conflict"
        ] += 1

        print()
        print(
            "STATUS: skipped because cleaned_tex already "
            "defines at least one token differently."
        )

        return counts

    if not missing:
        counts[
            "concepts_already_complete"
        ] += 1

        print()
        print(
            "STATUS: no backfill needed; all used local "
            "definitions are already present."
        )

        return counts

    proposed_cleaned_tex = (
        build_proposed_cleaned_tex(
            cleaned_tex,
            missing,
        )
    )

    counts[
        "concepts_ready_for_backfill"
    ] += 1

    counts["definitions_to_prepend"] += len(
        missing
    )

    counts["red_definitions_to_prepend"] += len(
        red_missing
    )

    counts["companion_definitions_to_prepend"] += len(
        companion_missing
    )

    print()
    print("STATUS: ready for backfill")
    print(
        f"Current cleaned_tex length: "
        f"{len(cleaned_tex):,}"
    )
    print(
        f"Proposed cleaned_tex length: "
        f"{len(proposed_cleaned_tex):,}"
    )

    print()
    print("Proposed beginning of cleaned_tex:")
    print("-" * 96)
    print(
        proposed_cleaned_tex[:1000]
        or "[empty]"
    )

    return counts


def add_counts(
    totals: dict[str, int],
    current: dict[str, int],
) -> None:
    for key, value in current.items():
        totals[key] = (
            totals.get(key, 0)
            + value
        )


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

        print("Local macro backfill plan")
        print(f"Database: {DB_PATH}")
        print(
            f'Audit run: {audit_run["id"]} '
            f'({audit_run["audit_version"]})'
        )
        print("Mode: READ-ONLY")
        print(
            "Existing cleaned_tex bodies will be preserved."
        )

        for row in rows:
            concept_counts = inspect_concept(
                row
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
            "problematic_concepts_scanned",
            "concepts_with_recoverable_red_commands",
            "concepts_ready_for_backfill",
            "concepts_already_complete",
            "concepts_skipped_for_conflict",
            "recoverable_red_commands",
            "definitions_to_prepend",
            "red_definitions_to_prepend",
            "companion_definitions_to_prepend",
            "missing_raw_sources",
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