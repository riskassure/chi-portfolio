import sys
import sqlite3
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[3]  # backend/src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import (
    DB_PATH,
    MATH_DIAGRAM_DIR,
    MATH_TEMP_DIR,
)

from database.math.pipeline.step2_build_diagrams import (
    convert_pstricks_to_svg,
    iter_standalone_pstree_blocks,
)

from services.math.render_helper import (
    hash_pstricks_block,
    make_diagram_img_tag,
    render_prose_latex_to_html,
)


def diagnose_standalone_pstrees(concept_id: int = 696):
    """
    Print standalone PSTree blocks detected for one concept.

    This is read-only:
    - no table rebuilds
    - no rendered_tex updates
    - no SVG conversion
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, slug, title, cleaned_tex
        FROM math_concepts
        WHERE id = ?;
    """, (concept_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        print(f"Concept {concept_id} was not found.")
        return

    concept_id, slug, title, cleaned_tex = row

    blocks = list(iter_standalone_pstree_blocks(cleaned_tex or ""))

    print("[PSTREE DIAGNOSTIC]")
    print(f"Concept ID: {concept_id}")
    print(f"Slug: {slug}")
    print(f"Title: {title}")
    print(f"Standalone PSTree blocks found: {len(blocks)}")
    print()

    for block_index, block in enumerate(blocks, start=1):
        print("=" * 72)
        print(f"Block {block_index}")
        print(f"Source positions: {block['start']}–{block['end']}")
        print("-" * 72)
        print(block["full_block"])
        print()


def diagnose_convert_standalone_pstree(
    concept_id: int = 696,
    block_number: int = 1,
):
    """
    Convert one extracted standalone PSTree block to SVG.

    This does not:
    - rebuild diagram tables
    - insert database rows
    - update rendered_tex
    """
    MATH_DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)
    MATH_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT cleaned_tex
        FROM math_concepts
        WHERE id = ?;
    """, (concept_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        print(f"Concept {concept_id} was not found.")
        return

    cleaned_tex = row[0] or ""
    blocks = list(iter_standalone_pstree_blocks(cleaned_tex))

    if not blocks:
        print(f"No standalone PSTree blocks found for concept {concept_id}.")
        return

    if block_number < 1 or block_number > len(blocks):
        print(
            f"Invalid block number {block_number}; "
            f"expected 1 through {len(blocks)}."
        )
        return

    block = blocks[block_number - 1]
    conversion_source = block["conversion_source"]
    source_hash = hash_pstricks_block(conversion_source)

    print("[PSTREE CONVERSION DIAGNOSTIC]")
    print(f"Concept ID: {concept_id}")
    print(f"Block: {block_number} of {len(blocks)}")
    print(f"Source hash: {source_hash}")
    print("-" * 72)
    print(conversion_source)
    print("-" * 72)

    svg_path, error_output, failure_stage = convert_pstricks_to_svg(
        conversion_source,
        source_hash,
    )

    if svg_path:
        print("✅ Conversion succeeded.")
        print(f"SVG path: {svg_path}")
        return

    print("❌ Conversion failed.")
    print(f"Failure stage: {failure_stage}")

    if error_output:
        print(error_output)


def diagnose_convert_all_standalone_pstrees(concept_id: int = 696):
    """
    Convert all extracted standalone PSTree blocks for one concept.

    This is still read-only with respect to the database:
    - no table rebuilds
    - no diagram row inserts
    - no rendered_tex updates
    """
    MATH_DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)
    MATH_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, slug, title, cleaned_tex
        FROM math_concepts
        WHERE id = ?;
    """, (concept_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        print(f"Concept {concept_id} was not found.")
        return

    concept_id, slug, title, cleaned_tex = row
    blocks = list(iter_standalone_pstree_blocks(cleaned_tex or ""))

    print("[PSTREE FULL CONVERSION DIAGNOSTIC]")
    print(f"Concept ID: {concept_id}")
    print(f"Slug: {slug}")
    print(f"Title: {title}")
    print(f"Standalone PSTree blocks found: {len(blocks)}")
    print()

    success_count = 0
    failure_count = 0

    for block_number, block in enumerate(blocks, start=1):
        conversion_source = block["conversion_source"]
        source_hash = hash_pstricks_block(conversion_source)

        print("=" * 72)
        print(f"Block {block_number} of {len(blocks)}")
        print(f"Source hash: {source_hash}")
        print("-" * 72)
        print(conversion_source)
        print("-" * 72)

        svg_path, error_output, failure_stage = convert_pstricks_to_svg(
            conversion_source,
            source_hash,
        )

        if svg_path:
            success_count += 1
            print("✅ Conversion succeeded.")
            print(f"SVG path: {svg_path}")
        else:
            failure_count += 1
            print("❌ Conversion failed.")
            print(f"Failure stage: {failure_stage}")

            if error_output:
                print(error_output)

        print()

    print("[PSTREE FULL CONVERSION DIAGNOSTIC COMPLETE]")
    print(f"Successful conversions: {success_count}")
    print(f"Failed conversions: {failure_count}")


def diagnose_standalone_pstree_replacement(concept_id: int = 696):
    """
    Preview replacement of standalone PSTree blocks with SVG image tags.

    This diagnostic:
    - reads cleaned_tex
    - replaces only parsed standalone PSTree blocks
    - preserves PSTree source inside verbatim environments
    - runs the normal prose renderer
    - writes a temporary HTML preview
    - does not update SQLite
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, slug, title, cleaned_tex
        FROM math_concepts
        WHERE id = ?;
    """, (concept_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        print(f"Concept {concept_id} was not found.")
        return

    concept_id, slug, title, cleaned_tex = row
    cleaned_tex = cleaned_tex or ""

    blocks = list(iter_standalone_pstree_blocks(cleaned_tex))

    print("[PSTREE REPLACEMENT PREVIEW]")
    print(f"Concept ID: {concept_id}")
    print(f"Slug: {slug}")
    print(f"Title: {title}")
    print(f"Standalone PSTree blocks found: {len(blocks)}")
    print()

    if not blocks:
        print("No standalone PSTree blocks were found.")
        return

    replacement_source = cleaned_tex
    replacement_count = 0
    missing_svg_count = 0

    # Work backward through the original source positions so earlier
    # replacements do not invalidate the positions of later blocks.
    for block_number, block in reversed(
        list(enumerate(blocks, start=1))
    ):
        conversion_source = block["conversion_source"]
        source_hash = hash_pstricks_block(conversion_source)
        svg_filename = f"{source_hash}.svg"
        svg_path = MATH_DIAGRAM_DIR / svg_filename

        if not svg_path.exists():
            missing_svg_count += 1
            print(
                f"⚠️ Block {block_number}: expected SVG does not exist: "
                f"{svg_path}"
            )
            continue

        replacement_html = make_diagram_img_tag(svg_filename)

        replacement_source = (
            replacement_source[:block["start"]]
            + replacement_html
            + replacement_source[block["end"]:]
        )

        replacement_count += 1

    remaining_standalone_blocks = list(
        iter_standalone_pstree_blocks(replacement_source)
    )

    rendered_preview = render_prose_latex_to_html(
        replacement_source
    )

    MATH_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    preview_path = (
        MATH_TEMP_DIR
        / f"pstree_replacement_preview_{concept_id}.html"
    )

    preview_path.write_text(
        rendered_preview,
        encoding="utf-8",
    )

    print()
    print("[PSTREE REPLACEMENT PREVIEW COMPLETE]")
    print(f"Replacement candidates: {len(blocks)}")
    print(f"Replacements made: {replacement_count}")
    print(f"Missing SVG files: {missing_svg_count}")
    print(
        "Standalone PSTree blocks remaining outside verbatim: "
        f"{len(remaining_standalone_blocks)}"
    )
    print(
        "Raw \\pstree occurrences remaining, including verbatim examples: "
        f"{replacement_source.count(chr(92) + 'pstree')}"
    )
    print(f"Preview written to: {preview_path}")


if __name__ == "__main__":
    # diagnose_standalone_pstrees(696)
    # diagnose_convert_standalone_pstree(696, 1)
    # diagnose_convert_all_standalone_pstrees(696)
    diagnose_standalone_pstree_replacement(696)