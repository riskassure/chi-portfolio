# backend/src/services/math/autolink_service.py

import re
from urllib.parse import quote, unquote


def resolve_explicit_math_link_targets(tex_content, db_cursor):
    """
    Convert explicit PlanetMath links whose href target is a legacy
    canonical_name into links using the concept's stored CMS slug.

    If the target concept does not exist locally, keep only the visible
    link text and remove the broken anchor.
    """
    if not tex_content or "math-explicit-link" not in tex_content:
        return tex_content or ""

    db_cursor.execute("""
        SELECT canonical_name, slug
        FROM math_concepts
        WHERE canonical_name IS NOT NULL
          AND slug IS NOT NULL;
    """)

    canonical_to_slug = {
        row[0].strip().casefold(): row[1].strip()
        for row in db_cursor.fetchall()
        if row[0] and row[1]
    }

    pattern = re.compile(
        r'<a\b[^>]*\bclass="[^"]*\bmath-explicit-link\b[^"]*"'
        r'[^>]*\bhref="concept\.html\?slug=([^"]+)"[^>]*>'
        r'([\s\S]*?)'
        r'</a>',
        flags=re.IGNORECASE,
    )

    def replace_target(match):
        legacy_target = unquote(match.group(1)).strip()
        link_text = match.group(2)

        resolved_slug = canonical_to_slug.get(
            legacy_target.casefold()
        )

        if not resolved_slug:
            return link_text

        return (
            '<a class="math-explicit-link math-autolink" '
            f'href="concept.html?slug={quote(resolved_slug)}">'
            f'{link_text}</a>'
        )

    return pattern.sub(replace_target, tex_content)


def apply_math_autolinker(concept_id, tex_content, db_cursor):
    """
    Tokenizes LaTeX content to safely apply anchor tags ONLY within standard
    descriptive text blocks, leaving math mode and structural layouts untouched.
    Uses an absolute positional index scanner to avoid string offset drift.
    """
    if not tex_content:
        return ""

    # 1. Gather this specific document's database link exclusions.
    db_cursor.execute("""
        SELECT word
        FROM math_link_exclusions
        WHERE concept_id = ?;
    """, (concept_id,))

    local_exclusions = {
        row[0].lower().strip()
        for row in db_cursor.fetchall()
    }

    # 2. Parse inline explicit macro overrides.
    escaped_macros = re.findall(
        r"\\PMlinkescapeword\{([^}]+)\}",
        tex_content
    )

    for word in escaped_macros:
        local_exclusions.add(word.lower().strip())

    # Clean macro tags out so they do not corrupt presentation layout.
    tex_content = re.sub(
        r"\\PMlinkescape(?:word|phrase)\{[^}]+\}",
        "",
        tex_content
    )

    tex_content = resolve_explicit_math_link_targets(
        tex_content,
        db_cursor
    )

    # 3. Harvest all available global cross-linking destination keys.
    targets = {}

    # Base concept titles.
    db_cursor.execute("""
        SELECT id, title, slug
        FROM math_concepts
        WHERE id != ?;
    """, (concept_id,))

    for row in db_cursor.fetchall():
        if row[1] and row[2]:
            targets[row[1].lower().strip()] = row[2]

    # Platform synonyms.
    db_cursor.execute("""
        SELECT ms.synonym_text, mc.slug
        FROM math_synonyms ms
        JOIN math_concepts mc
            ON ms.concept_id = mc.id
        WHERE ms.concept_id != ?;
    """, (concept_id,))

    for row in db_cursor.fetchall():
        if row[0] and row[1]:
            targets[row[0].lower().strip()] = row[1]

    # Platform defined terms.
    db_cursor.execute("""
        SELECT md.defined_term, mc.slug
        FROM math_definitions md
        JOIN math_concepts mc
            ON md.concept_id = mc.id
        WHERE md.concept_id != ?;
    """, (concept_id,))

    for row in db_cursor.fetchall():
        if row[0] and row[1]:
            targets[row[0].lower().strip()] = row[1]

    # Filter out target dictionary terms that match exclusions.
    active_targets = {
        k: v
        for k, v in targets.items()
        if k not in local_exclusions and len(k) > 2
    }

    if not active_targets:
        return tex_content

    sorted_phrases = sorted(
        active_targets.keys(),
        key=len,
        reverse=True
    )

    master_pattern_str = (
        r"\b("
        + "|".join(re.escape(phrase) for phrase in sorted_phrases)
        + r")\b"
    )

    master_regex = re.compile(master_pattern_str, re.IGNORECASE)

    # 4. Split rendered content into protected math/HTML tokens
    # versus ordinary prose where autolinking is allowed.
    token_pattern = re.compile(
        r"("
        r'<span\b[^>]*class=["\'][^"\']*\bmath-no-autolink\b[^"\']*["\'][^>]*>.*?</span>'
        r"|<a\b[^>]*>.*?</a>"
        r"|\$\$.*?\$\$"
        r"|\\\[.*?\\\]"
        r"|\\\(.*?\\\)"
        r"|\$.*?\$"
        r"|\\begin\{[^{}]+\}.*?\\end\{[^{}]+\}"
        r"|<!--.*?-->"
        r"|<[^>]+>"
        r"|\\[A-Za-z@]+\*?"
        r")",
        re.DOTALL | re.IGNORECASE
    )

    chunks = token_pattern.split(tex_content)
    processed_chunks = []

    for chunk in chunks:
        if (
            chunk.startswith("$")
            or chunk.startswith("\\")
            or chunk.lower().startswith('<span class="math-no-autolink"')
            or chunk.lower().startswith("<a")
        ):
            processed_chunks.append(chunk)
            continue

        cursor_pos = 0
        built_chunk = ""

        for match in master_regex.finditer(chunk):
            start, end = match.start(), match.end()
            matched_text = match.group(1)
            matched_lower = matched_text.lower().strip()
            slug_target = active_targets.get(matched_lower)

            built_chunk += chunk[cursor_pos:start]
            cursor_pos = end

            if not slug_target:
                built_chunk += matched_text
                continue

            # Avoid injecting inside HTML tags.
            last_open_bracket = built_chunk.rfind("<")
            last_close_bracket = built_chunk.rfind(">")

            if last_open_bracket > last_close_bracket:
                built_chunk += matched_text
                continue

            # Avoid nesting links.
            last_open_a = built_chunk.rfind("<a")
            last_close_a = built_chunk.rfind("</a>")

            if last_open_a > last_close_a:
                built_chunk += matched_text
                continue

            built_chunk += (
                f'<a class="math-autolink" '
                f'href="concept.html?slug={slug_target}">'
                f"{matched_text}</a>"
            )

        built_chunk += chunk[cursor_pos:]
        processed_chunks.append(built_chunk)

    return "".join(processed_chunks)
