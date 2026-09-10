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

    from services.music.music_catalog import read_catalog
    import json
    page = max(1, request.args.get('page', default=1, type=int))
    per_page = min(100, max(1, request.args.get('per_page', default=25, type=int)))
    try:
        sorts = json.loads(request.args.get('sort', '[]'))
        if not isinstance(sorts, list) or not all(isinstance(rule, dict) for rule in sorts):
            return jsonify(error="Invalid sorting parameters."), 400
    except ValueError:
        return jsonify(error="Invalid sorting parameters."), 400
    try:
        return jsonify(read_catalog(DB_PATH, page, per_page, request.args.get('search', ''),
                                    request.args.get('playlist', 'all'), sorts))
    except sqlite3.Error:
        return jsonify(error="The music catalog could not be read."), 500

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
            from services.music.music_catalog import tables
            tables(conn)
            
            for change in payload_changes:
                track_id = change.get("track_id")
                field = change.get("field")
                new_value = change.get("value")

                if field not in ALLOWED_COLUMNS:
                    continue

                query = f"UPDATE music_catalog SET {field} = ? WHERE track_id = ?;"
                cursor.execute(query, (new_value, track_id))
                cursor.execute("INSERT OR REPLACE INTO music_overrides VALUES (?, ?, ?)",
                               (track_id, field, new_value))

            conn.commit()
            return jsonify({"success": True, "message": f"Successfully committed {len(payload_changes)} adjustments."})
        except sqlite3.Error as e:
            return jsonify({"success": False, "error": f"Database mutation crashed: {str(e)}"}), 500
        finally:
            conn.close()

    return process_update()