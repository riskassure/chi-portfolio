# backend/src/routes/admin_math.py

import sqlite3
import sys
import re
from datetime import datetime
from flask import Blueprint, jsonify, request, send_from_directory

# Locate backend/src/ to grab the database configuration parameters
sys.path.append(str(sys.path[0] + '/..'))
from config import DB_PATH, MATH_DIAGRAM_DIR

math_bp = Blueprint('math_bp', __name__)

@math_bp.route("/api/math/diagrams/<path:filename>", methods=["GET"])
def serve_math_diagram(filename):
    return send_from_directory(MATH_DIAGRAM_DIR, filename)

def generate_slug(canonical_name):
    if not canonical_name: return None
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', canonical_name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1)
    return s2.lower().replace('_', '-').replace('--', '-')

def apply_math_autolinker(concept_id, tex_content, db_cursor):
    """
    Tokenizes LaTeX content to safely apply anchor tags ONLY within standard
    descriptive text blocks, leaving math mode and structural layouts untouched.
    Uses an absolute positional index scanner to completely avoid string offset 
    drift errors during regex execution.
    """
    if not tex_content:
        return ""

    # 1. Gather this specific document's database link exclusions
    db_cursor.execute("SELECT word FROM math_link_exclusions WHERE concept_id = ?;", (concept_id,))
    # Use index lookups row[0] to maintain database scope safety independently of row_factory styles
    local_exclusions = {row[0].lower().strip() for row in db_cursor.fetchall()}

    # 2. Parse inline explicit macro overrides (\PMlinkescapeword{word})
    escaped_macros = re.findall(r'\\PMlinkescapeword\{([^}]+)\}', tex_content)
    for word in escaped_macros:
        local_exclusions.add(word.lower().strip())

    # Clean the macro tags out so they don't corrupt the presentation layer layout
    tex_content = re.sub(r'\\PMlinkescapeword\{[^}]+\}', '', tex_content)

    # 3. Harvest all available global cross-linking destination keys across the platform
    targets = {}
    
    # Base concept titles
    db_cursor.execute("SELECT id, title, slug FROM math_concepts WHERE id != ?;", (concept_id,))
    for row in db_cursor.fetchall():
        targets[row[1].lower().strip()] = row[2]

    # Platform Synonyms
    db_cursor.execute("""
        SELECT ms.synonym_text, mc.slug 
        FROM math_synonyms ms
        JOIN math_concepts mc ON ms.concept_id = mc.id
        WHERE ms.concept_id != ?;
    """, (concept_id,))
    for row in db_cursor.fetchall():
        targets[row[0].lower().strip()] = row[1]

    # Platform Defined Terms
    db_cursor.execute("""
        SELECT md.defined_term, mc.slug 
        FROM math_definitions md
        JOIN math_concepts mc ON md.concept_id = mc.id
        WHERE md.concept_id != ?;
    """, (concept_id,))
    for row in db_cursor.fetchall():
        targets[row[0].lower().strip()] = row[1]

    # Filter out target dictionary terms that match our calculated exclusion arrays
    active_targets = {k: v for k, v in targets.items() if k not in local_exclusions and len(k) > 2}

    if not active_targets:
        return tex_content

    # Sort phrase dictionary keys by character length descending
    sorted_phrases = sorted(active_targets.keys(), key=len, reverse=True)

    # Compile a SINGLE Master Alternation Pattern of all dictionary terms
    master_pattern_str = r'\b(' + '|'.join(re.escape(phrase) for phrase in sorted_phrases) + r')\b'
    master_regex = re.compile(master_pattern_str, re.IGNORECASE)

    # 4. TOKENIZE ENGINE: Split the TeX string into safe text blocks vs sensitive math blocks
    token_pattern = re.compile(
        r'(\$\$.*?\$\$|\$.*?\$|\\begin\{.*?\}.*?\\end\{.*?\}|\\\w+)', 
        re.DOTALL | re.IGNORECASE
    )
    
    chunks = token_pattern.split(tex_content)
    processed_chunks = []

    for chunk in chunks:
        # If the block is math syntax or macro declarations, bypass processing entirely
        if chunk.startswith('$') or chunk.startswith('\\'):
            processed_chunks.append(chunk)
            continue
        
        # Safe text chunk loop processing: tracks dynamic string expansions using scanner positions
        cursor_pos = 0
        built_chunk = ""
        
        for match in master_regex.finditer(chunk):
            start, end = match.start(), match.end()
            matched_text = match.group(1)
            matched_lower = matched_text.lower().strip()
            slug_target = active_targets.get(matched_lower)
            
            # Catch up text from last checked point to current match
            built_chunk += chunk[cursor_pos:start]
            cursor_pos = end
            
            if not slug_target:
                built_chunk += matched_text
                continue
                
            # Perform a structural barrier inspection on the context built up so far
            # Checking built_chunk gives us the exact current HTML state, preventing link injection anomalies
            last_open_bracket = built_chunk.rfind("<")
            last_close_bracket = built_chunk.rfind(">")
            if last_open_bracket > last_close_bracket:
                built_chunk += matched_text
                continue
                
            last_open_a = built_chunk.rfind("<a")
            last_close_a = built_chunk.rfind("</a>")
            if last_open_a > last_close_a:
                built_chunk += matched_text
                continue
                
            # Safe to insert structured link tag
            built_chunk += f'<a class="math-autolink" href="concept.html?slug={slug_target}">{matched_text}</a>'
            
        # Append any remaining characters left in the text sequence
        built_chunk += chunk[cursor_pos:]
        processed_chunks.append(built_chunk)

    return "".join(processed_chunks)


@math_bp.route("/api/math/classifications", methods=["GET", "OPTIONS"])
def get_active_classifications():
    """Public lookup route supplying active MSC classifications for Tier #1 & #2 directory hubs."""
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT mcl.code, mcl.text
            FROM math_classifications mcl
            JOIN math_concept_classifications mcc ON mcl.id = mcc.classification_id
            ORDER BY mcl.code ASC;
        """)
        categories = [dict(row) for row in cursor.fetchall()]
        return jsonify({"status": "success", "count": len(categories), "data": categories}), 200
    except sqlite3.Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()


@math_bp.route("/api/admin/math/classifications/search", methods=["GET"])
def search_classifications_typeahead():
    """Typeahead autocomplete lookup facilitating rapid dynamic administrative keyword searching."""
    query_param = request.args.get('q', default='', type=str).strip()
    if len(query_param) < 2:
        return jsonify({"status": "success", "data": []}), 200

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT code, text 
            FROM math_classifications 
            WHERE code LIKE ? OR text LIKE ? 
            LIMIT 15;
        """, (f"%{query_param}%", f"%{query_param}%"))
        
        results = [{"code": r["code"], "text": r["text"]} for r in cursor.fetchall()]
        return jsonify({"status": "success", "data": results}), 200
    except sqlite3.Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()


@math_bp.route("/api/math/concepts", methods=["GET", "OPTIONS"])
def get_math_concepts():
    """Public read route to populate standard UI layouts/cards, filtering by specific codes or keyword query."""
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    try:
        class_filter = request.args.get('classification', default=None, type=str)
        search_query = request.args.get('q', default=None, type=str)

        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 🌟 FIXED: Removed the unsupported explicit separator from DISTINCT aggregates
        query_base = """
            SELECT 
                mc.id, mc.title, mc.slug, mc.owner, mc.created_at, mc.updated_at, mc.is_cleaned,
                GROUP_CONCAT(DISTINCT mt.type_name) AS type_names,
                GROUP_CONCAT(DISTINCT mcl.code) AS classification_codes
            FROM math_concepts mc
            LEFT JOIN math_concept_types mct ON mc.id = mct.concept_id
            LEFT JOIN math_types mt ON mct.type_id = mt.id
            LEFT JOIN math_concept_classifications mcc ON mc.id = mcc.concept_id
            LEFT JOIN math_classifications mcl ON mcc.classification_id = mcl.id
        """
        conditions = []
        params = []
        
        if class_filter:
            conditions.append("mc.id IN (SELECT concept_id FROM math_concept_classifications WHERE classification_id = (SELECT id FROM math_classifications WHERE code = ?))")
            params.append(class_filter.upper().strip())
            
        if search_query:
            search_query = search_query.strip()
            conditions.append("(mc.title LIKE ? OR mc.slug LIKE ? OR mcl.code LIKE ?)")
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
            # 🌟 FIXED: Reverted back to parsing standard comma-delimited strings safely
            d["types"] = d["type_names"].split(",") if d["type_names"] else []
            d["classification_codes"] = d["classification_codes"].split(",") if d["classification_codes"] else []
            d.pop("type_names", None)
            concepts.append(d)

        return jsonify({"status": "success", "count": len(concepts), "data": concepts}), 200
    except sqlite3.Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()


@math_bp.route("/api/math/concepts/<slug>", methods=["GET", "OPTIONS"])
def get_math_concept_detail(slug):
    """Public deep-dive view to fetch dynamic text payloads with integrated autolinks."""
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT mc.id, mc.title, mc.slug, mc.owner, mc.created_at, mc.updated_at,
                   mc.cleaned_tex, mc.rendered_tex
            FROM math_concepts mc
            WHERE mc.slug = ?;
        """, (slug,))
        concept_row = cursor.fetchone()
        
        if not concept_row:
            return jsonify({"status": "error", "message": "Concept not found."}), 404
            
        # 🌟 FIXED: Converted the immutable row object to a dictionary BEFORE mutations!
        concept_data = dict(concept_row)
        concept_id = concept_data["id"]
        
        display_tex = concept_data["rendered_tex"] or concept_data["cleaned_tex"]
        concept_data["display_tex"] = apply_math_autolinker(concept_id, display_tex, cursor)

        # Grab assigned types
        cursor.execute("""
            SELECT mt.type_name FROM math_types mt
            JOIN math_concept_types mct ON mt.id = mct.type_id WHERE mct.concept_id = ?;
        """, (concept_id,))
        concept_data["types"] = [r["type_name"] for r in cursor.fetchall()]

        # Grab assigned classification codes
        cursor.execute("""
            SELECT mcl.code, mcl.text FROM math_classifications mcl
            JOIN math_concept_classifications mcc ON mcl.id = mcc.classification_id WHERE mcc.concept_id = ?;
        """, (concept_id,))
        concept_data["classifications"] = [{"code": r["code"], "text": r["text"]} for r in cursor.fetchall()]

        # Grab metadata arrays
        cursor.execute("SELECT synonym_text FROM math_synonyms WHERE concept_id = ?;", (concept_id,))
        concept_data["synonyms"] = [r["synonym_text"] for r in cursor.fetchall()]
        
        cursor.execute("SELECT defined_term FROM math_definitions WHERE concept_id = ?;", (concept_id,))
        concept_data["definitions"] = [r["defined_term"] for r in cursor.fetchall()]
        
        return jsonify({"status": "success", "data": concept_data}), 200
    except sqlite3.Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()


@math_bp.route("/api/admin/math/update", methods=["POST", "OPTIONS"])
def update_math_metadata():
    """Protected transactional endpoint executing atomic clear-and-rebuild actions for updates."""
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    from app import admin_required

    @admin_required
    def process_update():
        data = request.get_json() or {}
        concept_id = data.get("id")
        updated_tex = data.get("cleaned_tex", "").strip()
        updated_title = data.get("title", "").strip()
        
        classifications = data.get("classifications", [])
        types = data.get("types", [])
        synonyms = data.get("synonyms", [])
        definitions = data.get("definitions", [])
        is_cleaned_flag = data.get("is_cleaned", 0)

        if not concept_id or not updated_title or not updated_tex:
            return jsonify({"success": False, "message": "Missing required operational field values."}), 400

        uniform_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            
            # 1. Update Core Records
            cursor.execute("""
                UPDATE math_concepts 
                SET title = ?, cleaned_tex = ?, updated_at = ?, is_cleaned = ?
                WHERE id = ?;
            """, (updated_title, updated_tex, uniform_timestamp, is_cleaned_flag, concept_id))
            
            # 2. Rebuild Relational Bridges Clear-and-Insert Pattern
            cursor.execute("DELETE FROM math_concept_classifications WHERE concept_id = ?;", (concept_id,))
            for code in classifications:
                cursor.execute("SELECT id FROM math_classifications WHERE code = ?;", (code.upper().strip(),))
                row = cursor.fetchone()
                if row:
                    cursor.execute("INSERT INTO math_concept_classifications (concept_id, classification_id) VALUES (?, ?);", (concept_id, row[0]))

            cursor.execute("DELETE FROM math_concept_types WHERE concept_id = ?;", (concept_id,))
            for t_name in types:
                cursor.execute("SELECT id FROM math_types WHERE type_name = ?;", (t_name.strip().capitalize(),))
                row = cursor.fetchone()
                if row:
                    cursor.execute("INSERT INTO math_concept_types (concept_id, type_id) VALUES (?, ?);", (concept_id, row[0]))

            # 3. Flush and rebuild Meta Lists
            cursor.execute("DELETE FROM math_synonyms WHERE concept_id = ?;", (concept_id,))
            for syn in synonyms:
                if syn.strip():
                    cursor.execute("INSERT INTO math_synonyms (concept_id, synonym_text) VALUES (?, ?);", (concept_id, syn.strip()))

            cursor.execute("DELETE FROM math_definitions WHERE concept_id = ?;", (concept_id,))
            for d_term in definitions:
                if d_term.strip():
                    cursor.execute("INSERT INTO math_definitions (concept_id, defined_term) VALUES (?, ?);", (concept_id, d_term.strip()))

            conn.commit()
            return jsonify({"success": True, "message": "Mathematical asset modifications completely recorded."})
        except sqlite3.Error as e:
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            conn.close()

    return process_update()


@math_bp.route("/api/admin/math/create", methods=["POST", "OPTIONS"])
def create_new_math_concept():
    """Protected admin route processing new additions to the portfolio matrix."""
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    from app import admin_required

    @admin_required
    def process_creation():
        data = request.get_json() or {}
        title = data.get("title", "").strip()
        raw_tex = data.get("cleaned_tex", "").strip()
        owner = data.get("owner", "CWoo").strip()
        
        classifications = data.get("classifications", [])
        types = data.get("types", [])
        synonyms = data.get("synonyms", [])
        definitions = data.get("definitions", [])
        is_cleaned_flag = data.get("is_cleaned", 0)

        if not title or not raw_tex:
            return jsonify({"success": False, "message": "Title and LaTeX body fields are strictly required."}), 400

        canonical_name = title.replace(" ", "")
        slug = generate_slug(canonical_name)
        uniform_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            # Insert Core Entity
            cursor.execute("""
                INSERT INTO math_concepts (canonical_name, slug, title, created_at, updated_at, owner, cleaned_tex, is_cleaned)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (canonical_name, slug, title, uniform_timestamp, uniform_timestamp, owner, raw_tex, is_cleaned_flag))
            concept_id = cursor.lastrowid

            # Attach Relational Meta Maps
            for code in classifications:
                cursor.execute("SELECT id FROM math_classifications WHERE code = ?;", (code.upper().strip(),))
                row = cursor.fetchone()
                if row:
                    cursor.execute("INSERT INTO math_concept_classifications (concept_id, classification_id) VALUES (?, ?);", (concept_id, row[0]))

            for t_name in types:
                cursor.execute("SELECT id FROM math_types WHERE type_name = ?;", (t_name.strip().capitalize(),))
                row = cursor.fetchone()
                if row:
                    cursor.execute("INSERT INTO math_concept_types (concept_id, type_id) VALUES (?, ?);", (concept_id, row[0]))

            for syn in synonyms:
                if syn.strip():
                    cursor.execute("INSERT INTO math_synonyms (concept_id, synonym_text) VALUES (?, ?);", (concept_id, syn.strip()))
            for d_term in definitions:
                if d_term.strip():
                    cursor.execute("INSERT INTO math_definitions (concept_id, defined_term) VALUES (?, ?);", (concept_id, d_term.strip()))

            conn.commit()
            return jsonify({"success": True, "message": "New concept generated successfully!", "slug": slug}), 201
        except sqlite3.Error as e:
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            conn.close()

    return process_creation()