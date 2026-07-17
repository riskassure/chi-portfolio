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
    extract_all_pstricks_diagram_blocks,
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


def ensure_diagram_tables_exist(cursor):
    """
    Create the diagram tables only if they do not already exist.

    Unlike rebuild_diagram_tables(), this is safe for additive or
    single-concept diagram processing because it preserves all existing rows.
    """
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS math_concept_diagrams (
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS math_concept_diagram_failures (
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
        blocks = extract_all_pstricks_diagram_blocks(cleaned_tex)
            
        if not blocks:
            rendered_tex = render_prose_latex_to_html(cleaned_tex)

            cursor.execute("""
                UPDATE math_concepts
                SET rendered_tex = ?
                WHERE id = ?;
            """, (rendered_tex, concept_id))

            continue

        concept_count += 1
        rendered_tex = cleaned_tex

        for block_index, block_info in enumerate(
            blocks,
            start=1,
        ):
            full_block = block_info["full_block"]
            conversion_source = block_info["conversion_source"]

            source_hash = block_info["source_hash"]
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


def process_pstricks_diagrams_in_transaction(
    cursor,
    concept_id: int,
    cleaned_tex: str,
) -> dict:
    """
    Synchronize all supported PSTricks diagrams for one concept using
    the caller's existing database transaction.

    This function does not open or close a database connection and does
    not commit or roll back.

    Returns:
        {
            "rendered_tex": str,
            "block_count": int,
            "success_count": int,
            "failure_count": int,
        }
    """
    cleaned_tex = cleaned_tex or ""

    MATH_DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)
    MATH_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    ensure_diagram_tables_exist(cursor)

    blocks = extract_all_pstricks_diagram_blocks(cleaned_tex)

    current_hashes = [
        block["source_hash"]
        for block in blocks
    ]

    # Remove diagram records that no longer correspond to source blocks.
    if current_hashes:
        placeholders = ", ".join("?" for _ in current_hashes)

        cursor.execute(f"""
            DELETE FROM math_concept_diagrams
            WHERE concept_id = ?
              AND source_hash NOT IN ({placeholders});
        """, (
            concept_id,
            *current_hashes,
        ))

        cursor.execute(f"""
            DELETE FROM math_concept_diagram_failures
            WHERE concept_id = ?
              AND source_hash NOT IN ({placeholders});
        """, (
            concept_id,
            *current_hashes,
        ))

    else:
        cursor.execute("""
            DELETE FROM math_concept_diagrams
            WHERE concept_id = ?;
        """, (concept_id,))

        cursor.execute("""
            DELETE FROM math_concept_diagram_failures
            WHERE concept_id = ?;
        """, (concept_id,))

        return {
            "rendered_tex": render_prose_latex_to_html(cleaned_tex),
            "block_count": 0,
            "success_count": 0,
            "failure_count": 0,
        }

    rendered_source = cleaned_tex
    success_count = 0
    failure_count = 0
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Work backward so source offsets remain valid during replacement.
    for block_index, block in reversed(
        list(enumerate(blocks, start=1))
    ):
        conversion_source = block["conversion_source"]
        source_hash = block["source_hash"]

        svg_path, error_output, failure_stage = (
            convert_pstricks_to_svg(
                conversion_source,
                source_hash,
            )
        )

        if svg_path:
            svg_filename = svg_path.name
            svg_url_path = (
                f"/api/math/diagrams/{svg_filename}"
            )

            cursor.execute("""
                INSERT INTO math_concept_diagrams (
                    concept_id,
                    block_index,
                    source_hash,
                    source_tex,
                    svg_path,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(concept_id, source_hash)
                DO UPDATE SET
                    block_index = excluded.block_index,
                    source_tex = excluded.source_tex,
                    svg_path = excluded.svg_path,
                    created_at = excluded.created_at;
            """, (
                concept_id,
                block_index,
                source_hash,
                conversion_source,
                svg_url_path,
                timestamp,
            ))

            # A successful retry supersedes any previous failure.
            cursor.execute("""
                DELETE FROM math_concept_diagram_failures
                WHERE concept_id = ?
                  AND source_hash = ?;
            """, (
                concept_id,
                source_hash,
            ))

            replacement_html = make_diagram_img_tag(
                svg_filename
            )

            success_count += 1

        else:
            tex_temp_path = str(
                MATH_TEMP_DIR / f"{source_hash}.tex"
            )

            cursor.execute("""
                INSERT INTO math_concept_diagram_failures (
                    concept_id,
                    block_index,
                    source_hash,
                    source_tex,
                    failure_stage,
                    error_output,
                    tex_temp_path,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(concept_id, source_hash)
                DO UPDATE SET
                    block_index = excluded.block_index,
                    source_tex = excluded.source_tex,
                    failure_stage = excluded.failure_stage,
                    error_output = excluded.error_output,
                    tex_temp_path = excluded.tex_temp_path,
                    created_at = excluded.created_at;
            """, (
                concept_id,
                block_index,
                source_hash,
                conversion_source,
                failure_stage,
                error_output,
                tex_temp_path,
                timestamp,
            ))

            # A failed rebuild must not leave an obsolete success record.
            cursor.execute("""
                DELETE FROM math_concept_diagrams
                WHERE concept_id = ?
                  AND source_hash = ?;
            """, (
                concept_id,
                source_hash,
            ))

            replacement_html = make_failed_diagram_placeholder(
                source_hash
            )

            failure_count += 1

        rendered_source = (
            rendered_source[:block["start"]]
            + replacement_html
            + rendered_source[block["end"]:]
        )

    return {
        "rendered_tex": render_prose_latex_to_html(
            rendered_source
        ),
        "block_count": len(blocks),
        "success_count": success_count,
        "failure_count": failure_count,
    }


def add_pstricks_diagrams_for_concept(concept_id: int):
    """
    Add supported PSTricks diagrams for one concept without rebuilding
    or clearing existing diagram tables.
    """
    print(f"[PSTRICKS ADDITIVE] Processing concept {concept_id}...")

    MATH_DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)
    MATH_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    ensure_diagram_tables_exist(cursor)

    cursor.execute("""
        SELECT id, slug, title, cleaned_tex
        FROM math_concepts
        WHERE id = ?;
    """, (concept_id,))

    row = cursor.fetchone()

    if row is None:
        conn.close()
        print(f"Concept {concept_id} was not found.")
        return

    concept_id, slug, title, cleaned_tex = row
    cleaned_tex = cleaned_tex or ""

    blocks = extract_all_pstricks_diagram_blocks(cleaned_tex)

    print(f"Slug: {slug}")
    print(f"Title: {title}")
    print(f"Supported PSTricks blocks found: {len(blocks)}")

    if not blocks:
        conn.close()
        print("No supported PSTricks blocks found; nothing changed.")
        return

    rendered_source = cleaned_tex
    success_count = 0
    failure_count = 0

    for block_index, block in reversed(
        list(enumerate(blocks, start=1))
    ):
        conversion_source = block["conversion_source"]
        source_hash = block["source_hash"]

        svg_path, error_output, failure_stage = convert_pstricks_to_svg(
            conversion_source,
            source_hash,
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
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ))

            replacement_html = make_diagram_img_tag(svg_filename)

            rendered_source = (
                rendered_source[:block["start"]]
                + replacement_html
                + rendered_source[block["end"]:]
            )

            success_count += 1

        else:
            tex_temp_path = str(
                MATH_TEMP_DIR / f"{source_hash}.tex"
            )

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
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ))

            replacement_html = make_failed_diagram_placeholder(
                source_hash
            )

            rendered_source = (
                rendered_source[:block["start"]]
                + replacement_html
                + rendered_source[block["end"]:]
            )

            failure_count += 1

    rendered_tex = render_prose_latex_to_html(rendered_source)

    cursor.execute("""
        UPDATE math_concepts
        SET rendered_tex = ?
        WHERE id = ?;
    """, (rendered_tex, concept_id))

    conn.commit()
    conn.close()

    print("[PSTRICKS ADDITIVE] Complete.")
    print(f"Successful diagrams: {success_count}")
    print(f"Failed diagrams: {failure_count}")


if __name__ == "__main__":
    build_math_diagrams()