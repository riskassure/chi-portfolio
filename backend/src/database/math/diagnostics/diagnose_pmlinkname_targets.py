# backend/src/database/math/diagnostics/diagnose_pmlinkname_targets.py

from __future__ import annotations

import csv
import sqlite3
import sys
from collections import Counter
from pathlib import Path


THIS_FILE = Path(__file__).resolve()
SRC_DIR = THIS_FILE.parents[3]  # backend/src

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DB_PATH, MATH_DATA_DIR


COMMAND = r"\PMlinkname"
OUTPUT_PATH = MATH_DATA_DIR / "pmlinkname_target_diagnostics.csv"


def find_matching_brace(text: str, opening_index: int) -> int:
    """
    Return the index of the closing brace matching text[opening_index].

    Nested braces are supported. Escaped braces such as \\{ and \\}
    are ignored.

    Return -1 if no matching closing brace is found.
    """
    if (
        opening_index < 0
        or opening_index >= len(text)
        or text[opening_index] != "{"
    ):
        return -1

    depth = 0
    index = opening_index

    while index < len(text):
        char = text[index]

        if char == "\\":
            # Skip an escaped character, including escaped braces.
            index += 2
            continue

        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1

            if depth == 0:
                return index

        index += 1

    return -1


def skip_whitespace(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1

    return index


def compact_snippet(
    text: str,
    start: int,
    end: int,
    radius: int = 120,
) -> str:
    snippet_start = max(0, start - radius)
    snippet_end = min(len(text), end + radius)

    return (
        text[snippet_start:snippet_end]
        .replace("\r", "")
        .replace("\n", r"\n")
        .replace("\t", " ")
        .strip()
    )


def compact_label(text: str) -> str:
    return (
        text
        .replace("\r", "")
        .replace("\n", " ")
        .replace("\t", " ")
        .strip()
    )


def parse_pmlinkname_occurrences(text: str) -> list[dict[str, object]]:
    """
    Parse every \\PMlinkname{label}{target} occurrence in the supplied text.

    Each returned dictionary contains:

        command_start
        command_end
        visible_label
        legacy_target
        parse_status
        parse_message
        snippet

    parse_status is initially one of:

        PARSED
        MALFORMED
        EMPTY_LABEL
        EMPTY_TARGET

    Successfully parsed targets are later classified as FOUND or MISSING.
    """
    findings: list[dict[str, object]] = []
    search_start = 0

    while True:
        command_start = text.find(COMMAND, search_start)

        if command_start == -1:
            break

        cursor = command_start + len(COMMAND)
        cursor = skip_whitespace(text, cursor)

        if cursor >= len(text) or text[cursor] != "{":
            command_end = min(
                len(text),
                command_start + len(COMMAND),
            )

            findings.append({
                "command_start": command_start,
                "command_end": command_end,
                "visible_label": "",
                "legacy_target": "",
                "parse_status": "MALFORMED",
                "parse_message": "Missing opening brace for visible label",
                "snippet": compact_snippet(
                    text,
                    command_start,
                    command_end,
                ),
            })

            search_start = command_start + len(COMMAND)
            continue

        label_open = cursor
        label_close = find_matching_brace(text, label_open)

        if label_close == -1:
            findings.append({
                "command_start": command_start,
                "command_end": len(text),
                "visible_label": "",
                "legacy_target": "",
                "parse_status": "MALFORMED",
                "parse_message": "Unclosed visible-label argument",
                "snippet": compact_snippet(
                    text,
                    command_start,
                    len(text),
                ),
            })

            # The rest of the text belongs to an unclosed argument.
            break

        visible_label = text[label_open + 1:label_close]
        cursor = skip_whitespace(text, label_close + 1)

        if cursor >= len(text) or text[cursor] != "{":
            command_end = label_close + 1

            findings.append({
                "command_start": command_start,
                "command_end": command_end,
                "visible_label": visible_label,
                "legacy_target": "",
                "parse_status": "MALFORMED",
                "parse_message": "Missing opening brace for target",
                "snippet": compact_snippet(
                    text,
                    command_start,
                    command_end,
                ),
            })

            search_start = command_end
            continue

        target_open = cursor
        target_close = find_matching_brace(text, target_open)

        if target_close == -1:
            findings.append({
                "command_start": command_start,
                "command_end": len(text),
                "visible_label": visible_label,
                "legacy_target": "",
                "parse_status": "MALFORMED",
                "parse_message": "Unclosed target argument",
                "snippet": compact_snippet(
                    text,
                    command_start,
                    len(text),
                ),
            })

            break

        legacy_target = text[target_open + 1:target_close]
        command_end = target_close + 1

        stripped_label = visible_label.strip()
        stripped_target = legacy_target.strip()

        if not stripped_label:
            parse_status = "EMPTY_LABEL"
            parse_message = "Visible-label argument is empty"
        elif not stripped_target:
            parse_status = "EMPTY_TARGET"
            parse_message = "Target argument is empty"
        else:
            parse_status = "PARSED"
            parse_message = ""

        findings.append({
            "command_start": command_start,
            "command_end": command_end,
            "visible_label": visible_label,
            "legacy_target": legacy_target,
            "parse_status": parse_status,
            "parse_message": parse_message,
            "snippet": compact_snippet(
                text,
                command_start,
                command_end,
            ),
        })

        search_start = command_end

    return findings


def load_concepts(
    connection: sqlite3.Connection,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            id,
            slug,
            title,
            canonical_name,
            cleaned_tex
        FROM math_concepts
        WHERE cleaned_tex LIKE '%\\PMlinkname%'
        ORDER BY id;
        """
    ).fetchall()


def load_canonical_name_lookup(
    connection: sqlite3.Connection,
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """
    Return:

      1. canonical_name.casefold() -> slug
      2. duplicate canonical-name keys -> list of slugs

    Duplicate canonical names are reported separately because they make
    target resolution ambiguous.
    """
    rows = connection.execute(
        """
        SELECT canonical_name, slug
        FROM math_concepts
        WHERE canonical_name IS NOT NULL
          AND TRIM(canonical_name) <> ''
          AND slug IS NOT NULL
          AND TRIM(slug) <> ''
        ORDER BY id;
        """
    ).fetchall()

    slugs_by_canonical: dict[str, list[str]] = {}

    for row in rows:
        canonical_name = row["canonical_name"].strip()
        slug = row["slug"].strip()
        key = canonical_name.casefold()

        slugs_by_canonical.setdefault(key, []).append(slug)

    lookup: dict[str, str] = {}
    duplicates: dict[str, list[str]] = {}

    for key, slugs in slugs_by_canonical.items():
        unique_slugs = list(dict.fromkeys(slugs))

        if len(unique_slugs) == 1:
            lookup[key] = unique_slugs[0]
        else:
            duplicates[key] = unique_slugs

    return lookup, duplicates


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        concepts = load_concepts(connection)
        canonical_lookup, duplicate_targets = (
            load_canonical_name_lookup(connection)
        )

        report_rows: list[dict[str, object]] = []
        status_counter: Counter[str] = Counter()
        unique_targets: set[str] = set()
        unique_missing_targets: set[str] = set()
        concepts_with_occurrences: set[int] = set()

        for concept in concepts:
            concept_id = concept["id"]
            source_slug = concept["slug"] or ""
            source_title = concept["title"] or ""
            source_canonical_name = concept["canonical_name"] or ""
            cleaned_tex = concept["cleaned_tex"] or ""

            occurrences = parse_pmlinkname_occurrences(cleaned_tex)

            for occurrence_number, occurrence in enumerate(
                occurrences,
                start=1,
            ):
                concepts_with_occurrences.add(concept_id)

                visible_label = str(
                    occurrence["visible_label"]
                ).strip()

                legacy_target = str(
                    occurrence["legacy_target"]
                ).strip()

                parse_status = str(occurrence["parse_status"])
                parse_message = str(occurrence["parse_message"])

                resolved_slug = ""
                status = parse_status
                message = parse_message

                if parse_status == "PARSED":
                    target_key = legacy_target.casefold()
                    unique_targets.add(target_key)

                    if target_key in duplicate_targets:
                        status = "AMBIGUOUS"
                        candidate_slugs = duplicate_targets[target_key]
                        message = (
                            "Canonical target matches multiple local slugs: "
                            + ", ".join(candidate_slugs)
                        )
                    else:
                        resolved_slug = canonical_lookup.get(
                            target_key,
                            "",
                        )

                        if resolved_slug:
                            status = "FOUND"
                            message = ""
                        else:
                            status = "MISSING"
                            message = (
                                "No local math_concepts row has this "
                                "canonical_name"
                            )
                            unique_missing_targets.add(target_key)

                status_counter[status] += 1

                report_rows.append({
                    "concept_id": concept_id,
                    "source_slug": source_slug,
                    "source_title": source_title,
                    "source_canonical_name": source_canonical_name,
                    "occurrence_number": occurrence_number,
                    "visible_label": compact_label(visible_label),
                    "legacy_target": legacy_target,
                    "resolved_slug": resolved_slug,
                    "status": status,
                    "message": message,
                    "snippet": occurrence["snippet"],
                })

    finally:
        connection.close()

    fieldnames = [
        "concept_id",
        "source_slug",
        "source_title",
        "source_canonical_name",
        "occurrence_number",
        "visible_label",
        "legacy_target",
        "resolved_slug",
        "status",
        "message",
        "snippet",
    ]

    with OUTPUT_PATH.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(report_rows)

    total_occurrences = len(report_rows)

    print(r"\PMlinkname target diagnostic")
    print("=" * 80)
    print(f"Database: {DB_PATH}")
    print(f"Concepts containing command: {len(concepts_with_occurrences)}")
    print(f"Total occurrences: {total_occurrences}")
    print(f"Unique non-empty targets: {len(unique_targets)}")
    print(f"Unique missing targets: {len(unique_missing_targets)}")
    print()

    print("Status counts")
    print("-" * 80)

    status_order = [
        "FOUND",
        "MISSING",
        "AMBIGUOUS",
        "MALFORMED",
        "EMPTY_LABEL",
        "EMPTY_TARGET",
    ]

    for status in status_order:
        print(f"{status:15} {status_counter.get(status, 0)}")

    print()

    missing_rows = [
        row
        for row in report_rows
        if row["status"] == "MISSING"
    ]

    print("Missing targets")
    print("-" * 80)

    if not missing_rows:
        print("[none]")
    else:
        shown_targets: set[str] = set()

        for row in missing_rows:
            target_key = str(row["legacy_target"]).casefold()

            if target_key in shown_targets:
                continue

            shown_targets.add(target_key)

            print(
                f'{row["legacy_target"]} '
                f'| source: {row["source_slug"]} '
                f'| label: {row["visible_label"]}'
            )

    print()

    problem_rows = [
        row
        for row in report_rows
        if row["status"] in {
            "AMBIGUOUS",
            "MALFORMED",
            "EMPTY_LABEL",
            "EMPTY_TARGET",
        }
    ]

    print("Malformed or ambiguous occurrences")
    print("-" * 80)

    if not problem_rows:
        print("[none]")
    else:
        for row in problem_rows:
            print(
                f'{row["concept_id"]} | '
                f'{row["source_slug"]} | '
                f'occurrence {row["occurrence_number"]} | '
                f'{row["status"]}'
            )
            print(f'  Target: {row["legacy_target"]}')
            print(f'  Message: {row["message"]}')
            print(f'  Snippet: {row["snippet"]}')
            print()

    print()
    print(f"CSV report written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()