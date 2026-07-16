# backend/src/utils/math/step2_build_diagrams.py

import sys
import re
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime

SRC_DIR = Path(__file__).resolve().parents[3]  # backend/src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DB_PATH, MATH_DIAGRAM_DIR, MATH_TEMP_DIR

from services.math.render_helper import (
    hash_pstricks_block,
    make_diagram_img_tag,
    render_prose_latex_to_html,
)


def wrap_pstricks_document(ps_block: str) -> str:
    return rf"""
\documentclass{{article}}
\usepackage{{pstricks}}
\usepackage{{pst-tree}}
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


PSTRICKS_BLOCK_WITH_SETUP_RE = re.compile(
    r"""
    (?P<setup>
        (?:
            [ \t\r\n]*
            \\psset\s*\{[^{}]*\}
        )*
    )
    [ \t\r\n]*
    (?P<picture>
        \\begin\{pspicture\}
        [\s\S]*?
        \\end\{pspicture\}
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def iter_pstricks_blocks_with_setup(cleaned_tex: str):
    """
    Yield PSTricks conversion blocks.

    If one or more \\psset{...} commands appear immediately before a
    pspicture block, include them in the conversion source and replacement
    source. This lets PSTricks scaling/setup affect the generated SVG and
    prevents the setup command from remaining as visible prose.
    """
    text = cleaned_tex or ""

    for match in PSTRICKS_BLOCK_WITH_SETUP_RE.finditer(text):
        full_block = match.group(0)
        setup = match.group("setup") or ""
        picture = match.group("picture") or ""

        conversion_source = f"{setup}\n{picture}".strip()

        yield {
            "full_block": full_block,
            "conversion_source": conversion_source,
            "picture": picture,
            "setup": setup,
        }


VERBATIM_ENVIRONMENT_RE = re.compile(
    r"""
    \\begin\{verbatim\*?\}
    [\s\S]*?
    \\end\{verbatim\*?\}
    """,
    re.IGNORECASE | re.VERBOSE,
)


def get_verbatim_ranges(text: str) -> list[tuple[int, int]]:
    """
    Return source ranges occupied by verbatim environments.

    Standalone PSTree examples shown as source code must not be converted
    into diagrams.
    """
    return [
        (match.start(), match.end())
        for match in VERBATIM_ENVIRONMENT_RE.finditer(text or "")
    ]


def index_is_inside_ranges(
    index: int,
    ranges: list[tuple[int, int]],
) -> bool:
    return any(start <= index < end for start, end in ranges)


def find_matching_delimiter(
    text: str,
    open_index: int,
    opening: str,
    closing: str,
) -> int:
    """
    Find the matching closing delimiter using balanced parsing.

    Escaped delimiters are ignored. This supports nested braces inside
    PSTree roots and child lists.
    """
    if (
        open_index < 0
        or open_index >= len(text)
        or text[open_index] != opening
    ):
        return -1

    depth = 0

    for index in range(open_index, len(text)):
        character = text[index]

        if character not in {opening, closing}:
            continue

        backslash_count = 0
        previous = index - 1

        while previous >= 0 and text[previous] == "\\":
            backslash_count += 1
            previous -= 1

        if backslash_count % 2 == 1:
            continue

        if character == opening:
            depth += 1
        else:
            depth -= 1

            if depth == 0:
                return index

    return -1


def skip_whitespace(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1

    return index


def parse_standalone_pstree_at(
    text: str,
    command_index: int,
) -> dict | None:
    """
    Parse one complete:

        \\pstree[optional settings]{root}{children}

    expression, including nested PSTree commands inside the children.
    """
    command = "\\pstree"

    if not text.startswith(command, command_index):
        return None

    cursor = command_index + len(command)
    cursor = skip_whitespace(text, cursor)

    options = ""

    if cursor < len(text) and text[cursor] == "[":
        options_end = find_matching_delimiter(
            text,
            cursor,
            "[",
            "]",
        )

        if options_end == -1:
            return None

        options = text[cursor:options_end + 1]
        cursor = skip_whitespace(text, options_end + 1)

    if cursor >= len(text) or text[cursor] != "{":
        return None

    root_end = find_matching_delimiter(
        text,
        cursor,
        "{",
        "}",
    )

    if root_end == -1:
        return None

    root = text[cursor:root_end + 1]
    cursor = skip_whitespace(text, root_end + 1)

    if cursor >= len(text) or text[cursor] != "{":
        return None

    children_end = find_matching_delimiter(
        text,
        cursor,
        "{",
        "}",
    )

    if children_end == -1:
        return None

    children = text[cursor:children_end + 1]
    full_block = text[command_index:children_end + 1]

    return {
        "start": command_index,
        "end": children_end + 1,
        "full_block": full_block,
        "conversion_source": full_block.strip(),
        "options": options,
        "root": root,
        "children": children,
    }


def iter_standalone_pstree_blocks(cleaned_tex: str):
    """
    Yield top-level standalone PSTree blocks outside verbatim environments.

    Advancing past the complete outer tree prevents nested \\pstree commands
    from being returned as separate diagrams.
    """
    text = cleaned_tex or ""
    verbatim_ranges = get_verbatim_ranges(text)

    cursor = 0

    while cursor < len(text):
        command_index = text.find("\\pstree", cursor)

        if command_index == -1:
            break

        if index_is_inside_ranges(command_index, verbatim_ranges):
            cursor = command_index + len("\\pstree")
            continue

        parsed = parse_standalone_pstree_at(
            text,
            command_index,
        )

        if parsed is None:
            cursor = command_index + len("\\pstree")
            continue

        yield parsed
        cursor = parsed["end"]


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

        for block_index, block_info in enumerate(iter_pstricks_blocks_with_setup(cleaned_tex), start=1):
            full_block = block_info["full_block"]
            conversion_source = block_info["conversion_source"]

            source_hash = hash_pstricks_block(conversion_source)
            svg_path, error_output, failure_stage = convert_pstricks_to_svg(
                conversion_source,
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
                    conversion_source,
                    svg_url_path,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                rendered_tex = rendered_tex.replace(
                    full_block,
                    make_diagram_img_tag(svg_filename),
                    1
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
                    conversion_source,
                    failure_stage,
                    error_output,
                    tex_temp_path,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                rendered_tex = rendered_tex.replace(
                    full_block,
                    make_failed_diagram_placeholder(source_hash),
                    1
                )

        rendered_tex = render_prose_latex_to_html(rendered_tex)

        cursor.execute("""
            UPDATE math_concepts
            SET rendered_tex = ?
            WHERE id = ?;
        """, (rendered_tex, concept_id))

    conn.commit()
    conn.close()

    print("[STEP 2] Complete.")
    print(f"   Concepts with PSTricks: {concept_count}")
    print(f"   Diagrams converted: {diagram_count}")
    print(f"   Failed conversions: {failed_count}")


if __name__ == "__main__":
    build_math_diagrams()