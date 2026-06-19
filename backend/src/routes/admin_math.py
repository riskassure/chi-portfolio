# backend/src/routes/admin_math.py

import sqlite3
import sys
from flask import Blueprint, jsonify, request

# Locate backend/src/ to grab the database configuration parameters
sys.path.append(str(sys.path[0] + '/..'))
from config import DB_PATH

math_bp = Blueprint('math_bp', __name__)

@math_bp.route("/api/math/concepts", methods=["GET", "OPTIONS"])
def get_math_concepts():
    """Public read route to populate standard UI layouts/cards."""
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Pull concept definitions grouped with their classification maps and bridge types
        cursor.execute("""
            SELECT 
                mc.id, mc.title, mc.slug, mc.owner, mc.created_at,
                GROUP_CONCAT(DISTINCT mt.type_name) AS type_names,
                GROUP_CONCAT(DISTINCT mcl.code) AS classification_codes
            FROM math_concepts mc
            LEFT JOIN math_concept_types mct ON mc.id = mct.concept_id
            LEFT JOIN math_types mt ON mct.type_id = mt.id
            LEFT JOIN math_concept_classifications mcc ON mc.id = mcc.concept_id
            LEFT JOIN math_classifications mcl ON mcc.classification_id = mcl.id
            GROUP BY mc.id
            ORDER BY mc.title ASC;
        """)
        
        concepts = []
        for row in cursor.fetchall():
            d = dict(row)
            # Transform group-concatenated strings into clean list arrays for the frontend UI
            d["types"] = d["type_names"].split(",") if d["type_names"] else []
            d["classification_codes"] = d["classification_codes"].split(",") if d["classification_codes"] else []
            # Pop old raw concatenated strings out of payload
            d.pop("type_names", None)
            concepts.append(d)

        return jsonify({"status": "success", "count": len(concepts), "data": concepts}), 200
    except sqlite3.Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

@math_bp.route("/api/math/concepts/<slug>", methods=["GET", "OPTIONS"])
def get_math_concept_detail(slug):
    """Public deep-dive view to fetch raw TeX content for rendering frames."""
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Select the concept data out of the core table context
        cursor.execute("""
            SELECT mc.id, mc.title, mc.slug, mc.owner, mc.created_at, mc.cleaned_tex
            FROM math_concepts mc
            WHERE mc.slug = ?;
        """, (slug,))
        concept_row = cursor.fetchone()
        
        if not concept_row:
            return jsonify({"status": "error", "message": "Concept not found."}), 404
            
        concept_data = dict(concept_row)
        concept_id = concept_data["id"]
        
        # Grab assigned document types via the relational bridge table
        cursor.execute("""
            SELECT mt.type_name 
            FROM math_types mt
            JOIN math_concept_types mct ON mt.id = mct.type_id
            WHERE mct.concept_id = ?;
        """, (concept_id,))
        concept_data["types"] = [r["type_name"] for r in cursor.fetchall()]

        # Grab assigned classification codes and descriptions
        cursor.execute("""
            SELECT mcl.code, mcl.text
            FROM math_classifications mcl
            JOIN math_concept_classifications mcc ON mcl.id = mcc.classification_id
            WHERE mcc.concept_id = ?;
        """, (concept_id,))
        concept_data["classifications"] = [{"code": r["code"], "text": r["text"]} for r in cursor.fetchall()]

        # Grab supplementary relational lists
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
    """Protected admin endpoint to modify TeX content or structural metadata."""
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    from app import admin_required

    @admin_required
    def process_update():
        data = request.get_json() or {}
        concept_id = data.get("id")
        updated_tex = data.get("cleaned_tex")
        updated_title = data.get("title")

        if not concept_id:
            return jsonify({"success": False, "message": "Missing target record identifier."}), 400

        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE math_concepts 
                SET title = COALESCE(?, title), cleaned_tex = COALESCE(?, cleaned_tex)
                WHERE id = ?;
            """, (updated_title, updated_tex, concept_id))
            
            conn.commit()
            return jsonify({"success": True, "message": "Mathematical portfolio asset updated successfully."})
        except sqlite3.Error as e:
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            conn.close()

    return process_update()