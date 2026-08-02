# backend/src/services/math/concept_render_service.py

import sqlite3

from services.math.render_helper import (
    extract_all_pstricks_diagram_blocks,
    get_svg_filename,
    make_diagram_img_tag,
    render_prose_latex_to_html,
)


def render_tex_reusing_existing_diagrams(
    concept_id: int,
    cleaned_tex: str,
    cursor,
) -> str:
    """
    Rebuild rendered_tex without running LaTeX or dvisvgm.

    Existing SVG records are reused for all supported PSTricks blocks:
      - pspicture, including preceding psset commands
      - standalone top-level pstree expressions

    Missing diagram records become placeholders rather than visible
    raw PSTricks source.
    """
    if not cleaned_tex:
        return ""

    diagram_blocks = extract_all_pstricks_diagram_blocks(
        cleaned_tex
    )

    if not diagram_blocks:
        return render_prose_latex_to_html(cleaned_tex)

    try:
        cursor.execute("""
            SELECT
                source_hash,
                svg_path
            FROM math_concept_diagrams
            WHERE concept_id = ?;
        """, (concept_id,))

        diagram_lookup = {
            row[0]: row[1]
            for row in cursor.fetchall()
        }

    except sqlite3.OperationalError:
        diagram_lookup = {}

    rendered_source = cleaned_tex

    for block in reversed(diagram_blocks):
        source_hash = block["source_hash"]
        svg_path = diagram_lookup.get(source_hash)

        if svg_path:
            svg_filename = get_svg_filename(svg_path)
            replacement = make_diagram_img_tag(svg_filename)
        else:
            replacement = (
                '<div class="img-placeholder">'
                '<em>[Diagram unavailable.]</em>'
                '</div>'
            )

        rendered_source = (
            rendered_source[:block["start"]]
            + replacement
            + rendered_source[block["end"]:]
        )

    return render_prose_latex_to_html(rendered_source)
