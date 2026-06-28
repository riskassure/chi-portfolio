# backend/src/utils/math/step2_build_diagrams.py

import sys
import re
import sqlite3
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime

SRC_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(SRC_DIR))

from config import DB_PATH, MATH_DIAGRAM_DIR, MATH_TEMP_DIR


PSPICTURE_RE = re.compile(
    r"\\begin\{pspicture\}[\s\S]*?\\end\{pspicture\}",
    re.MULTILINE
)


def hash_block(block: str) -> str:
    return hashlib.sha256(block.encode("utf-8")).hexdigest()[:16]


def wrap_pstricks_document(ps_block: str) -> str:
    return rf"""
\documentclass{{article}}
\usepackage{{pstricks}}
\usepackage{{pst-plot}}
\usepackage{{pst-node}}
\usepackage{{multido}}

% Common color aliases used by imported PlanetMath pspicture diagrams.
\definecolor{{lightblue}}{{RGB}}{{173,216,230}}
\definecolor{{lightgray}}{{RGB}}{{211,211,211}}

\pagestyle{{empty}}
\begin{{document}}
{ps_block}
\end{{document}}
"""


def combine_process_output(error: subprocess.CalledProcessError) -> str:
    """
    Preserve as much diagnostic information as possible.
    Some TeX tools write useful errors to stdout rather than stderr.
    """
    parts = []

    if error.stdout:
        parts.append("===== STDOUT =====")
        parts.append(error.stdout)

    if error.stderr:
        parts.append("===== STDERR =====")
        parts.append(error.stderr)

    return "\n".join(parts).strip()


def convert_pstricks_to_svg(ps_block: str, source_hash: str) -> tuple[Path | None, str, str | None]:
    """
    Attempts PSTricks -> DVI -> SVG conversion.

    Returns:
        (svg_path, "", None) on success
        (None, error_output, failure_stage) on failure
    """
    tex_path = MATH_TEMP_DIR / f"{source_hash}.tex"
    dvi_path = MATH_TEMP_DIR / f"{source_hash}.dvi"
    svg_path = MATH_DIAGRAM_DIR / f"{source_hash}.svg"

    if svg_path.exists():
        return svg_path, "", None

    tex_path.write_text(wrap_pstricks_document(ps_block), encoding="utf-8")

    try:
        subprocess.run(
            ["latex", "-interaction=nonstopmode", tex_path.name],
            cwd=MATH_TEMP_DIR,
            check=True,
            capture_output=True,
            text=True
        )

    except subprocess.CalledProcessError as e:
        error_output = combine_process_output(e)

        print(f"❌ Failed converting PSTricks block {source_hash} during latex step")
        print(error_output)

        return None, error_output, "latex"

    try:
        subprocess.run(
            ["dvisvgm", dvi_path.name, "-o", str(svg_path)],
            cwd=MATH_TEMP_DIR,
            check=True,
            capture_output=True,
            text=True
        )

    except subprocess.CalledProcessError as e:
        error_output = combine_process_output(e)

        print(f"❌ Failed converting PSTricks block {source_hash} during dvisvgm step")
        print(error_output)

        return None, error_output, "dvisvgm"

    return svg_path, "", None


def render_prose_latex_to_html(tex: str) -> str:
    if not tex:
        return ""

    html = tex.replace("\r\n", "\n").replace("\r", "\n")

    # PlanetMath/link escaping macros.
    html = re.sub(
        r"\\PMlinkescapetext\{([^{}]*)\}",
        r"\1",
        html,
        flags=re.DOTALL
    )

    # Common text formatting commands.
    html = re.sub(
        r"\\textbf\{([^{}]*)\}",
        r"<strong>\1</strong>",
        html,
        flags=re.DOTALL
    )

    html = re.sub(
        r"\\emph\{([^{}]*)\}",
        r"<em>\1</em>",
        html,
        flags=re.DOTALL
    )

    # Old TeX style emphasis: {\em text}
    html = re.sub(
        r"\{\\em\s+([^{}]*)\}",
        r"<em>\1</em>",
        html,
        flags=re.DOTALL
    )

    # Old TeX style bold: {\bf text}
    html = re.sub(
        r"\{\\bf\s+([^{}]*)\}",
        r"<strong>\1</strong>",
        html,
        flags=re.DOTALL
    )

    # IMPORTANT:
    # \\ followed by blank lines should become a paragraph break.
    html = re.sub(r"\\\\[ \t]*(?:\n[ \t]*){2,}", "\n\n", html)

    # Remaining \\ should become a line break.
    html = re.sub(r"\\\\[ \t]*", "<br>\n", html)

    # Preserve paragraph breaks.
    parts = re.split(r"\n\s*\n+", html.strip())
    paragraphs = []

    for part in parts:
        cleaned = part.strip()
        if cleaned:
            paragraphs.append(f"<p>{cleaned}</p>")

    return "\n\n".join(paragraphs)


def make_img_tag(svg_filename: str) -> str:
    return (
        f'<div class="math-diagram-wrap">'
        f'<img src="http://127.0.0.1:5000/api/math/diagrams/{svg_filename}" '
        f'class="math-diagram" '
        f'alt="Mathematical diagram">'
        f'</div>'
    )


def make_failed_diagram_placeholder(source_hash: str) -> str:
    return (
        '<div class="img-placeholder">'
        f'<em>[Diagram conversion failed — hash {source_hash}; see admin diagnostics]</em>'
        '</div>'
    )


def rebuild_diagram_tables(cursor):
    cursor.execute("DROP TABLE IF EXISTS math_concept_diagrams;")
    cursor.execute("""
        CREATE TABLE math_concept_diagrams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id INTEGER NOT NULL,
            block_index INTEGER NOT NULL,
            source_hash TEXT NOT NULL,
            source_tex TEXT NOT NULL,
            svg_path TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(concept_id)
                REFERENCES math_concepts(id)
                ON DELETE CASCADE,
            UNIQUE(concept_id, source_hash)
        );
    """)

    cursor.execute("DROP TABLE IF EXISTS math_concept_diagram_failures;")
    cursor.execute("""
        CREATE TABLE math_concept_diagram_failures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id INTEGER NOT NULL,
            block_index INTEGER NOT NULL,
            source_hash TEXT NOT NULL,
            source_tex TEXT NOT NULL,
            failure_stage TEXT,
            error_output TEXT,
            tex_temp_path TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(concept_id)
                REFERENCES math_concepts(id)
                ON DELETE CASCADE,
            UNIQUE(concept_id, source_hash)
        );
    """)


def build_math_diagrams():
    print("[STEP 2] Building PSTricks SVG diagrams...")

    MATH_DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)
    MATH_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    rebuild_diagram_tables(cursor)

    cursor.execute("""
        SELECT id, cleaned_tex
        FROM math_concepts
        ORDER BY id ASC;
    """)

    rows = cursor.fetchall()

    concept_count = 0
    diagram_count = 0
    failed_count = 0

    for concept_id, cleaned_tex in rows:
        if not cleaned_tex or "\\begin{pspicture}" not in cleaned_tex:
            rendered_tex = render_prose_latex_to_html(cleaned_tex)

            cursor.execute("""
                UPDATE math_concepts
                SET rendered_tex = ?
                WHERE id = ?;
            """, (rendered_tex, concept_id))

            continue

        concept_count += 1
        rendered_tex = cleaned_tex

        for block_index, ps_block in enumerate(PSPICTURE_RE.findall(cleaned_tex), start=1):
            source_hash = hash_block(ps_block)
            svg_path, error_output, failure_stage = convert_pstricks_to_svg(
                ps_block,
                source_hash
            )

            if svg_path:
                svg_filename = svg_path.name
                svg_url_path = f"/api/math/diagrams/{svg_filename}"

                cursor.execute("""
                    INSERT OR IGNORE INTO math_concept_diagrams (
                        concept_id,
                        block_index,
                        source_hash,
                        source_tex,
                        svg_path,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (
                    concept_id,
                    block_index,
                    source_hash,
                    ps_block,
                    svg_url_path,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                rendered_tex = rendered_tex.replace(
                    ps_block,
                    make_img_tag(svg_filename)
                )

                diagram_count += 1

            else:
                failed_count += 1
                tex_temp_path = str(MATH_TEMP_DIR / f"{source_hash}.tex")

                cursor.execute("""
                    INSERT OR REPLACE INTO math_concept_diagram_failures (
                        concept_id,
                        block_index,
                        source_hash,
                        source_tex,
                        failure_stage,
                        error_output,
                        tex_temp_path,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    concept_id,
                    block_index,
                    source_hash,
                    ps_block,
                    failure_stage,
                    error_output,
                    tex_temp_path,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                rendered_tex = rendered_tex.replace(
                    ps_block,
                    make_failed_diagram_placeholder(source_hash)
                )

                rendered_tex = render_prose_latex_to_html(rendered_tex)

                cursor.execute("""
                    UPDATE math_concepts
                    SET rendered_tex = ?
                    WHERE id = ?;
                """, (rendered_tex, concept_id))

    conn.commit()
    conn.close()

    print("✅ [STEP 2] Complete.")
    print(f"   Concepts with PSTricks: {concept_count}")
    print(f"   Diagrams converted: {diagram_count}")
    print(f"   Failed conversions: {failed_count}")


if __name__ == "__main__":
    build_math_diagrams()