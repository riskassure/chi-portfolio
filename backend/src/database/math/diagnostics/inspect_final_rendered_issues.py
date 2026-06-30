import sqlite3
from pathlib import Path

import sys

SRC_DIR = Path(__file__).resolve().parents[3]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DB_PATH


TARGETS = {
    77: [r"\end{"],
    648: [r"\newcommand"],
    787: [r"\emph"],
    835: [r"\def"],
}


def show_context(text: str, needle: str, radius: int = 500) -> None:
    index = text.find(needle)

    if index == -1:
        print(f"Needle not found: {needle}")
        return

    start = max(0, index - radius)
    end = min(len(text), index + len(needle) + radius)

    print("-" * 100)
    print(f"NEEDLE: {needle}")
    print("-" * 100)
    print(text[start:end])
    print()


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for concept_id, needles in TARGETS.items():
        cursor.execute("""
            SELECT id, cleaned_tex, rendered_tex
            FROM math_concepts
            WHERE id = ?;
        """, (concept_id,))

        row = cursor.fetchone()

        if not row:
            print(f"Missing concept {concept_id}")
            continue

        concept_id, cleaned_tex, rendered_tex = row

        print("=" * 100)
        print(f"Concept {concept_id}")
        print("=" * 100)

        print("\nCLEANED_TEX CONTEXTS")
        for needle in needles:
            show_context(cleaned_tex or "", needle)

        print("\nRENDERED_TEX CONTEXTS")
        for needle in needles:
            show_context(rendered_tex or "", needle)

    conn.close()


if __name__ == "__main__":
    main()