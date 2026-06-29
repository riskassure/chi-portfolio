import re
import sqlite3
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[3]  # backend/src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DB_PATH


TARGET_COMMANDS = [
    r"\\textbf",
    r"\\emph",
    r"\\item",
]


def show_context(text: str, pattern: str, window: int = 350) -> list[str]:
    contexts = []

    for match in re.finditer(pattern, text):
        start = max(match.start() - window, 0)
        end = min(match.end() + window, len(text))
        contexts.append(text[start:end])

    return contexts


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT id, title, cleaned_tex, rendered_tex
        FROM math_concepts
        ORDER BY id;
    """).fetchall()

    for row in rows:
        rendered_tex = row["rendered_tex"] or ""

        found_any = False
        output_chunks = []

        for command in TARGET_COMMANDS:
            contexts = show_context(rendered_tex, command)

            if contexts:
                found_any = True
                output_chunks.append(f"\n--- {command} ---")

                for context in contexts:
                    output_chunks.append(context)

        if found_any:
            print("\n" + "=" * 100)
            print(f'{row["id"]}: {row["title"]}')
            print("=" * 100)
            print("\n".join(output_chunks))

    conn.close()


if __name__ == "__main__":
    main()