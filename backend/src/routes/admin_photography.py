import sqlite3
import math
import sys
from datetime import datetime
from flask import Blueprint, jsonify, request

# Tell Python to look up one folder level to find config.py
sys.path.append(str(sys.path[0] + '/..'))
from services import gallery_settings
from routes.travel import editable
from config import DB_PATH          

photography_bp = Blueprint('photography_bp', __name__)

@photography_bp.route('/api/photography/settings', methods=['GET', 'POST'])
def photography_settings():
    try:
        if request.method == 'POST':
            if not editable() or request.headers.get('Origin') != request.host_url.rstrip('/'):
                return jsonify(error='Sign in on the local website to save gallery settings.'), 403
            body = request.get_json(silent=True)
            if not isinstance(body, dict):
                return jsonify(error='Expected gallery settings.'), 400
            gallery_settings.save(body.get('settings'), body.get('revision'))
        settings, revision = gallery_settings.read()
        return jsonify(settings=settings, revision=revision, editable=editable())
    except gallery_settings.Conflict as error:
        return jsonify(error=str(error)), 409
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except OSError:
        return jsonify(error='Could not read or save gallery settings.'), 503


@photography_bp.route('/api/photography/current', methods=['GET', 'OPTIONS'])
def get_current_photos():
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                image_id, 
                file_path, 
                COALESCE(title, 'Untitled Landscape') AS title, 
                COALESCE(location_name, 'Unknown Location') AS location_name, 
                COALESCE(latitude, 0.0) AS latitude, 
                COALESCE(longitude, 0.0) AS longitude, 
                is_currently_displayed 
            FROM photography_catalog 
            ORDER BY COALESCE(is_currently_displayed, 0) DESC, image_id ASC
            LIMIT ?;
        """, (gallery_settings.read()[0]['photo_count'],))
        
        photos = [dict(row) for row in cursor.fetchall()]
        return jsonify({"status": "success", "count": len(photos), "data": photos}), 200
    except sqlite3.Error as e:
        return jsonify({"status": "error", "message": f"Database failed: {str(e)}"}), 500
    finally:
        conn.close()


@photography_bp.route('/api/photography/rotate', methods=['POST', 'OPTIONS'])
def rotate_catalog_pool():
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200
        
    # Rotation uses the saved preference, never a stale browser default.
    limit = gallery_settings.read()[0]['photo_count']

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        # Safe 5-Priority rules query logic
        cursor.execute("""
            SELECT image_id FROM photography_catalog 
            ORDER BY 
                COALESCE(display_count, 0) ASC,
                COALESCE(last_displayed_date, '1970-01-01 00:00:00') ASC,
                COALESCE(is_currently_displayed, 0) ASC,
                CASE WHEN COALESCE(location_name, '') = 'Unknown Location' THEN 0 ELSE 1 END,
                COALESCE(title, '') ASC
            LIMIT ?;
        """, (limit,))
        
        target_ids = [row['image_id'] for row in cursor.fetchall()]
        
        # Absolute structural fallback in case data-states are empty
        if not target_ids:
            cursor.execute("SELECT image_id FROM photography_catalog ORDER BY image_id ASC LIMIT ?;", (limit,))
            target_ids = [row['image_id'] for row in cursor.fetchall()]
        
        if target_ids:
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Clear previous display visibility states
            cursor.execute("UPDATE photography_catalog SET is_currently_displayed = 0;")
            
            # Write flags onto targeted sequence IDs
            for img_id in target_ids:
                cursor.execute("""
                    UPDATE photography_catalog 
                    SET is_currently_displayed = 1,
                        last_displayed_date = ?,
                        display_count = display_count + 1
                    WHERE image_id = ?;
                """, (now_str, img_id))
            conn.commit()

        # Gather final output results to route right back to frontend render array
        cursor.execute("""
            SELECT 
                image_id, 
                file_path, 
                COALESCE(title, 'Untitled Landscape') AS title, 
                COALESCE(location_name, 'Unknown Location') AS location_name, 
                COALESCE(latitude, 0.0) AS latitude, 
                COALESCE(longitude, 0.0) AS longitude, 
                is_currently_displayed
            FROM photography_catalog 
            WHERE is_currently_displayed = 1
            ORDER BY image_id ASC;
        """)
        photos = [dict(row) for row in cursor.fetchall()]
            
        return jsonify({
            "status": "success", 
            "count": len(photos),
            "data": photos
        }), 200
    except sqlite3.Error as e:
        print(f"\n❌ BACKEND CRASH EXCEPTION LOGGED:\n{str(e)}\n")
        return jsonify({"status": "error", "message": f"Rotation engine failed: {str(e)}"}), 500
    finally:
        conn.close()


@photography_bp.route("/api/photography/update", methods=["POST", "OPTIONS"])
def update_photography_catalog():
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    from app import admin_required

    @admin_required
    def process_update():
        data = request.get_json() or {}
        if not isinstance(data, dict):
            return jsonify(success=False, message='Invalid photo details.'), 400
        image_id = data.get("image_id")
        location_name = data.get("location_name")
        title = data.get('title')
        if 'title' in data and (not isinstance(title, str) or not title.strip() or len(title) > 200):
            return jsonify(success=False, message='A title of 1 to 200 characters is required.'), 400
        if not isinstance(location_name, str) or len(location_name) > 200:
            return jsonify(success=False, message='Location must be at most 200 characters.'), 400
        
        try:
            latitude = float(data.get("latitude", 0.0)) if data.get("latitude") else 0.0
            longitude = float(data.get("longitude", 0.0)) if data.get("longitude") else 0.0
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Invalid coordinate formatting."}), 400

        if not math.isfinite(latitude) or not math.isfinite(longitude) or abs(latitude) > 90 or abs(longitude) > 180:
            return jsonify(success=False, message='Latitude must be between -90 and 90, longitude between -180 and 180.'), 400

        if not image_id:
            return jsonify({"success": False, "message": "Missing image_id identifier."}), 400

        conn = None
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE photography_catalog 
                SET location_name = ?, latitude = ?, longitude = ?, title = COALESCE(?, title)
                WHERE image_id = ?;
            """, (location_name, latitude, longitude, title, image_id))

            if cursor.rowcount != 1:
                conn.rollback()
                return jsonify(success=False, message='Photo not found.'), 404
            
            conn.commit()
            return jsonify({"success": True, "message": "Photography metadata successfully updated."})
        except sqlite3.Error as e:
            return jsonify({"success": False, "error": f"Database modification failed: {str(e)}"}), 500
        finally:
            if conn is not None:
                conn.close()

    return process_update()
