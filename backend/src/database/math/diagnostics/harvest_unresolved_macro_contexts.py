# backend/src/database/math/diagnostics/harvest_unresolved_macro_contexts.py

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[3]  # backend/src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DB_PATH, MATH_DATA_DIR


COMMAND_RE = re.compile(r"^\\[A-Za-z@]+(?:\*)?$")
COMMAND_TOKEN_RE = re.compile(r"\\[A-Za-z@]+(?:\*)?")

DEFINITION_HINT_RE = re.compile(
    r"\\(?:newcommand|renewcommand|providecommand|"
    r"DeclareMathOperator|def|let)\*?",
    re.IGNORECASE,
)

OUTPUT_DIR = MATH_DATA_DIR / "diagnostics"

SOURCE_COLUMNS = (
    "raw_content",
    "cleaned_tex",
    "rendered_tex",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Collect source contexts for unresolved commands from the latest "
            "persisted MathJax audit."
        )
    )

    parser.add_argument(
        "--run-id",
        type=int,
        default=None,
        help=(
            "Specific completed math_audit_runs.id. "
            "Default: latest completed run."
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Output directory. Default: {OUTPUT_DIR}",
    )

    return parser.parse_args()


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


def get_audit_run(
    conn: sqlite3.Connection,
    run_id: int | None,
) -> sqlite3.Row:
    if run_id is not None:
        row = conn.execute(
            """
            SELECT *
            FROM math_audit_runs
            WHERE id = ?
              AND completed_at IS NOT NULL;
            """,
            (run_id,),
        ).fetchone()
    else:
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
            "No matching completed audit run was found."
        )

    return row


def load_command_inventory(
    conn: sqlite3.Connection,
    run_id: int,
) -> dict[str, dict]:
    """
    Read the persisted audit summaries and build one inventory
    record for each unresolved backslash command.
    """
    rows = conn.execute(
        """
        SELECT
            result.concept_id,
            result.issue_summary,
            concept.slug,
            concept.title
        FROM math_concept_audit_results result
        JOIN math_concepts concept
          ON concept.id = result.concept_id
        WHERE result.run_id = ?
          AND result.status = 'problematic'
        ORDER BY concept.id;
        """,
        (run_id,),
    ).fetchall()

    inventory: dict[str, dict] = {}

    for row in rows:
        try:
            summary = json.loads(row["issue_summary"] or "")
        except (TypeError, json.JSONDecodeError):
            continue

        if not isinstance(summary, dict):
            continue

        for command, raw_count in summary.items():
            command = str(command or "").strip()

            # Excludes entries such as:
            # [PMMATHPROSEBLOCK_LEAK]
            if not COMMAND_RE.fullmatch(command):
                continue

            try:
                count = int(raw_count or 0)
            except (TypeError, ValueError):
                count = 0

            item = inventory.setdefault(
                command,
                {
                    "command": command,
                    "audit_hits": 0,
                    "concepts": {},
                },
            )

            item["audit_hits"] += count

            item["concepts"][row["concept_id"]] = {
                "slug": row["slug"] or "",
                "title": row["title"] or "",
                "count": count,
            }

    return inventory


def load_concept_sources(
    conn: sqlite3.Connection,
) -> list[sqlite3.Row]:
    """
    Retrieve all available TeX layers.

    Original raw source is held in stg_math_import.raw_content
    and linked through math_concepts.source_staging_id.
    """
    if table_exists(conn, "stg_math_import"):
        return conn.execute(
            """
            SELECT
                concept.id,
                concept.slug,
                concept.title,
                staging.raw_content,
                concept.cleaned_tex,
                concept.rendered_tex
            FROM math_concepts concept
            LEFT JOIN stg_math_import staging
              ON staging.id = concept.source_staging_id
            ORDER BY concept.id;
            """
        ).fetchall()

    return conn.execute(
        """
        SELECT
            id,
            slug,
            title,
            NULL AS raw_content,
            cleaned_tex,
            rendered_tex
        FROM math_concepts
        ORDER BY id;
        """
    ).fetchall()


def normalize_context(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def make_context(
    text: str,
    start: int,
    end: int,
    radius: int = 260,
) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)

    return normalize_context(text[left:right])


def is_definition_context(
    text: str,
    command_start: int,
) -> bool:
    """
    Treat the command occurrence as definition-related when a
    definition command occurs shortly before it.
    """
    prefix = text[
        max(0, command_start - 180):
        command_start
    ]

    return DEFINITION_HINT_RE.search(prefix) is not None


def collect_contexts(
    concepts: list[sqlite3.Row],
    commands: set[str],
) -> tuple[
    dict[str, list[dict]],
    dict[str, list[dict]],
]:
    """
    Search all concepts and all available TeX layers.

    We collect:
      - up to 12 definition-like contexts per command;
      - up to 3 ordinary usage contexts per command.
    """
    definition_contexts: dict[str, list[dict]] = defaultdict(list)
    usage_contexts: dict[str, list[dict]] = defaultdict(list)

    definition_seen: dict[str, set[str]] = defaultdict(set)
    usage_seen: dict[str, set[str]] = defaultdict(set)

    for row in concepts:
        for source_column in SOURCE_COLUMNS:
            text = row[source_column] or ""

            if not text:
                continue

            for match in COMMAND_TOKEN_RE.finditer(text):
                command = match.group(0)

                if command not in commands:
                    continue

                context = make_context(
                    text,
                    match.start(),
                    match.end(),
                )

                normalized_key = context.casefold()

                record = {
                    "command": command,
                    "source_concept_id": row["id"],
                    "source_slug": row["slug"] or "",
                    "source_title": row["title"] or "",
                    "source_column": source_column,
                    "context": context,
                }

                if is_definition_context(text, match.start()):
                    if (
                        normalized_key
                        not in definition_seen[command]
                        and len(definition_contexts[command]) < 12
                    ):
                        definition_seen[command].add(
                            normalized_key
                        )

                        definition_contexts[command].append(
                            record
                        )

                elif (
                    normalized_key
                    not in usage_seen[command]
                    and len(usage_contexts[command]) < 3
                ):
                    usage_seen[command].add(
                        normalized_key
                    )

                    usage_contexts[command].append(
                        record
                    )

    return definition_contexts, usage_contexts


def write_inventory(
    path: Path,
    inventory: dict[str, dict],
    definition_contexts: dict[str, list[dict]],
    usage_contexts: dict[str, list[dict]],
) -> None:
    fields = [
        "command",
        "audit_hits",
        "affected_concept_count",
        "affected_slugs",
        "definition_context_count",
        "sample_definition_context",
        "sample_definition_source",
        "sample_usage_context",
        "sample_usage_source",
        "status",
    ]

    ordered = sorted(
        inventory.values(),
        key=lambda item: (
            -item["audit_hits"],
            item["command"].lower(),
        ),
    )

    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
        )

        writer.writeheader()

        for item in ordered:
            command = item["command"]

            definitions = definition_contexts.get(
                command,
                [],
            )

            usages = usage_contexts.get(
                command,
                [],
            )

            first_definition = (
                definitions[0]
                if definitions
                else None
            )

            first_usage = (
                usages[0]
                if usages
                else None
            )

            writer.writerow({
                "command": command,
                "audit_hits": item["audit_hits"],
                "affected_concept_count": len(
                    item["concepts"]
                ),
                "affected_slugs": " | ".join(
                    sorted(
                        concept["slug"]
                        for concept
                        in item["concepts"].values()
                        if concept["slug"]
                    )
                ),
                "definition_context_count": len(
                    definitions
                ),
                "sample_definition_context": (
                    first_definition["context"]
                    if first_definition
                    else ""
                ),
                "sample_definition_source": (
                    (
                        f'{first_definition["source_slug"]}:'
                        f'{first_definition["source_column"]}'
                    )
                    if first_definition
                    else ""
                ),
                "sample_usage_context": (
                    first_usage["context"]
                    if first_usage
                    else ""
                ),
                "sample_usage_source": (
                    (
                        f'{first_usage["source_slug"]}:'
                        f'{first_usage["source_column"]}'
                    )
                    if first_usage
                    else ""
                ),
                "status": (
                    "definition_context_found"
                    if definitions
                    else "usage_only"
                ),
            })


def write_context_details(
    path: Path,
    definition_contexts: dict[str, list[dict]],
) -> None:
    fields = [
        "command",
        "source_concept_id",
        "source_slug",
        "source_title",
        "source_column",
        "context",
    ]

    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
        )

        writer.writeheader()

        for command in sorted(
            definition_contexts,
            key=str.lower,
        ):
            for row in definition_contexts[command]:
                writer.writerow(row)


def main() -> None:
    args = parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    try:
        required_tables = {
            "math_audit_runs",
            "math_concept_audit_results",
            "math_concepts",
        }

        missing_tables = sorted(
            table_name
            for table_name in required_tables
            if not table_exists(conn, table_name)
        )

        if missing_tables:
            raise RuntimeError(
                "Missing required table(s): "
                + ", ".join(missing_tables)
            )

        audit_run = get_audit_run(
            conn,
            args.run_id,
        )

        inventory = load_command_inventory(
            conn,
            audit_run["id"],
        )

        if not inventory:
            raise RuntimeError(
                f"Audit run {audit_run['id']} "
                "contains no unresolved commands."
            )

        concepts = load_concept_sources(conn)

        definitions, usages = collect_contexts(
            concepts,
            set(inventory),
        )

        inventory_path = (
            output_dir
            / (
                "unresolved_macro_inventory_"
                f"run_{audit_run['id']}.csv"
            )
        )

        contexts_path = (
            output_dir
            / (
                "unresolved_macro_definition_contexts_"
                f"run_{audit_run['id']}.csv"
            )
        )

        write_inventory(
            inventory_path,
            inventory,
            definitions,
            usages,
        )

        write_context_details(
            contexts_path,
            definitions,
        )

        commands_with_definitions = sum(
            bool(definitions.get(command))
            for command in inventory
        )

        print("Macro context harvest complete.")
        print(f"   Database: {DB_PATH}")

        print(
            f"   Audit run: {audit_run['id']} "
            f"({audit_run['audit_version']})"
        )

        print(
            f"   Unresolved commands: "
            f"{len(inventory)}"
        )

        print(
            "   Commands with definition-like contexts: "
            f"{commands_with_definitions}"
        )

        print(f"   Inventory: {inventory_path}")
        print(f"   Definition contexts: {contexts_path}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()