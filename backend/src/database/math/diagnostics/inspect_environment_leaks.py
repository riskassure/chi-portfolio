import re
import sqlite3
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[3]  # backend/src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DB_PATH


TARGET_ENVIRONMENTS = [
    "center",
    "multicols",
    "verbatim",
    "figure",
    "minipage",
    "proof",
    "prooftree",
    "thebibliography",
    "quote",
]


def find_environment_contexts(text: str, env_name: str, window: int = 500) -> list[str]:
    pattern = re.compile(
        rf"\\begin\{{{re.escape(env_name)}\}}",
        flags=re.IGNORECASE,
    )

    contexts = []

    for match in pattern.finditer(text):
        start = max(match.start() - window, 0)
        end = min(match.end() + window, len(text))
        contexts.append(text[start:end])

    return contexts


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT id, title, rendered_tex
        FROM math_concepts
        ORDER BY id;
    """).fetchall()

    for row in rows:
        rendered_tex = row["rendered_tex"] or ""

        output_chunks = []

        for env_name in TARGET_ENVIRONMENTS:
            contexts = find_environment_contexts(rendered_tex, env_name)

            if contexts:
                output_chunks.append(f"\n--- {env_name} ---")

                for context in contexts:
                    output_chunks.append(context)

        if output_chunks:
            print("\n" + "=" * 100)
            print(f'{row["id"]}: {row["title"]}')
            print("=" * 100)
            print("\n".join(output_chunks))

    conn.close()


if __name__ == "__main__":
    main()