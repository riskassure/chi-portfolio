import re
import sqlite3
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[3]  # backend/src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DB_PATH


TABULAR_RE = re.compile(
    r"\\begin\{tabular\}(?:\{[^{}]*\})?[\s\S]*?\\end\{tabular\}",
    flags=re.IGNORECASE,
)


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT id, title, cleaned_tex, rendered_tex
        FROM math_concepts
        WHERE rendered_tex LIKE '%\\begin{tabular}%'
        ORDER BY id
        LIMIT 20;
    """).fetchall()

    for row in rows:
        print("\n" + "=" * 100)
        print(f'{row["id"]}: {row["title"]}')
        print("=" * 100)

        rendered_tex = row["rendered_tex"] or ""
        matches = TABULAR_RE.findall(rendered_tex)

        for i, block in enumerate(matches, start=1):
            print(f"\n--- tabular block {i} ---")
            print(block[:2000])

    conn.close()


if __name__ == "__main__":
    main()