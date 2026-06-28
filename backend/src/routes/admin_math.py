# backend/src/routes/admin_math.py

import sqlite3
import sys
import re
from pathlib import Path
from collections import Counter
from datetime import datetime
from flask import Blueprint, jsonify, request, send_from_directory

SRC_DIR = Path(__file__).resolve().parents[1]  # backend/src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DB_PATH, MATH_DIAGRAM_DIR

from services.math.render_helper import (
    PSPICTURE_RE,
    hash_pstricks_block,
    extract_pstricks_blocks,
    extract_pstricks_hashes,
    get_svg_filename,
    make_diagram_img_tag,
    render_prose_latex_to_html,
)

math_bp = Blueprint("math_bp", __name__)


@math_bp.route("/api/math/diagrams/<path:filename>", methods=["GET"])
def serve_math_diagram(filename):
    return send_from_directory(MATH_DIAGRAM_DIR, filename)


def generate_slug(canonical_name):
    if not canonical_name:
        return None

    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1-\2", canonical_name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s1)

    return (
        s2.lower()
        .replace("_", "-")
        .replace("--", "-")
    )


def escape_like_term(term):
    """Escape SQLite LIKE wildcards so user text is treated literally."""
    return (
        term
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def parse_csv_list(value):
    if not value:
        return []

    return [
        x.strip()
        for x in value.split(",")
        if x and x.strip()
    ]


def normalize_tex_for_save_compare(tex: str) -> str:
    """
    Normalize enough to avoid false positives from trivial outer whitespace,
    but do not aggressively rewrite the TeX.
    """
    return (tex or "").strip()


def compare_pstricks_hashes(old_tex: str, new_tex: str) -> dict:
    old_hashes = extract_pstricks_hashes(old_tex)
    new_hashes = extract_pstricks_hashes(new_tex)

    old_counter = Counter(old_hashes)
    new_counter = Counter(new_hashes)

    added_hashes = list((new_counter - old_counter).elements())
    removed_hashes = list((old_counter - new_counter).elements())
    unchanged_hashes = list((old_counter & new_counter).elements())

    return {
        "old_count": len(old_hashes),
        "new_count": len(new_hashes),
        "unchanged_count": len(unchanged_hashes),
        "added_count": len(added_hashes),
        "removed_count": len(removed_hashes),
        "old_hashes": old_hashes,
        "new_hashes": new_hashes,
        "added_hashes": added_hashes,
        "removed_hashes": removed_hashes,
        "pstricks_changed": old_counter != new_counter
    }


def determine_smart_save_mode(old_tex: str, new_tex: str) -> dict:
    old_clean = normalize_tex_for_save_compare(old_tex)
    new_clean = normalize_tex_for_save_compare(new_tex)

    tex_changed = old_clean != new_clean
    diagram_compare = compare_pstricks_hashes(old_clean, new_clean)

    if not tex_changed:
        return {
            "save_mode": "metadata_only",
            "tex_changed": False,
            "pstricks_changed": False,
            "diagram_compare": diagram_compare,
            "message": "Saved metadata only. TeX source was unchanged."
        }

    if not diagram_compare["pstricks_changed"]:
        return {
            "save_mode": "text_render_only",
            "tex_changed": True,
            "pstricks_changed": False,
            "diagram_compare": diagram_compare,
            "message": "Saved TeX changes. PSTricks diagram blocks were unchanged."
        }

    return {
        "save_mode": "diagram_rebuild_needed",
        "tex_changed": True,
        "pstricks_changed": True,
        "diagram_compare": diagram_compare,
        "message": (
            "Saved TeX changes. PSTricks diagram blocks changed; "
            "diagram rebuild logic will handle this in the next Phase C step."
        )
    }


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
        r"\\PMlinkescapeword\{[^}]+\}",
        "",
        tex_content
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

    # 4. Split TeX into safe text blocks vs sensitive math/command blocks.
    token_pattern = re.compile(
        r"("
        r'<span class="math-no-autolink">.*?</span>'
        r"|<a\b.*?</a>"
        r"|\$\$.*?\$\$"
        r"|\$.*?\$"
        r"|\\begin\{.*?\}.*?\\end\{.*?\}"
        r"|\\\w+"
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


def render_tex_reusing_existing_diagrams(concept_id: int, cleaned_tex: str, cursor) -> str:
    """
    Rebuild rendered_tex without running LaTeX/dvisvgm.

    For ordinary TeX:
        render prose using the shared render helper.

    For unchanged PSTricks blocks:
        replace each pspicture block with its existing SVG image tag,
        then render prose using the shared render helper.

    For missing diagram records:
        leave a placeholder rather than showing raw PSTricks.
    """
    if not cleaned_tex:
        return ""

    ps_blocks = extract_pstricks_blocks(cleaned_tex)

    if not ps_blocks:
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

    rendered_tex = cleaned_tex

    for ps_block in ps_blocks:
        source_hash = hash_pstricks_block(ps_block)
        svg_path = diagram_lookup.get(source_hash)

        if svg_path:
            svg_filename = get_svg_filename(svg_path)
            replacement = make_diagram_img_tag(svg_filename)
        else:
            replacement = '<div class="img-placeholder"><em>[Diagram unavailable.]</em></div>'

        rendered_tex = rendered_tex.replace(ps_block, replacement, 1)

    return render_prose_latex_to_html(rendered_tex)


@math_bp.route("/api/math/classifications", methods=["GET", "OPTIONS"])
def get_active_classifications():
    """Public lookup route supplying active MSC classifications for directory hubs."""
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    conn = None

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT
                mcl.code,
                mcl.text
            FROM math_classifications mcl
            JOIN math_concept_classifications mcc
                ON mcl.id = mcc.classification_id
            ORDER BY mcl.code ASC;
        """)

        categories = [
            dict(row)
            for row in cursor.fetchall()
        ]

        return jsonify({
            "status": "success",
            "count": len(categories),
            "data": categories
        }), 200

    except sqlite3.Error as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

    finally:
        if conn:
            conn.close()


@math_bp.route("/api/admin/math/classifications/search", methods=["GET", "OPTIONS"])
def search_classifications_typeahead():
    """Admin typeahead lookup for MSC classifications."""
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    query_param = request.args.get("q", default="", type=str).strip()

    if len(query_param) < 2:
        return jsonify({
            "status": "success",
            "data": []
        }), 200

    conn = None

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT code, text
            FROM math_classifications
            WHERE code LIKE ?
               OR text LIKE ?
            ORDER BY code ASC
            LIMIT 15;
        """, (
            f"%{query_param}%",
            f"%{query_param}%"
        ))

        results = [
            {"code": r["code"], "text": r["text"]}
            for r in cursor.fetchall()
        ]

        return jsonify({
            "status": "success",
            "data": results
        }), 200

    except sqlite3.Error as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

    finally:
        if conn:
            conn.close()


@math_bp.route("/api/admin/math/concepts/search", methods=["GET"])
def search_admin_math_concepts():
    from app import admin_required

    @admin_required
    def process_search():
        q = request.args.get("q", default="", type=str).strip()
        exclude_id = request.args.get("exclude_id", default=None, type=int)

        if len(q) < 2:
            return jsonify({
                "status": "success",
                "data": []
            }), 200

        like_q = f"%{q}%"
        conn = None

        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DISTINCT
                    mc.id,
                    mc.title,
                    mc.canonical_name,
                    mc.slug
                FROM math_concepts mc
                LEFT JOIN math_synonyms ms
                    ON ms.concept_id = mc.id
                LEFT JOIN math_definitions md
                    ON md.concept_id = mc.id
                WHERE
                    (? IS NULL OR mc.id != ?)
                    AND (
                        mc.title LIKE ?
                        OR mc.canonical_name LIKE ?
                        OR mc.slug LIKE ?
                        OR ms.synonym_text LIKE ?
                        OR md.defined_term LIKE ?
                    )
                ORDER BY mc.title ASC
                LIMIT 20;
            """, (
                exclude_id,
                exclude_id,
                like_q,
                like_q,
                like_q,
                like_q,
                like_q
            ))

            rows = [dict(row) for row in cursor.fetchall()]

            return jsonify({
                "status": "success",
                "data": rows
            }), 200

        except sqlite3.Error as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

        finally:
            if conn:
                conn.close()

    return process_search()


@math_bp.route("/api/admin/math/types", methods=["GET", "OPTIONS"])
def get_admin_math_types():
    """Protected admin lookup route for editor type suggestions."""
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    from app import admin_required

    @admin_required
    def process_lookup():
        conn = None

        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT type_name
                FROM math_types
                ORDER BY type_name ASC;
            """)

            results = [
                r["type_name"]
                for r in cursor.fetchall()
            ]

            return jsonify({
                "status": "success",
                "count": len(results),
                "data": results
            }), 200

        except sqlite3.Error as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

        finally:
            if conn:
                conn.close()

    return process_lookup()


@math_bp.route("/api/math/search", methods=["GET", "OPTIONS"])
def search_math_library():
    """
    Unified public search route for concepts, synonyms, defined terms,
    and MSC classifications.

    Concept-like results route to:
        concept.html?slug=...

    Classification results route to:
        list.html?classification=...
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    query_param = request.args.get("q", default="", type=str).strip()

    if len(query_param) < 2:
        return jsonify({
            "status": "success",
            "query": query_param,
            "count": 0,
            "data": []
        }), 200

    def clamp_int(value, default, min_value=1, max_value=200):
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = default

        return max(min_value, min(parsed, max_value))

    explicit_family_limits = (
        "concept_limit" in request.args
        or "classification_limit" in request.args
    )

    overall_limit = clamp_int(
        request.args.get("limit"),
        default=20,
        max_value=200
    )

    if explicit_family_limits:
        concept_limit = clamp_int(
            request.args.get("concept_limit"),
            default=overall_limit,
            max_value=200
        )
        classification_limit = clamp_int(
            request.args.get("classification_limit"),
            default=overall_limit,
            max_value=200
        )
    else:
        concept_limit = overall_limit
        classification_limit = overall_limit

    safe_query = escape_like_term(query_param)
    like_param = f"%{safe_query}%"
    prefix_param = f"{safe_query}%"

    concept_results = []
    classification_results = []
    seen_concept_slugs = set()
    seen_class_codes = set()

    def append_concept_result(row, match_type, matched_text=None):
        slug = row["slug"]

        if not slug or slug in seen_concept_slugs:
            return

        seen_concept_slugs.add(slug)

        concept_results.append({
            "kind": "concept",
            "match_type": match_type,
            "id": row["id"],
            "title": row["title"],
            "label": row["title"],
            "slug": slug,
            "matched_text": matched_text,
            "classification_codes": parse_csv_list(row["classification_codes"]),
        })

    conn = None

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. Concept title / slug / canonical name matches.
        cursor.execute("""
            SELECT
                mc.id,
                mc.title,
                mc.slug,
                GROUP_CONCAT(DISTINCT mcl.code) AS classification_codes
            FROM math_concepts mc
            LEFT JOIN math_concept_classifications mcc
                ON mc.id = mcc.concept_id
            LEFT JOIN math_classifications mcl
                ON mcc.classification_id = mcl.id
            WHERE mc.title LIKE ? ESCAPE '\\'
               OR mc.slug LIKE ? ESCAPE '\\'
               OR mc.canonical_name LIKE ? ESCAPE '\\'
            GROUP BY mc.id
            ORDER BY
                CASE
                    WHEN LOWER(mc.title) = LOWER(?) THEN 0
                    WHEN LOWER(mc.title) LIKE LOWER(?) ESCAPE '\\' THEN 1
                    ELSE 2
                END,
                mc.title ASC
            LIMIT ?;
        """, (
            like_param,
            like_param,
            like_param,
            query_param,
            prefix_param,
            concept_limit
        ))

        for row in cursor.fetchall():
            append_concept_result(row, "title")

        remaining_concept_slots = max(
            0,
            concept_limit - len(seen_concept_slugs)
        )

        # 2. Synonym matches.
        if remaining_concept_slots > 0:
            cursor.execute("""
                SELECT
                    mc.id,
                    mc.title,
                    mc.slug,
                    ms.synonym_text AS matched_text,
                    GROUP_CONCAT(DISTINCT mcl.code) AS classification_codes
                FROM math_synonyms ms
                JOIN math_concepts mc
                    ON ms.concept_id = mc.id
                LEFT JOIN math_concept_classifications mcc
                    ON mc.id = mcc.concept_id
                LEFT JOIN math_classifications mcl
                    ON mcc.classification_id = mcl.id
                WHERE ms.synonym_text LIKE ? ESCAPE '\\'
                GROUP BY ms.id
                ORDER BY
                    CASE
                        WHEN LOWER(ms.synonym_text) = LOWER(?) THEN 0
                        WHEN LOWER(ms.synonym_text) LIKE LOWER(?) ESCAPE '\\' THEN 1
                        ELSE 2
                    END,
                    ms.synonym_text ASC
                LIMIT ?;
            """, (
                like_param,
                query_param,
                prefix_param,
                remaining_concept_slots
            ))

            for row in cursor.fetchall():
                append_concept_result(row, "synonym", row["matched_text"])

        remaining_concept_slots = max(
            0,
            concept_limit - len(seen_concept_slugs)
        )

        # 3. Defined-term matches.
        if remaining_concept_slots > 0:
            cursor.execute("""
                SELECT
                    mc.id,
                    mc.title,
                    mc.slug,
                    md.defined_term AS matched_text,
                    GROUP_CONCAT(DISTINCT mcl.code) AS classification_codes
                FROM math_definitions md
                JOIN math_concepts mc
                    ON md.concept_id = mc.id
                LEFT JOIN math_concept_classifications mcc
                    ON mc.id = mcc.concept_id
                LEFT JOIN math_classifications mcl
                    ON mcc.classification_id = mcl.id
                WHERE md.defined_term LIKE ? ESCAPE '\\'
                GROUP BY md.id
                ORDER BY
                    CASE
                        WHEN LOWER(md.defined_term) = LOWER(?) THEN 0
                        WHEN LOWER(md.defined_term) LIKE LOWER(?) ESCAPE '\\' THEN 1
                        ELSE 2
                    END,
                    md.defined_term ASC
                LIMIT ?;
            """, (
                like_param,
                query_param,
                prefix_param,
                remaining_concept_slots
            ))

            for row in cursor.fetchall():
                append_concept_result(row, "definition", row["matched_text"])

        # 4. MSC classification matches.
        cursor.execute("""
            SELECT
                code,
                text,
                description
            FROM math_classifications
            WHERE code LIKE ? ESCAPE '\\'
               OR text LIKE ? ESCAPE '\\'
               OR COALESCE(description, '') LIKE ? ESCAPE '\\'
            ORDER BY
                CASE
                    WHEN LOWER(code) = LOWER(?) THEN 0
                    WHEN LOWER(code) LIKE LOWER(?) ESCAPE '\\' THEN 1
                    WHEN LOWER(text) LIKE LOWER(?) ESCAPE '\\' THEN 2
                    ELSE 3
                END,
                code ASC
            LIMIT ?;
        """, (
            like_param,
            like_param,
            like_param,
            query_param,
            prefix_param,
            prefix_param,
            classification_limit
        ))

        for row in cursor.fetchall():
            code = row["code"]

            if not code or code in seen_class_codes:
                continue

            seen_class_codes.add(code)

            classification_results.append({
                "kind": "classification",
                "match_type": "classification",
                "code": code,
                "label": f"{code} — {row['text']}",
                "text": row["text"],
                "description": row["description"],
            })

        if explicit_family_limits:
            results = concept_results + classification_results
        else:
            # Balanced quick mode.
            if concept_results and classification_results and overall_limit >= 4:
                reserved_class_slots = min(
                    len(classification_results),
                    max(1, overall_limit // 4)
                )
                concept_take = min(
                    len(concept_results),
                    overall_limit - reserved_class_slots
                )
                class_take = min(
                    len(classification_results),
                    overall_limit - concept_take
                )
                results = (
                    concept_results[:concept_take]
                    + classification_results[:class_take]
                )
            else:
                results = (
                    concept_results
                    + classification_results
                )[:overall_limit]

        return jsonify({
            "status": "success",
            "query": query_param,
            "count": len(results),
            "data": results,
            "meta": {
                "concept_candidate_count": len(concept_results),
                "classification_candidate_count": len(classification_results),
                "overall_limit": overall_limit,
                "concept_limit": concept_limit,
                "classification_limit": classification_limit,
            }
        }), 200

    except sqlite3.Error as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

    finally:
        if conn:
            conn.close()


@math_bp.route("/api/math/concepts", methods=["GET", "OPTIONS"])
def get_math_concepts():
    """
    Public read route for catalog/list views.

    This route still supports ?classification=CODE.
    The ?q= behavior remains for backward compatibility, but the main search UI
    should use /api/math/search.
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    conn = None

    try:
        class_filter = request.args.get("classification", default=None, type=str)
        search_query = request.args.get("q", default=None, type=str)

        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query_base = """
            SELECT
                mc.id,
                mc.title,
                mc.slug,
                mc.owner,
                mc.created_at,
                mc.updated_at,
                mc.is_cleaned,
                GROUP_CONCAT(DISTINCT mt.type_name) AS type_names,
                GROUP_CONCAT(DISTINCT mcl.code) AS classification_codes
            FROM math_concepts mc
            LEFT JOIN math_concept_types mct
                ON mc.id = mct.concept_id
            LEFT JOIN math_types mt
                ON mct.type_id = mt.id
            LEFT JOIN math_concept_classifications mcc
                ON mc.id = mcc.concept_id
            LEFT JOIN math_classifications mcl
                ON mcc.classification_id = mcl.id
        """

        conditions = []
        params = []

        if class_filter:
            conditions.append("""
                mc.id IN (
                    SELECT concept_id
                    FROM math_concept_classifications
                    WHERE classification_id = (
                        SELECT id
                        FROM math_classifications
                        WHERE code = ?
                    )
                )
            """)
            params.append(class_filter.upper().strip())

        if search_query:
            search_query = search_query.strip()
            conditions.append("""
                (
                    mc.title LIKE ?
                    OR mc.slug LIKE ?
                    OR mcl.code LIKE ?
                )
            """)
            like_param = f"%{search_query}%"
            params.extend([like_param, like_param, like_param])

        if conditions:
            query_base += " WHERE " + " AND ".join(conditions)

        query_base += """
            GROUP BY mc.id
            ORDER BY mc.title ASC;
        """

        cursor.execute(query_base, params)

        concepts = []

        for row in cursor.fetchall():
            d = dict(row)
            d["types"] = (
                d["type_names"].split(",")
                if d["type_names"]
                else []
            )
            d["classification_codes"] = (
                d["classification_codes"].split(",")
                if d["classification_codes"]
                else []
            )
            d.pop("type_names", None)
            concepts.append(d)

        return jsonify({
            "status": "success",
            "count": len(concepts),
            "data": concepts
        }), 200

    except sqlite3.Error as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

    finally:
        if conn:
            conn.close()


@math_bp.route("/api/math/concepts/<slug>", methods=["GET", "OPTIONS"])
def get_math_concept_detail(slug):
    """Public deep-dive view to fetch dynamic text payloads with autolinks."""
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    conn = None

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Supports concept.html?slug=... and also the older JS fallback where an id
        # may be passed into the same route.
        if str(slug).isdigit():
            cursor.execute("""
                SELECT
                    mc.id,
                    mc.title,
                    mc.slug,
                    mc.owner,
                    mc.created_at,
                    mc.updated_at,
                    mc.cleaned_tex,
                    mc.rendered_tex
                FROM math_concepts mc
                WHERE mc.slug = ?
                   OR mc.id = ?;
            """, (slug, int(slug)))
        else:
            cursor.execute("""
                SELECT
                    mc.id,
                    mc.title,
                    mc.slug,
                    mc.owner,
                    mc.created_at,
                    mc.updated_at,
                    mc.cleaned_tex,
                    mc.rendered_tex
                FROM math_concepts mc
                WHERE mc.slug = ?;
            """, (slug,))

        concept_row = cursor.fetchone()

        if not concept_row:
            return jsonify({
                "status": "error",
                "message": "Concept not found."
            }), 404

        concept_data = dict(concept_row)
        concept_id = concept_data["id"]

        display_tex = (
            concept_data["rendered_tex"]
            or concept_data["cleaned_tex"]
        )

        concept_data["display_tex"] = apply_math_autolinker(
            concept_id,
            display_tex,
            cursor
        )

        cursor.execute("""
            SELECT mt.type_name
            FROM math_types mt
            JOIN math_concept_types mct
                ON mt.id = mct.type_id
            WHERE mct.concept_id = ?
            ORDER BY mt.type_name ASC;
        """, (concept_id,))

        concept_data["types"] = [
            r["type_name"]
            for r in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT mcl.code, mcl.text
            FROM math_classifications mcl
            JOIN math_concept_classifications mcc
                ON mcl.id = mcc.classification_id
            WHERE mcc.concept_id = ?
            ORDER BY mcl.code ASC;
        """, (concept_id,))

        concept_data["classifications"] = [
            {"code": r["code"], "text": r["text"]}
            for r in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT synonym_text
            FROM math_synonyms
            WHERE concept_id = ?
            ORDER BY synonym_text ASC;
        """, (concept_id,))

        concept_data["synonyms"] = [
            r["synonym_text"]
            for r in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT defined_term
            FROM math_definitions
            WHERE concept_id = ?
            ORDER BY defined_term ASC;
        """, (concept_id,))

        concept_data["definitions"] = [
            r["defined_term"]
            for r in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT
                rc.related_concept_id AS id,
                mc.title,
                mc.canonical_name,
                mc.slug
            FROM math_related_concepts rc
            JOIN math_concepts mc
                ON mc.id = rc.related_concept_id
            WHERE rc.concept_id = ?
            ORDER BY mc.title ASC;
        """, (concept_id,))

        concept_data["related_concepts"] = [
            dict(r)
            for r in cursor.fetchall()
        ]

        return jsonify({
            "status": "success",
            "data": concept_data
        }), 200

    except sqlite3.Error as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

    finally:
        if conn:
            conn.close()


@math_bp.route("/api/admin/math/concepts/<int:concept_id>", methods=["GET", "OPTIONS"])
def get_admin_math_concept_detail(concept_id):
    """
    Protected admin read route for hydrating edit.html?id=123.

    Returns:
      - cleaned_tex from math_concepts, editable
      - rendered_tex from math_concepts, read-only
      - raw_tex from stg_math_import.raw_content, read-only
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    from app import admin_required

    @admin_required
    def process_read():
        conn = None

        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    mc.id,
                    mc.canonical_name,
                    mc.slug,
                    mc.title,
                    mc.owner,
                    mc.created_at,
                    mc.updated_at,
                    mc.source_staging_id,
                    mc.source_file_name,
                    stg.raw_content AS raw_tex,
                    mc.cleaned_tex,
                    mc.rendered_tex,
                    mc.is_cleaned
                FROM math_concepts mc
                LEFT JOIN stg_math_import stg
                    ON stg.id = mc.source_staging_id
                WHERE mc.id = ?;
            """, (concept_id,))

            concept_row = cursor.fetchone()

            if not concept_row:
                return jsonify({
                    "status": "error",
                    "message": "Concept not found."
                }), 404

            concept_data = dict(concept_row)

            cursor.execute("""
                SELECT mcl.code, mcl.text
                FROM math_classifications mcl
                JOIN math_concept_classifications mcc
                    ON mcl.id = mcc.classification_id
                WHERE mcc.concept_id = ?
                ORDER BY mcl.code ASC;
            """, (concept_id,))

            concept_data["classifications"] = [
                {"code": r["code"], "text": r["text"]}
                for r in cursor.fetchall()
            ]

            cursor.execute("""
                SELECT mt.type_name
                FROM math_types mt
                JOIN math_concept_types mct
                    ON mt.id = mct.type_id
                WHERE mct.concept_id = ?
                ORDER BY mt.type_name ASC;
            """, (concept_id,))

            concept_data["types"] = [
                r["type_name"]
                for r in cursor.fetchall()
            ]

            cursor.execute("""
                SELECT synonym_text
                FROM math_synonyms
                WHERE concept_id = ?
                ORDER BY synonym_text ASC;
            """, (concept_id,))

            concept_data["synonyms"] = [
                r["synonym_text"]
                for r in cursor.fetchall()
            ]

            cursor.execute("""
                SELECT defined_term
                FROM math_definitions
                WHERE concept_id = ?
                ORDER BY defined_term ASC;
            """, (concept_id,))

            concept_data["definitions"] = [
                r["defined_term"]
                for r in cursor.fetchall()
            ]

            cursor.execute("""
                SELECT word
                FROM math_link_exclusions
                WHERE concept_id = ?
                ORDER BY word ASC;
            """, (concept_id,))

            concept_data["link_exclusions"] = [
                r["word"]
                for r in cursor.fetchall()
            ]

            cursor.execute("""
                SELECT
                    rc.id,
                    rc.related_canonical_name,
                    rc.related_concept_id,
                    mc.title,
                    mc.canonical_name,
                    mc.slug
                FROM math_related_concepts rc
                LEFT JOIN math_concepts mc
                    ON mc.id = rc.related_concept_id
                WHERE rc.concept_id = ?
                ORDER BY COALESCE(mc.title, rc.related_canonical_name) ASC;
            """, (concept_id,))

            concept_data["related_concepts"] = [
                dict(r)
                for r in cursor.fetchall()
            ]

            cursor.execute("""
                SELECT
                    id,
                    block_index,
                    source_hash,
                    source_tex,
                    failure_stage,
                    error_output,
                    tex_temp_path,
                    created_at
                FROM math_concept_diagram_failures
                WHERE concept_id = ?
                ORDER BY block_index ASC;
            """, (concept_id,))

            concept_data["diagram_failures"] = [
                dict(r)
                for r in cursor.fetchall()
            ]

            return jsonify({
                "status": "success",
                "data": concept_data
            }), 200

        except sqlite3.Error as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

        finally:
            if conn:
                conn.close()

    return process_read()


@math_bp.route("/api/admin/math/update", methods=["POST", "OPTIONS"])
def update_math_metadata():
    """
    Protected transactional endpoint for updates.

    Only cleaned_tex is editable here. rendered_tex is cleared so the public page
    falls back to updated cleaned_tex until step2_build_diagrams.py regenerates
    rendered_tex.
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    from app import admin_required

    @admin_required
    def process_update():
        data = request.get_json() or {}

        concept_id = data.get("id")
        updated_tex = data.get("cleaned_tex", "").strip()
        updated_title = data.get("title", "").strip()
        updated_owner = data.get("owner", "CWoo").strip() or "CWoo"

        classifications = data.get("classifications", [])
        types = data.get("types", [])
        synonyms = data.get("synonyms", [])
        definitions = data.get("definitions", [])
        related_concepts = data.get("related_concepts", [])
        is_cleaned_flag = data.get("is_cleaned", 0)

        if not concept_id or not updated_title or not updated_tex:
            return jsonify({
                "success": False,
                "message": "Missing required operational field values."
            }), 400

        uniform_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = None

        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            # Fetch existing TeX before updating so smart-save can compare old vs new.
            cursor.execute("""
                SELECT
                    cleaned_tex,
                    slug
                FROM math_concepts
                WHERE id = ?;
            """, (concept_id,))

            existing_row = cursor.fetchone()

            if not existing_row:
                return jsonify({
                    "success": False,
                    "message": f"Concept id {concept_id} was not found."
                }), 404

            old_cleaned_tex = existing_row[0] or ""
            current_slug = existing_row[1] or None

            smart_save = determine_smart_save_mode(
                old_cleaned_tex,
                updated_tex
            )

            # Update core record.
            # Smart-save Phase C2:
            # If TeX did not change, preserve rendered_tex exactly as-is.
            # If TeX changed, rendered_tex is still cleared for now.
            # The next slice will refresh rendered_tex for text-only changes.
            if smart_save["save_mode"] == "metadata_only":
                # TeX did not change. Preserve rendered_tex exactly as-is.
                cursor.execute("""
                    UPDATE math_concepts
                    SET
                        title = ?,
                        owner = ?,
                        cleaned_tex = ?,
                        updated_at = ?,
                        is_cleaned = ?
                    WHERE id = ?;
                """, (
                    updated_title,
                    updated_owner,
                    updated_tex,
                    uniform_timestamp,
                    is_cleaned_flag,
                    concept_id
                ))

            elif smart_save["save_mode"] == "text_render_only":
                # TeX changed, but PSTricks blocks did not.
                # Refresh rendered_tex safely without regenerating diagrams.
                refreshed_rendered_tex = render_tex_reusing_existing_diagrams(
                    concept_id=concept_id,
                    cleaned_tex=updated_tex,
                    cursor=cursor
                )

                cursor.execute("""
                    UPDATE math_concepts
                    SET
                        title = ?,
                        owner = ?,
                        cleaned_tex = ?,
                        rendered_tex = ?,
                        updated_at = ?,
                        is_cleaned = ?
                    WHERE id = ?;
                """, (
                    updated_title,
                    updated_owner,
                    updated_tex,
                    refreshed_rendered_tex,
                    uniform_timestamp,
                    is_cleaned_flag,
                    concept_id
                ))

            else:
                # PSTricks blocks changed.
                # For now, do not attempt diagram generation in Save.
                # The next phase will require Render Preview before Save.
                cursor.execute("""
                    UPDATE math_concepts
                    SET
                        title = ?,
                        owner = ?,
                        cleaned_tex = ?,
                        rendered_tex = NULL,
                        updated_at = ?,
                        is_cleaned = ?
                    WHERE id = ?;
                """, (
                    updated_title,
                    updated_owner,
                    updated_tex,
                    uniform_timestamp,
                    is_cleaned_flag,
                    concept_id
                ))

            # Rebuild classifications.
            cursor.execute("""
                DELETE FROM math_concept_classifications
                WHERE concept_id = ?;
            """, (concept_id,))

            for code in classifications:
                clean_code = code.upper().strip()

                if not clean_code:
                    continue

                cursor.execute("""
                    SELECT id
                    FROM math_classifications
                    WHERE code = ?;
                """, (clean_code,))

                row = cursor.fetchone()

                if row:
                    cursor.execute("""
                        INSERT OR IGNORE INTO math_concept_classifications (
                            concept_id,
                            classification_id
                        )
                        VALUES (?, ?);
                    """, (concept_id, row[0]))

            # Rebuild types.
            cursor.execute("""
                DELETE FROM math_concept_types
                WHERE concept_id = ?;
            """, (concept_id,))

            for t_name in types:
                clean_type = t_name.strip().capitalize()

                if not clean_type:
                    continue

                cursor.execute("""
                    SELECT id
                    FROM math_types
                    WHERE type_name = ?;
                """, (clean_type,))

                row = cursor.fetchone()

                if row:
                    cursor.execute("""
                        INSERT OR IGNORE INTO math_concept_types (
                            concept_id,
                            type_id
                        )
                        VALUES (?, ?);
                    """, (concept_id, row[0]))

            # Rebuild synonyms.
            cursor.execute("""
                DELETE FROM math_synonyms
                WHERE concept_id = ?;
            """, (concept_id,))

            for syn in synonyms:
                clean_syn = syn.strip()

                if clean_syn:
                    cursor.execute("""
                        INSERT INTO math_synonyms (
                            concept_id,
                            synonym_text
                        )
                        VALUES (?, ?);
                    """, (concept_id, clean_syn))

            # Rebuild defined terms.
            cursor.execute("""
                DELETE FROM math_definitions
                WHERE concept_id = ?;
            """, (concept_id,))

            for d_term in definitions:
                clean_term = d_term.strip()

                if clean_term:
                    cursor.execute("""
                        INSERT INTO math_definitions (
                            concept_id,
                            defined_term
                        )
                        VALUES (?, ?);
                    """, (concept_id, clean_term))

            # Rebuild related concepts.
            cursor.execute("""
                DELETE FROM math_related_concepts
                WHERE concept_id = ?;
            """, (concept_id,))

            for rel_name in related_concepts:
                clean_rel = rel_name.strip()

                if clean_rel:
                    cursor.execute("""
                        INSERT INTO math_related_concepts (
                            concept_id,
                            related_canonical_name
                        )
                        VALUES (?, ?);
                    """, (concept_id, clean_rel))

            cursor.execute("""
                UPDATE math_related_concepts
                SET related_concept_id = (
                    SELECT mc.id
                    FROM math_concepts mc
                    WHERE mc.canonical_name = math_related_concepts.related_canonical_name
                )
                WHERE concept_id = ?;
            """, (concept_id,))

            conn.commit()

            return jsonify({
                "success": True,
                "message": smart_save["message"],
                "concept_id": concept_id,
                "slug": current_slug,
                "save_mode": smart_save["save_mode"],
                "tex_changed": smart_save["tex_changed"],
                "pstricks_changed": smart_save["pstricks_changed"],
                "diagram_compare": smart_save["diagram_compare"]
            }), 200

        except sqlite3.Error as e:
            if conn:
                conn.rollback()

            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

        finally:
            if conn:
                conn.close()

    return process_update()


@math_bp.route("/api/admin/math/create", methods=["POST", "OPTIONS"])
def create_new_math_concept():
    """Protected admin route for creating new math concepts."""
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    from app import admin_required

    @admin_required
    def process_creation():
        data = request.get_json() or {}

        title = data.get("title", "").strip()
        cleaned_tex = data.get("cleaned_tex", "").strip()
        owner = data.get("owner", "CWoo").strip() or "CWoo"

        classifications = data.get("classifications", [])
        types = data.get("types", [])
        synonyms = data.get("synonyms", [])
        definitions = data.get("definitions", [])
        related_concepts = data.get("related_concepts", [])
        is_cleaned_flag = data.get("is_cleaned", 0)

        if not title or not cleaned_tex:
            return jsonify({
                "success": False,
                "message": "Title and LaTeX body fields are strictly required."
            }), 400

        canonical_name = title.replace(" ", "")
        slug = generate_slug(canonical_name)
        uniform_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = None

        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            cursor.execute("""
                INSERT INTO math_concepts (
                    canonical_name,
                    slug,
                    title,
                    created_at,
                    updated_at,
                    owner,
                    source_staging_id,
                    source_file_name,
                    cleaned_tex,
                    rendered_tex,
                    is_cleaned
                )
                VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, NULL, ?);
            """, (
                canonical_name,
                slug,
                title,
                uniform_timestamp,
                uniform_timestamp,
                owner,
                cleaned_tex,
                is_cleaned_flag
            ))

            concept_id = cursor.lastrowid

            # Attach classifications.
            for code in classifications:
                clean_code = code.upper().strip()

                if not clean_code:
                    continue

                cursor.execute("""
                    SELECT id
                    FROM math_classifications
                    WHERE code = ?;
                """, (clean_code,))

                row = cursor.fetchone()

                if row:
                    cursor.execute("""
                        INSERT OR IGNORE INTO math_concept_classifications (
                            concept_id,
                            classification_id
                        )
                        VALUES (?, ?);
                    """, (concept_id, row[0]))

            # Attach document types.
            for t_name in types:
                clean_type = t_name.strip().capitalize()

                if not clean_type:
                    continue

                cursor.execute("""
                    SELECT id
                    FROM math_types
                    WHERE type_name = ?;
                """, (clean_type,))

                row = cursor.fetchone()

                if row:
                    cursor.execute("""
                        INSERT OR IGNORE INTO math_concept_types (
                            concept_id,
                            type_id
                        )
                        VALUES (?, ?);
                    """, (concept_id, row[0]))

            # Attach synonyms.
            for syn in synonyms:
                clean_syn = syn.strip()

                if clean_syn:
                    cursor.execute("""
                        INSERT INTO math_synonyms (
                            concept_id,
                            synonym_text
                        )
                        VALUES (?, ?);
                    """, (concept_id, clean_syn))

            # Attach defined terms.
            for d_term in definitions:
                clean_term = d_term.strip()

                if clean_term:
                    cursor.execute("""
                        INSERT INTO math_definitions (
                            concept_id,
                            defined_term
                        )
                        VALUES (?, ?);
                    """, (concept_id, clean_term))

            # Attach related concepts.
            for rel_name in related_concepts:
                clean_rel = rel_name.strip()

                if clean_rel:
                    cursor.execute("""
                        INSERT INTO math_related_concepts (
                            concept_id,
                            related_canonical_name
                        )
                        VALUES (?, ?);
                    """, (concept_id, clean_rel))

            cursor.execute("""
                UPDATE math_related_concepts
                SET related_concept_id = (
                    SELECT mc.id
                    FROM math_concepts mc
                    WHERE mc.canonical_name = math_related_concepts.related_canonical_name
                )
                WHERE concept_id = ?;
            """, (concept_id,))

            conn.commit()

            return jsonify({
                "success": True,
                "message": "New concept generated successfully!",
                "concept_id": concept_id,
                "id": concept_id,
                "slug": slug
            }), 201

        except sqlite3.IntegrityError as e:
            if conn:
                conn.rollback()

            return jsonify({
                "success": False,
                "error": str(e),
                "message": "A concept with this canonical name or slug may already exist."
            }), 409

        except sqlite3.Error as e:
            if conn:
                conn.rollback()

            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

        finally:
            if conn:
                conn.close()

    return process_creation()