import sqlite3
import sys
from flask import Blueprint, jsonify, request

# 1. Tell Python to look up one folder level (out of routes/ into src/) to find config.py
sys.path.append(str(sys.path[0] + '/..'))
from config import DB_PATH          # 📥 Direct pull from source of truth!

music_bp = Blueprint('music_bp', __name__)

@music_bp.route("/api/music", methods=["GET", "OPTIONS"])
def get_music_catalog():
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    try:
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=25, type=int)
        offset = (page - 1) * per_page

        # Connect to SQLite using the absolute path string from config
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM music_catalog;")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT spotify_playlist, genre, composition_name, unit_name, 
                   track_name, composer, performer, album_name, 
                   release_date, duration_string, popularity, track_id 
            FROM music_catalog
            LIMIT ? OFFSET ?;
        """, (per_page, offset))
        
        catalog_list = [dict(row) for row in cursor.fetchall()]
        total_pages = (total_records + per_page - 1) // per_page
        
        return jsonify({
            "total_records": total_records,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "data": catalog_list
        })
    except sqlite3.Error as e:
        return jsonify({"error": f"Database transaction failed: {str(e)}"}), 500
    finally:
        conn.close()

@music_bp.route("/api/music/update", methods=["POST", "OPTIONS"])
def update_music_catalog():
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    from app import admin_required

    @admin_required
    def process_update():
        data = request.get_json() or {}
        payload_changes = data.get("changes", [])

        if not payload_changes:
            return jsonify({"success": True, "message": "No changes detected to process."})

        ALLOWED_COLUMNS = ["genre", "composition_name", "track_name", "composer", "performer"]

        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            
            for change in payload_changes:
                track_id = change.get("track_id")
                field = change.get("field")
                new_value = change.get("value")

                if field not in ALLOWED_COLUMNS:
                    continue

                query = f"UPDATE music_catalog SET {field} = ? WHERE track_id = ?;"
                cursor.execute(query, (new_value, track_id))

            conn.commit()
            return jsonify({"success": True, "message": f"Successfully committed {len(payload_changes)} adjustments."})
        except sqlite3.Error as e:
            return jsonify({"success": False, "error": f"Database mutation crashed: {str(e)}"}), 500
        finally:
            conn.close()

    return process_update()