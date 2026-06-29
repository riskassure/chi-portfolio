# backend/src/database/math/diagnostics/summarize_rendered_environments.py

import sys
import re
import sqlite3
from pathlib import Path
from collections import Counter

SRC_DIR = Path(__file__).resolve().parents[3]  # backend/src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DB_PATH

MATHJAX_ALLOWED_ENVIRONMENTS = {
    "align",
    "align*",
    "alignat",
    "alignat*",
    "equation",
    "equation*",
    "eqnarray",
    "eqnarray*",
    "gather",
    "gather*",
    "multline",
    "multline*",
    "displaymath",
    "split",
    "cases",
    "matrix",
    "pmatrix",
    "bmatrix",
    "Bmatrix",
    "vmatrix",
    "Vmatrix",
    "smallmatrix",
    "array",
}


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT id, title, rendered_tex
        FROM math_concepts
        ORDER BY id;
    """).fetchall()

    env_counter = Counter()
    command_counter = Counter()

    for row in rows:
        rendered_tex = row["rendered_tex"] or ""

        for env in re.findall(r"\\begin\{([^}]+)\}", rendered_tex):
            if env not in MATHJAX_ALLOWED_ENVIRONMENTS:
                env_counter[env] += 1

        for cmd in re.findall(r"\\([A-Za-z]+)", rendered_tex):
            command_counter[cmd] += 1

    print("Environment counts:")
    print("=" * 80)
    for env, count in env_counter.most_common(50):
        print(f"{env}: {count}")

    print()
    print("Command counts:")
    print("=" * 80)
    for cmd, count in command_counter.most_common(50):
        print(f"\\{cmd}: {count}")

    conn.close()


if __name__ == "__main__":
    main()