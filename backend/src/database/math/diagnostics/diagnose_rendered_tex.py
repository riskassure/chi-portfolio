# backend/src/utils/math/diagnose_rendered_tex.py

from __future__ import annotations

import csv
import re
import sqlite3
import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[3]  # backend/src
sys.path.append(str(SRC_DIR))

from config import DB_PATH, MATH_DATA_DIR


OUTPUT_PATH = MATH_DATA_DIR / "rendered_tex_diagnostics.csv"


ISSUE_PATTERNS = {
    "raw_latex_environment_leak": [
        r"\\begin\{",
        r"\\end\{",
    ],
    "raw_latex_command_leak": [
        r"\\section",
        r"\\subsection",
        r"\\paragraph",
        r"\\emph",
        r"\\textbf",
        r"\\item",
        r"\\cite",
        r"\\ref",
        r"\\label",
    ],
    "possible_bad_tabular": [
        r"\\begin\{tabular\}",
        r"\\end\{tabular\}",
        r"\\hline",
    ],
    "possible_bad_bibliography": [
        r"\\begin\{thebibliography\}",
        r"\\end\{thebibliography\}",
        r"\\bibitem",
    ],
    "possible_bad_diagram_placeholder": [
        r"\[diagram",
        r"diagram failed",
        r"missing diagram",
        r"diagram unavailable",
    ],
    "mathjax_risk": [
        r"\\newcommand",
        r"\\renewcommand",
        r"\\def",
    ],
}

MATHJAX_ALLOWED_ENVIRONMENTS = {
    "align",
    "align*",
    "equation",
    "equation*",
    "gather",
    "gather*",
    "multline",
    "multline*",
    "split",
    "cases",
    "matrix",
    "pmatrix",
    "bmatrix",
    "Bmatrix",
    "vmatrix",
    "Vmatrix",
    "array",
}


def remove_allowed_mathjax_environments(text: str) -> str:
    if not text:
        return ""

    cleaned = text

    for env in MATHJAX_ALLOWED_ENVIRONMENTS:
        env_pattern = re.escape(env)

        cleaned = re.sub(
            rf"\\begin\{{{env_pattern}\}}[\s\S]*?\\end\{{{env_pattern}\}}",
            "[MATHJAX_ENV]",
            cleaned,
            flags=re.IGNORECASE,
        )

    return cleaned


def compact_excerpt(text: str | None, pattern: str, radius: int = 120) -> str:
    if not text:
        return ""

    match = re.search(pattern, text, flags=re.IGNORECASE)

    if not match:
        return text[: radius * 2].replace("\n", " ").strip()

    start = max(match.start() - radius, 0)
    end = min(match.end() + radius, len(text))

    return text[start:end].replace("\n", " ").strip()


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT
            id,
            title,
            canonical_name,
            cleaned_tex,
            rendered_tex
        FROM math_concepts
        ORDER BY id;
        """
    ).fetchall()

    findings: list[dict[str, str | int]] = []

    for row in rows:
        concept_id = row["id"]
        title = row["title"] or ""
        canonical_name = row["canonical_name"] or ""
        cleaned_tex = row["cleaned_tex"] or ""
        rendered_tex = row["rendered_tex"] or ""
        rendered_tex_for_diagnostics = remove_allowed_mathjax_environments(rendered_tex)

        for issue_type, patterns in ISSUE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, rendered_tex_for_diagnostics, flags=re.IGNORECASE):
                    findings.append(
                        {
                            "concept_id": concept_id,
                            "title": title,
                            "canonical_name": canonical_name,
                            "source_field": "rendered_tex",
                            "issue_type": issue_type,
                            "matched_pattern": pattern,
                            "rendered_excerpt": compact_excerpt(rendered_tex, pattern),
                            "cleaned_excerpt": compact_excerpt(cleaned_tex, pattern),
                        }
                    )

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "concept_id",
                "title",
                "canonical_name",
                "source_field",
                "issue_type",
                "matched_pattern",
                "rendered_excerpt",
                "cleaned_excerpt",
            ],
        )
        writer.writeheader()
        writer.writerows(findings)

    conn.close()

    print(f"Checked {len(rows)} concepts.")
    print(f"Found {len(findings)} possible issues.")
    print(f"Wrote report to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()