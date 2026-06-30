import re
import sqlite3
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[3]  # backend/src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DB_PATH


TARGET_ENVIRONMENTS = [
    "multicols",
    "prooftree",
    "stp",
    "thebibliography",
    "Large",
    "conv",
    "thmplain",
    "warning",
    "bibliography",
    "supertabular",
    "program",
    "alg",
]


def find_environment_blocks(text: str, env_name: str) -> list[str]:
    pattern = re.compile(
        rf"\\begin\{{{re.escape(env_name)}\}}[\s\S]*?\\end\{{{re.escape(env_name)}\}}",
        flags=re.IGNORECASE,
    )
    return pattern.findall(text)


def find_environment_contexts(text: str, env_name: str, window: int = 700) -> list[str]:
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
            blocks = find_environment_blocks(rendered_tex, env_name)

            if blocks:
                output_chunks.append(f"\n--- {env_name}: full matched blocks ---")

                for block_index, block in enumerate(blocks, start=1):
                    output_chunks.append(f"\n[{env_name} block {block_index}]")
                    output_chunks.append(block[:2500])

            else:
                contexts = find_environment_contexts(rendered_tex, env_name)

                if contexts:
                    output_chunks.append(f"\n--- {env_name}: unmatched begin contexts ---")

                    for context_index, context in enumerate(contexts, start=1):
                        output_chunks.append(f"\n[{env_name} context {context_index}]")
                        output_chunks.append(context[:2500])

        if output_chunks:
            print("\n" + "=" * 100)
            print(f'{row["id"]}: {row["title"]}')
            print("=" * 100)
            print("\n".join(output_chunks))

    conn.close()


if __name__ == "__main__":
    main()