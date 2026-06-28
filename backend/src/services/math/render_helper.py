# backend/src/utils/math/render_helpers.py

import re
import html as html_lib
import hashlib
from urllib.parse import quote


PSPICTURE_RE = re.compile(
    r"\\begin\{pspicture\}[\s\S]*?\\end\{pspicture\}",
    re.MULTILINE
)


def hash_pstricks_block(block: str) -> str:
    return hashlib.sha256(block.encode("utf-8")).hexdigest()[:16]


def extract_pstricks_blocks(tex: str) -> list[str]:
    return PSPICTURE_RE.findall(tex or "")


def extract_pstricks_hashes(tex: str) -> list[str]:
    return [
        hash_pstricks_block(block)
        for block in extract_pstricks_blocks(tex)
    ]


def get_svg_filename(svg_path: str) -> str | None:
    if not svg_path:
        return None

    clean_path = str(svg_path).replace("\\", "/").rstrip("/")
    return clean_path.split("/")[-1]


def make_diagram_img_tag(svg_filename: str) -> str:
    if not svg_filename:
        return '<div class="img-placeholder"><em>[Diagram path missing.]</em></div>'

    return (
        '<div class="math-diagram-wrap">'
        f'<img src="http://127.0.0.1:5000/api/math/diagrams/{svg_filename}" '
        'class="math-diagram" '
        'alt="Mathematical diagram">'
        '</div>'
    )


def render_pmlinkname(match: re.Match) -> str:
    link_text = match.group(1).strip()
    target_slug = match.group(2).strip()

    return (
        f'<a class="math-explicit-link" '
        f'href="concept.html?slug={quote(target_slug)}">'
        f'{html_lib.escape(link_text)}</a>'
    )


def render_prose_latex_to_html(tex: str) -> str:
    if not tex:
        return ""

    html = tex.replace("\r\n", "\n").replace("\r", "\n")

    html = re.sub(
        r"\\PMlinkname\{([^{}]+)\}\{([^{}]+)\}",
        render_pmlinkname,
        html,
        flags=re.DOTALL,
    )

    html = re.sub(
        r"\\PMlinkescapetext\{([^{}]*)\}",
        r'<span class="math-no-autolink">\1</span>',
        html,
        flags=re.DOTALL,
    )

    html = re.sub(
        r"\\textbf\{([^{}]*)\}",
        r"<strong>\1</strong>",
        html,
        flags=re.DOTALL,
    )

    html = re.sub(
        r"\\emph\{([^{}]*)\}",
        r"<em>\1</em>",
        html,
        flags=re.DOTALL,
    )

    html = re.sub(
        r"\{\\em\s+([^{}]*)\}",
        r"<em>\1</em>",
        html,
        flags=re.DOTALL,
    )

    html = re.sub(
        r"\{\\bf\s+([^{}]*)\}",
        r"<strong>\1</strong>",
        html,
        flags=re.DOTALL,
    )

    html = re.sub(r"\\\\[ \t]*(?:\n[ \t]*){2,}", "\n\n", html)
    html = re.sub(r"\\\\[ \t]*", "<br>\n", html)

    parts = re.split(r"\n\s*\n+", html.strip())
    paragraphs = []

    for part in parts:
        cleaned = part.strip()
        if cleaned:
            paragraphs.append(f"<p>{cleaned}</p>")

    return "\n\n".join(paragraphs)