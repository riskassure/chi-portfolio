# backend/src/database/math/migrations/backfill_local_macro_preludes.py

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
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

BACKUP_DIR = (
    Path(DB_PATH).parent
    / "backups"
)

EXPECTED_PROBLEMATIC_CONCEPTS = 34
EXPECTED_RECOVERABLE_CONCEPTS = 19
EXPECTED_RECOVERABLE_COMMANDS = 20

EXPECTED_UPDATE_COUNT = 19
EXPECTED_DEFINITION_COUNT = 29
EXPECTED_RED_DEFINITION_COUNT = 20
EXPECTED_COMPANION_DEFINITION_COUNT = 9


@dataclass(frozen=True)
class BackfillUpdate:
    """
    One validated cleaned_tex update proposed by this migration.
    """

    concept_id: int
    slug: str
    title: str
    original_cleaned_tex: str
    proposed_cleaned_tex: str

    missing_definitions: tuple[
        LocalMacroDefinition,
        ...
    ]

    red_definition_count: int
    companion_definition_count: int

    @property
    def definition_count(self) -> int:
        return len(self.missing_definitions)


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
) -> tuple[
    dict[str, int],
    BackfillUpdate | None,
]:
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
        return counts, None

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

        return counts, None

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
        return counts, None

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

        return counts, None

    if not missing:
        counts[
            "concepts_already_complete"
        ] += 1

        print()
        print(
            "STATUS: no backfill needed; all used local "
            "definitions are already present."
        )

        return counts, None

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

    update = BackfillUpdate(
        concept_id=int(row["concept_id"]),
        slug=str(row["slug"]),
        title=str(row["title"]),
        original_cleaned_tex=cleaned_tex,
        proposed_cleaned_tex=proposed_cleaned_tex,
        missing_definitions=tuple(missing),
        red_definition_count=len(red_missing),
        companion_definition_count=len(
            companion_missing
        ),
    )

    return counts, update


def add_counts(
    totals: dict[str, int],
    current: dict[str, int],
) -> None:
    for key, value in current.items():
        totals[key] = (
            totals.get(key, 0)
            + value
        )


def validate_update_plan(
    updates: list[BackfillUpdate],
    totals: dict[str, int],
) -> str:
    """
    Verify that the live database still matches the reviewed plan.

    Two states are accepted:

    ready
        All 19 concepts still require the reviewed 29 definitions.

    already_complete
        All 19 concepts already contain their definitions, making a
        repeated migration run safely idempotent.

    A partial or changed state is rejected for manual review.
    """

    errors: list[str] = []

    fixed_expectations = {
        "problematic_concepts_scanned":
            EXPECTED_PROBLEMATIC_CONCEPTS,
        "concepts_with_recoverable_red_commands":
            EXPECTED_RECOVERABLE_CONCEPTS,
        "recoverable_red_commands":
            EXPECTED_RECOVERABLE_COMMANDS,
        "concepts_skipped_for_conflict": 0,
        "missing_raw_sources": 0,
    }

    for key, expected_value in fixed_expectations.items():
        actual_value = totals.get(
            key,
            0,
        )

        if actual_value != expected_value:
            errors.append(
                f"{key}: expected {expected_value}, "
                f"found {actual_value}"
            )

    ready_count = totals.get(
        "concepts_ready_for_backfill",
        0,
    )

    complete_count = totals.get(
        "concepts_already_complete",
        0,
    )

    if (
        ready_count + complete_count
        != EXPECTED_RECOVERABLE_CONCEPTS
    ):
        errors.append(
            "Ready plus already-complete concepts: "
            f"expected {EXPECTED_RECOVERABLE_CONCEPTS}, "
            f"found {ready_count + complete_count}"
        )

    if len(updates) != ready_count:
        errors.append(
            "Collected update count does not match "
            "concepts_ready_for_backfill: "
            f"{len(updates)} versus {ready_count}"
        )

    concept_ids = [
        update.concept_id
        for update in updates
    ]

    if len(concept_ids) != len(set(concept_ids)):
        errors.append(
            "Duplicate concept IDs were collected."
        )

    slugs = [
        update.slug
        for update in updates
    ]

    if len(slugs) != len(set(slugs)):
        errors.append(
            "Duplicate concept slugs were collected."
        )

    collected_definition_count = sum(
        update.definition_count
        for update in updates
    )

    collected_red_count = sum(
        update.red_definition_count
        for update in updates
    )

    collected_companion_count = sum(
        update.companion_definition_count
        for update in updates
    )

    aggregate_expectations = {
        "definitions_to_prepend":
            collected_definition_count,
        "red_definitions_to_prepend":
            collected_red_count,
        "companion_definitions_to_prepend":
            collected_companion_count,
    }

    for key, expected_value in aggregate_expectations.items():
        actual_value = totals.get(
            key,
            0,
        )

        if actual_value != expected_value:
            errors.append(
                f"{key} does not match collected updates: "
                f"{actual_value} versus {expected_value}"
            )

    for update in updates:
        if update.definition_count == 0:
            errors.append(
                f"{update.slug}: update contains no definitions."
            )

        if (
            update.red_definition_count
            + update.companion_definition_count
            != update.definition_count
        ):
            errors.append(
                f"{update.slug}: red plus companion counts "
                "do not equal the definition count."
            )

        if (
            update.original_cleaned_tex
            == update.proposed_cleaned_tex
        ):
            errors.append(
                f"{update.slug}: proposed cleaned_tex "
                "is unchanged."
            )

        expected_prelude = "\n".join(
            definition.source_text
            for definition in update.missing_definitions
        ).strip()

        proposed = (
            update.proposed_cleaned_tex
            or ""
        ).lstrip()

        if not proposed.startswith(expected_prelude):
            errors.append(
                f"{update.slug}: proposed cleaned_tex does "
                "not begin with the expected prelude."
            )

        original_body = (
            update.original_cleaned_tex
            or ""
        ).lstrip()

        if (
            original_body
            and not proposed.endswith(original_body)
        ):
            errors.append(
                f"{update.slug}: existing cleaned_tex body "
                "was not preserved exactly."
            )

    if (
        ready_count == EXPECTED_UPDATE_COUNT
        and complete_count == 0
    ):
        state = "ready"

        reviewed_counts = {
            "definitions_to_prepend":
                EXPECTED_DEFINITION_COUNT,
            "red_definitions_to_prepend":
                EXPECTED_RED_DEFINITION_COUNT,
            "companion_definitions_to_prepend":
                EXPECTED_COMPANION_DEFINITION_COUNT,
        }

        for key, expected_value in reviewed_counts.items():
            actual_value = totals.get(
                key,
                0,
            )

            if actual_value != expected_value:
                errors.append(
                    f"{key}: expected reviewed value "
                    f"{expected_value}, found {actual_value}"
                )

    elif (
        ready_count == 0
        and complete_count
        == EXPECTED_RECOVERABLE_CONCEPTS
    ):
        state = "already_complete"

        if updates:
            errors.append(
                "Already-complete state unexpectedly "
                "contains proposed updates."
            )

        for key in (
            "definitions_to_prepend",
            "red_definitions_to_prepend",
            "companion_definitions_to_prepend",
        ):
            if totals.get(key, 0) != 0:
                errors.append(
                    f"{key} should be zero in the "
                    "already-complete state."
                )

    else:
        state = "invalid_partial_state"

        errors.append(
            "The database is in an unreviewed partial state: "
            f"{ready_count} ready and "
            f"{complete_count} already complete."
        )

    if errors:
        raise RuntimeError(
            "Backfill validation failed:\n- "
            + "\n- ".join(errors)
        )

    return state


def create_database_backup(
    source_conn: sqlite3.Connection,
) -> Path:
    """
    Create and verify a timestamped SQLite backup.

    SQLite's backup API is used instead of copying the database file
    directly, so the backup remains valid even when SQLite journaling
    or WAL files are active.
    """

    database_path = Path(DB_PATH)

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    suffix = (
        database_path.suffix
        or ".db"
    )

    backup_path = (
        BACKUP_DIR
        / (
            f"{database_path.stem}"
            f"_before_local_macro_backfill_"
            f"{timestamp}"
            f"{suffix}"
        )
    )

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if backup_path.exists():
        raise RuntimeError(
            f"Backup path already exists: "
            f"{backup_path}"
        )

    backup_conn = sqlite3.connect(
        str(backup_path)
    )

    try:
        source_conn.backup(
            backup_conn
        )

        backup_conn.commit()

    finally:
        backup_conn.close()

    if (
        not backup_path.is_file()
        or backup_path.stat().st_size == 0
    ):
        raise RuntimeError(
            "SQLite backup was not created correctly: "
            f"{backup_path}"
        )

    verification_conn = sqlite3.connect(
        str(backup_path)
    )

    try:
        integrity_row = verification_conn.execute(
            "PRAGMA integrity_check;"
        ).fetchone()

    finally:
        verification_conn.close()

    if (
        integrity_row is None
        or integrity_row[0] != "ok"
    ):
        raise RuntimeError(
            "SQLite backup failed integrity verification: "
            f"{backup_path}"
        )

    return backup_path


def apply_backfill_updates(
    conn: sqlite3.Connection,
    updates: list[BackfillUpdate],
) -> int:
    """
    Apply every validated cleaned_tex update in one transaction.

    Each UPDATE uses optimistic locking against the cleaned_tex value
    inspected during planning. If any row has changed since inspection,
    the entire transaction is rolled back.
    """

    if not updates:
        return 0

    try:
        conn.execute(
            "BEGIN IMMEDIATE;"
        )

        for update in updates:
            cursor = conn.execute(
                """
                UPDATE math_concepts
                SET cleaned_tex = ?
                WHERE id = ?
                  AND slug = ?
                  AND COALESCE(cleaned_tex, '') = ?;
                """,
                (
                    update.proposed_cleaned_tex,
                    update.concept_id,
                    update.slug,
                    update.original_cleaned_tex,
                ),
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    "Optimistic-lock validation failed for "
                    f"{update.concept_id}: {update.slug}. "
                    "The row may have changed since the plan "
                    "was constructed."
                )

        placeholders = ", ".join(
            "?"
            for _update in updates
        )

        verification_rows = conn.execute(
            f"""
            SELECT
                id,
                slug,
                cleaned_tex
            FROM math_concepts
            WHERE id IN ({placeholders});
            """,
            tuple(
                update.concept_id
                for update in updates
            ),
        ).fetchall()

        verification_by_id = {
            int(row["id"]): row
            for row in verification_rows
        }

        if len(verification_by_id) != len(updates):
            raise RuntimeError(
                "Post-update verification did not return "
                "every expected concept."
            )

        for update in updates:
            row = verification_by_id.get(
                update.concept_id
            )

            if row is None:
                raise RuntimeError(
                    "Post-update verification could not find "
                    f"{update.concept_id}: {update.slug}."
                )

            if str(row["slug"]) != update.slug:
                raise RuntimeError(
                    "Post-update slug mismatch for concept "
                    f"{update.concept_id}."
                )

            stored_cleaned_tex = (
                row["cleaned_tex"]
                or ""
            )

            if (
                stored_cleaned_tex
                != update.proposed_cleaned_tex
            ):
                raise RuntimeError(
                    "Post-update cleaned_tex verification "
                    f"failed for {update.concept_id}: "
                    f"{update.slug}."
                )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    return len(updates)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill concept-local macro preludes "
            "into math_concepts.cleaned_tex."
        )
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Create a verified SQLite backup and apply "
            "the validated cleaned_tex updates."
        ),
    )

    return parser.parse_args()


def main(
    apply: bool = False,
) -> None:
    conn = sqlite3.connect(
        str(DB_PATH)
    )

    conn.row_factory = sqlite3.Row

    totals: dict[str, int] = {}
    updates: list[BackfillUpdate] = []

    backup_path: Path | None = None
    applied_count = 0

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

        print("Local macro prelude backfill")
        print(f"Database: {DB_PATH}")
        print(
            f'Audit run: {audit_run["id"]} '
            f'({audit_run["audit_version"]})'
        )

        if apply:
            print("Mode: APPLY")
        else:
            print("Mode: DRY RUN")
        print(
            "Existing cleaned_tex bodies will be preserved."
        )

        for row in rows:
            (
                concept_counts,
                update,
            ) = inspect_concept(
                row
            )

            add_counts(
                totals,
                concept_counts,
            )

            if update is not None:
                updates.append(update)

        validation_state = validate_update_plan(
            updates,
            totals,
        )

        if apply:
            if validation_state == "ready":
                backup_path = create_database_backup(
                    conn
                )

                applied_count = apply_backfill_updates(
                    conn,
                    updates,
                )

            elif validation_state == "already_complete":
                applied_count = 0

            else:
                raise RuntimeError(
                    "Apply was requested for an unsupported "
                    f"validation state: {validation_state}"
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

        print(
            f"validated_updates_collected: "
            f"{len(updates)}"
        )

        print(
            f"validation_state: "
            f"{validation_state}"
        )

        print("validation_gates: passed")

        if apply:
            if backup_path is not None:
                print(
                    f"backup_path: "
                    f"{backup_path}"
                )
            else:
                print(
                    "backup_path: "
                    "[not created; no updates required]"
                )

            print(
                f"database_rows_updated: "
                f"{applied_count}"
            )

        print()

        if not apply:
            print(
                "No database rows were inserted, "
                "updated, or deleted."
            )

        elif validation_state == "already_complete":
            print(
                "No database updates were needed; "
                "the backfill was already complete."
            )

        else:
            print(
                "Database update committed successfully "
                f"for {applied_count} concepts."
            )

    finally:
        conn.close()


if __name__ == "__main__":
    arguments = parse_args()

    main(
        apply=arguments.apply,
    )