# backend/src/utils/math/diagnose_psset_before_pspicture.py

import re
import sys
import sqlite3
from pathlib import Path


THIS_FILE = Path(__file__).resolve()

# Expected location:
# backend/src/database/math/diagnostics/diagnose_psset_before_pspicture.py
SRC_DIR = THIS_FILE.parents[3]      # backend/src
BACKEND_DIR = THIS_FILE.parents[4]  # backend

for path in (SRC_DIR, BACKEND_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from config import DB_PATH


PSSET_RE = re.compile(
    r"\\psset\s*\{[^{}]*\}",
    re.IGNORECASE
)

PSPICTURE_BEGIN_RE = re.compile(
    r"\\begin\{pspicture\}",
    re.IGNORECASE
)


def compact_snippet(text, start, end):
    snippet = text[max(0, start):min(len(text), end)]
    return (
        snippet
        .replace("\r", "")
        .replace("\n", "\\n")
        .replace("\t", " ")
    )


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, slug, title, cleaned_tex
        FROM math_concepts
        WHERE cleaned_tex LIKE '%psset%'
           OR cleaned_tex LIKE '%pspicture%'
        ORDER BY id ASC;
    """)

    rows = cursor.fetchall()
    conn.close()

    total_psset = 0
    psset_before_any_pspicture = 0
    immediate_psset_before_pspicture = 0
    concepts_with_immediate = set()

    immediate_examples = []
    non_immediate_examples = []

    for concept_id, slug, title, cleaned_tex in rows:
        text = cleaned_tex or ""

        for psset_match in PSSET_RE.finditer(text):
            total_psset += 1

            next_picture = PSPICTURE_BEGIN_RE.search(text, psset_match.end())

            if not next_picture:
                non_immediate_examples.append({
                    "concept_id": concept_id,
                    "slug": slug,
                    "title": title,
                    "psset": psset_match.group(0),
                    "reason": "No following pspicture",
                    "snippet": compact_snippet(text, psset_match.start() - 120, psset_match.end() + 160),
                })
                continue

            psset_before_any_pspicture += 1
            between = text[psset_match.end():next_picture.start()]

            # For tomorrow's Step 2 fix, this is the safest first target:
            # \psset{...}
            # \begin{pspicture}
            #
            # with only whitespace between them.
            if between.strip() == "":
                immediate_psset_before_pspicture += 1
                concepts_with_immediate.add(concept_id)

                immediate_examples.append({
                    "concept_id": concept_id,
                    "slug": slug,
                    "title": title,
                    "psset": psset_match.group(0),
                    "snippet": compact_snippet(text, psset_match.start() - 120, next_picture.end() + 160),
                })
            else:
                non_immediate_examples.append({
                    "concept_id": concept_id,
                    "slug": slug,
                    "title": title,
                    "psset": psset_match.group(0),
                    "reason": f"Text between psset and pspicture: {repr(between[:80])}",
                    "snippet": compact_snippet(text, psset_match.start() - 120, next_picture.end() + 160),
                })

    print("PSTricks \\psset diagnostic")
    print("==========================")
    print(f"Total \\psset occurrences: {total_psset}")
    print(f"\\psset before a later pspicture: {psset_before_any_pspicture}")
    print(f"Immediately before pspicture: {immediate_psset_before_pspicture}")
    print(f"Concepts with immediate psset+pspicture: {len(concepts_with_immediate)}")
    print()

    print("Immediate examples")
    print("------------------")
    if not immediate_examples:
        print("[none]")
    else:
        for row in immediate_examples[:50]:
            print(f"{row['concept_id']} | {row['slug']} | {row['title']}")
            print(f"  {row['psset']}")
            print(f"  {row['snippet']}")
            print()

    print()
    print("Other psset examples")
    print("--------------------")
    if not non_immediate_examples:
        print("[none]")
    else:
        for row in non_immediate_examples[:25]:
            print(f"{row['concept_id']} | {row['slug']} | {row['title']}")
            print(f"  {row['psset']}")
            print(f"  {row['reason']}")
            print(f"  {row['snippet']}")
            print()


if __name__ == "__main__":
    main()