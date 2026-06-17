import sqlite3
import sys
from flask import Blueprint, jsonify, request

# 1. Tell Python to look up one folder level (out of routes/ into src/) to find config.py
sys.path.append(str(sys.path[0] + '/..'))
from config import DB_PATH          # 📥 Direct pull from source of truth!

photography_bp = Blueprint('photography_bp', __name__)

@photography_bp.route('/api/photography/current', methods=['GET', 'OPTIONS'])
def get_current_photos():
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT image_id, file_path, title, location_name, latitude, longitude 
            FROM photography_catalog 
            WHERE is_currently_displayed = 1
            LIMIT 3;
        """)
        
        photos = [dict(row) for row in cursor.fetchall()]
        return jsonify({"status": "success", "count": len(photos), "data": photos}), 200
    except sqlite3.Error as e:
        return jsonify({"status": "error", "message": f"Database failed: {str(e)}"}), 500
    finally:
        conn.close()

@photography_bp.route("/api/photography/update", methods=["POST", "OPTIONS"])
def update_photography_catalog():
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    # 📥 IMPORT IT LOCALLY HERE INSIDE THE FUNCTION INTERIOR:
    from app import admin_required

    @admin_required
    def process_update():
        data = request.get_json() or {}
        image_id = data.get("image_id")
        location_name = data.get("location_name")
        
        try:
            latitude = float(data.get("latitude", 0.0)) if data.get("latitude") else 0.0
            longitude = float(data.get("longitude", 0.0)) if data.get("longitude") else 0.0
        except ValueError:
            return jsonify({"success": False, "message": "Invalid coordinate formatting."}), 400

        if not image_id:
            return jsonify({"success": False, "message": "Missing image_id identifier."}), 400

        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE photography_catalog 
                SET location_name = ?, latitude = ?, longitude = ?
                WHERE image_id = ?;
            """, (location_name, latitude, longitude, image_id))
            
            conn.commit()
            return jsonify({"success": True, "message": "Photography metadata successfully updated."})
        except sqlite3.Error as e:
            return jsonify({"success": False, "error": f"Database modification failed: {str(e)}"}), 500
        finally:
            conn.close()

    return process_update()