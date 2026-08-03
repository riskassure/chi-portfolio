# backend/src/routes/admin_math.py

import sqlite3
import sys
import re
from pathlib import Path
from datetime import datetime
from flask import Blueprint, jsonify, request, send_from_directory

SRC_DIR = Path(__file__).resolve().parents[1]  # backend/src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DB_PATH, MATH_DIAGRAM_DIR

from services.math.concept_render_service import (
    render_math_preview,
)

from services.math.audit_service import (
    get_latest_completed_audit_run_id,
    get_now_timestamp,
    normalize_audit_mode,
)

from services.math.public_search_service import (
    search_public_math_library,
)

from services.math.public_catalog_service import (
    fetch_public_math_catalog,
)

from services.math.public_concept_detail_service import (
    fetch_public_math_concept_detail,
)

from services.math.admin_concept_detail_service import (
    fetch_admin_math_concept_detail,
)

from services.math.concept_create_service import (
    create_math_concept,
)

from services.math.concept_update_service import (
    update_math_concept,
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


@math_bp.route("/api/admin/math/audit-runs/batch-save", methods=["POST", "OPTIONS"])
def batch_save_math_audit_run():
    """Persist a completed browser-side MathJax audit run in one transaction."""
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    from app import admin_required

    @admin_required
    def process_batch_save():
        data = request.get_json() or {}

        mode = normalize_audit_mode(data.get("mode"))
        audit_version = (data.get("audit_version") or "mathjax-audit-v1").strip()
        results = data.get("results") or []

        if not isinstance(results, list):
            return jsonify({
                "status": "error",
                "message": "results must be a list."
            }), 400

        uniform_timestamp = get_now_timestamp()

        conn = None

        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            cursor.execute("""
                INSERT INTO math_audit_runs (
                    started_at,
                    completed_at,
                    audit_version,
                    mode,
                    total_scanned,
                    total_problematic,
                    total_errors
                )
                VALUES (?, NULL, ?, ?, 0, 0, 0);
            """, (
                uniform_timestamp,
                audit_version,
                mode
            ))

            run_id = cursor.lastrowid

            saved_count = 0

            for row in results:
                concept_id = row.get("concept_id")
                rendered_tex_hash = (row.get("rendered_tex_hash") or "unknown").strip()
                status = (row.get("status") or "").strip().lower()
                issue_count = int(row.get("issue_count") or 0)
                issue_summary = row.get("issue_summary") or ""

                if not concept_id:
                    continue

                if status not in {"clean", "problematic", "error"}:
                    status = "error"

                cursor.execute("""
                    INSERT OR REPLACE INTO math_concept_audit_results (
                        run_id,
                        concept_id,
                        rendered_tex_hash,
                        status,
                        issue_count,
                        issue_summary,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (
                    run_id,
                    concept_id,
                    rendered_tex_hash,
                    status,
                    issue_count,
                    issue_summary,
                    uniform_timestamp
                ))

                saved_count += 1

            cursor.execute("""
                SELECT
                    COUNT(*) AS total_scanned,
                    SUM(CASE WHEN status = 'problematic' THEN 1 ELSE 0 END) AS total_problematic,
                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS total_errors
                FROM math_concept_audit_results
                WHERE run_id = ?;
            """, (run_id,))

            totals = cursor.fetchone()

            total_scanned = totals[0] or 0
            total_problematic = totals[1] or 0
            total_errors = totals[2] or 0

            cursor.execute("""
                UPDATE math_audit_runs
                SET
                    completed_at = ?,
                    total_scanned = ?,
                    total_problematic = ?,
                    total_errors = ?
                WHERE id = ?;
            """, (
                get_now_timestamp(),
                total_scanned,
                total_problematic,
                total_errors,
                run_id
            ))

            conn.commit()

            return jsonify({
                "status": "success",
                "run_id": run_id,
                "saved_count": saved_count,
                "total_scanned": total_scanned,
                "total_problematic": total_problematic,
                "total_errors": total_errors
            }), 201

        except sqlite3.Error as e:
            if conn:
                conn.rollback()

            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

        finally:
            if conn:
                conn.close()

    return process_batch_save()
    

@math_bp.route("/api/admin/math/concepts/audit-list", methods=["GET", "OPTIONS"])
def get_admin_math_concepts_audit_list():
    """
    Protected lightweight concept list for the browser-side MathJax audit page.

    Supported modes:
      - all: return every concept
      - problematic: return concepts that were problematic/error in the latest completed audit run
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    from app import admin_required

    @admin_required
    def process_audit_list():
        mode = normalize_audit_mode(request.args.get("mode"))

        conn = None

        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            params = []
            latest_run_id = None

            if mode == "problematic":
                latest_run_id = get_latest_completed_audit_run_id(cursor)

                if latest_run_id is None:
                    return jsonify({
                        "status": "success",
                        "mode": mode,
                        "latest_run_id": None,
                        "count": 0,
                        "data": [],
                        "message": "No completed audit run exists yet."
                    }), 200

                where_clause = """
                    WHERE mc.id IN (
                        SELECT concept_id
                        FROM math_concept_audit_results
                        WHERE run_id = ?
                          AND status IN ('problematic', 'error')
                    )
                """
                params.append(latest_run_id)

            else:
                where_clause = ""

            cursor.execute(f"""
                SELECT
                    mc.id,
                    mc.canonical_name,
                    mc.slug,
                    mc.title
                FROM math_concepts mc
                {where_clause}
                ORDER BY
                    COALESCE(mc.title, mc.canonical_name, mc.slug, CAST(mc.id AS TEXT)) COLLATE NOCASE ASC;
            """, params)

            concepts = []

            for row in cursor.fetchall():
                concept = dict(row)

                concepts.append({
                    "id": concept["id"],
                    "canonical_name": concept["canonical_name"],
                    "slug": concept["slug"],
                    "title": (
                        concept["title"]
                        or concept["canonical_name"]
                        or concept["slug"]
                        or f"Concept {concept['id']}"
                    )
                })

            return jsonify({
                "status": "success",
                "mode": mode,
                "latest_run_id": latest_run_id,
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

    return process_audit_list()


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

    query_param = request.args.get(
        "q",
        default="",
        type=str,
    ).strip()

    if len(query_param) < 2:
        return jsonify({
            "status": "success",
            "query": query_param,
            "count": 0,
            "data": [],
        }), 200

    explicit_family_limits = (
        "concept_limit" in request.args
        or "classification_limit" in request.args
    )

    conn = None

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        search_result = search_public_math_library(
            cursor=cursor,
            query_param=query_param,
            overall_limit_value=request.args.get("limit"),
            concept_limit_value=request.args.get(
                "concept_limit"
            ),
            classification_limit_value=request.args.get(
                "classification_limit"
            ),
            explicit_family_limits=explicit_family_limits,
        )

        return jsonify({
            "status": "success",
            "query": query_param,
            **search_result,
        }), 200

    except sqlite3.Error as e:
        return jsonify({
            "status": "error",
            "message": str(e),
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

    classification_filter = request.args.get(
        "classification",
        default=None,
        type=str,
    )

    search_query = request.args.get(
        "q",
        default=None,
        type=str,
    )

    conn = None

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        concepts = fetch_public_math_catalog(
            cursor=cursor,
            classification_filter=classification_filter,
            search_query=search_query,
        )

        return jsonify({
            "status": "success",
            "count": len(concepts),
            "data": concepts,
        }), 200

    except sqlite3.Error as e:
        return jsonify({
            "status": "error",
            "message": str(e),
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

        concept_data = fetch_public_math_concept_detail(
            cursor=cursor,
            identifier=slug,
        )

        if concept_data is None:
            return jsonify({
                "status": "error",
                "message": "Concept not found.",
            }), 404

        return jsonify({
            "status": "success",
            "data": concept_data,
        }), 200

    except sqlite3.Error as e:
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500

    finally:
        if conn:
            conn.close()


@math_bp.route(
    "/api/admin/math/concepts/<int:concept_id>",
    methods=["GET", "OPTIONS"],
)
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

            concept_data = fetch_admin_math_concept_detail(
                cursor=cursor,
                concept_id=concept_id,
            )

            if concept_data is None:
                return jsonify({
                    "status": "error",
                    "message": "Concept not found.",
                }), 404

            return jsonify({
                "status": "success",
                "data": concept_data,
            }), 200

        except sqlite3.Error as e:
            return jsonify({
                "status": "error",
                "message": str(e),
            }), 500

        finally:
            if conn:
                conn.close()

    return process_read()


@math_bp.route("/api/admin/math/render-preview", methods=["POST", "OPTIONS"])
def render_admin_math_preview():
    """
    Render unsaved cleaned TeX for the admin editor.

    This route does not create or update concept records or diagram-table rows.
    It may create or reuse hash-named SVG files for successful PSTricks blocks.
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    from app import admin_required

    @admin_required
    def process_preview():
        data = request.get_json() or {}
        cleaned_tex = data.get("cleaned_tex", "")

        if not cleaned_tex.strip():
            return jsonify({
                "success": False,
                "message": "LaTeX body is required."
            }), 400

        try:
            preview_result = render_math_preview(cleaned_tex)

            return jsonify({
                "success": True,
                "rendered_tex": preview_result["rendered_tex"],
                "block_count": preview_result["block_count"],
                "success_count": preview_result["success_count"],
                "failure_count": preview_result["failure_count"],
                "failures": preview_result["failures"],
            }), 200

        except Exception as e:
            print("[ADMIN RENDER PREVIEW ERROR]", str(e))

            return jsonify({
                "success": False,
                "message": "Unable to render preview.",
                "error": str(e),
            }), 500

    return process_preview()


@math_bp.route("/api/admin/math/update", methods=["POST", "OPTIONS"])
def update_math_metadata():
    """
    Protected transactional endpoint for concept updates.

    Only cleaned_tex is editable here. rendered_tex is refreshed during save:
    existing diagram SVGs are reused when possible, and changed supported
    PSTricks diagrams are rebuilt inside the same transaction.
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

            update_result = update_math_concept(
                cursor=cursor,
                concept_id=concept_id,
                updated_title=updated_title,
                updated_owner=updated_owner,
                updated_tex=updated_tex,
                updated_at=uniform_timestamp,
                is_cleaned_flag=is_cleaned_flag,
                classifications=classifications,
                types=types,
                synonyms=synonyms,
                definitions=definitions,
                related_concepts=related_concepts,
            )

            if update_result is None:
                return jsonify({
                    "success": False,
                    "message": (
                        f"Concept id {concept_id} was not found."
                    ),
                }), 404

            conn.commit()

            return jsonify({
                "success": True,
                **update_result,
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

            create_result = create_math_concept(
                cursor=cursor,
                canonical_name=canonical_name,
                slug=slug,
                title=title,
                timestamp=uniform_timestamp,
                owner=owner,
                cleaned_tex=cleaned_tex,
                is_cleaned_flag=is_cleaned_flag,
                classifications=classifications,
                types=types,
                synonyms=synonyms,
                definitions=definitions,
                related_concepts=related_concepts,
            )

            conn.commit()

            return jsonify({
                "success": True,
                **create_result,
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