import sqlite3
from flask import Flask, jsonify, request, session
from pathlib import Path

app = Flask(__name__)

# --- NEW: SESSION ENCRYPTION SECURITY CONFIGURATION ---
# In production, this would be a random string read from an environment variable.
app.secret_key = "classical_music_portfolio_secret_key_pass"

# --- ADD THESE TWO LINES FOR LOCAL CROSS-PORT COOKIE SUPPORT ---
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True # Required when SameSite is set to None

SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR.parent / "portfolio.db"

# Master password configuration (Easy to move to database/hashes later)
ADMIN_PASSWORD = "SuperSecretPassword123"


@app.after_request
def add_cors_headers(response):
    """Unified helper to handle CORS credentials mapping across endpoints safely."""
    # Note: To support session cookies with fetch requests, we must specify the exact origin
    # instead of a wildcard "*", and allow credentials to pass through.
    response.headers.add("Access-Control-Allow-Origin", "http://127.0.0.1:5500") # Adjust port if using Live Server
    response.headers.add("Access-Control-Allow-Credentials", "true")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    return response


@app.route("/api/login", methods=["POST", "OPTIONS"])
def login_admin():
    """Verifies incoming payload password and commits admin status to secure browser cookie."""
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    data = request.get_json() or {}
    password_attempt = data.get("password")

    if password_attempt == ADMIN_PASSWORD:
        session["is_admin"] = True
        return jsonify({"success": True, "message": "Authentication successful. Welcome Admin."})
    
    return jsonify({"success": False, "message": "Invalid credentials. Unauthorized access rejected."}), 401


@app.route("/api/logout", methods=["POST"])
def logout_admin():
    """Clears the session cookie context to safely revoke admin view rights."""
    session.pop("is_admin", None)
    return jsonify({"success": True, "message": "Logged out safely."})


@app.route("/api/session-check", methods=["GET"])
def check_session_status():
    """Probes current tracking state so UI knows whether to paint hidden control panels."""
    is_admin_active = session.get("is_admin", False)
    return jsonify({"is_admin": is_admin_active})


@app.route("/api/music", methods=["GET", "OPTIONS"])
def get_music_catalog():
    """Queries SQLite and streams a precise slice of the music catalog based on pagination metrics."""
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    if not DB_PATH.exists():
        return jsonify({"error": "Database warehouse file not discovered. Please run load_to_db.py first."}), 404

    try:
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=25, type=int)
        offset = (page - 1) * per_page

        conn = sqlite3.connect(DB_PATH)
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
        
        rows = cursor.fetchall()
        catalog_list = [dict(row) for row in rows]
        total_pages = (total_records + per_page - 1) // per_page
        
        payload = {
            "total_records": total_records,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "data": catalog_list
        }
        
        return jsonify(payload)

    except sqlite3.Error as e:
        return jsonify({"error": f"Database transaction failed: {str(e)}"}), 500
    finally:
        conn.close()


@app.route("/api/music/update", methods=["POST", "OPTIONS"])
def update_music_catalog():
    """Validates admin session, sanitizes inputs against a whitelist, and commits changes to SQLite."""
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    # 1. SECURITY CHECK: Verify the encrypted session cookie matches
    if not session.get("is_admin", False):
        return jsonify({"success": False, "message": "Unauthorized access rejected. Admin rights required."}), 403

    data = request.get_json() or {}
    payload_changes = data.get("changes", [])

    if not payload_changes:
        return jsonify({"success": True, "message": "No changes detected to process."})

    # Strict whitelist matching only the columns we want to allow editing on
    ALLOWED_COLUMNS = ["genre", "composition_name", "track_name", "composer", "performer"]

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 2. TRANSACTION UPDATE LOOP
        for change in payload_changes:
            track_id = change.get("track_id")
            field = change.get("field")
            new_value = change.get("value")

            # Safety guard: ignore fields not in our whitelist
            if field not in ALLOWED_COLUMNS:
                continue

            # Construct the query dynamically using safe parameter binding wrappers
            query = f"UPDATE music_catalog SET {field} = ? WHERE track_id = ?;"
            cursor.execute(query, (new_value, track_id))

        conn.commit() # Lock the modifications permanently into portfolio.db
        return jsonify({"success": True, "message": f"Successfully committed {len(payload_changes)} adjustments to the database."})

    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database mutation crashed: {str(e)}"}), 500
    finally:
        conn.close()


@app.route('/api/photography/current', methods=['GET', 'OPTIONS'])
def get_current_photos():
    """
    Fetches the photos currently marked for display from the database
    and returns them as a JSON payload for the frontend slideshow/gallery.
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    if not DB_PATH.exists():
        return jsonify({"status": "error", "message": "Database warehouse file not found."}), 404
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        # Query for the 3 photos currently active in the rotation
        cursor.execute("""
            SELECT image_id, file_path, title, location_name, latitude, longitude 
            FROM photography_catalog 
            WHERE is_currently_displayed = 1
            LIMIT 3;
        """)
        
        rows = cursor.fetchall()
        photos = [dict(row) for row in rows]
        
        return jsonify({
            "status": "success",
            "count": len(photos),
            "data": photos
        }), 200

    except sqlite3.Error as e:
        return jsonify({
            "status": "error",
            "message": f"Database transaction failed: {str(e)}"
        }), 500
    finally:
        conn.close()
    

@app.route("/api/photography/update", methods=["POST", "OPTIONS"])
def update_photography_catalog():
    """Validates admin session and updates photography metadata (location, coordinates)."""
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS preflight ok"}), 200

    # 1. SECURITY GUARDRAIL: Verify encrypted session cookie
    if not session.get("is_admin", False):
        return jsonify({"success": False, "message": "Unauthorized access rejected. Admin rights required."}), 403

    data = request.get_json() or {}
    image_id = data.get("image_id")
    location_name = data.get("location_name")
    
    # Handle numbers carefully, falling back to 0.0 if empty or invalid
    try:
        latitude = float(data.get("latitude", 0.0)) if data.get("latitude") else 0.0
        longitude = float(data.get("longitude", 0.0)) if data.get("longitude") else 0.0
    except ValueError:
        return jsonify({"success": False, "message": "Invalid coordinate formatting."}), 400

    if not image_id:
        return jsonify({"success": False, "message": "Missing image_id identifier."}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Safely bind variables to prevent SQL Injection
        cursor.execute("""
            UPDATE photography_catalog 
            SET location_name = ?, latitude = ?, longitude = ?
            WHERE image_id = ?;
        """, (location_name, latitude, longitude, image_id))
        
        conn.commit()
        return jsonify({"success": True, "message": "Photography catalog metadata successfully updated."})

    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database modification failed: {str(e)}"}), 500
    finally:
        conn.close()
        

if __name__ == "__main__":
    print("\nStarting Local Web App Gateway Server with Security Guardrails...")
    print("API Endpoint listening at: http://127.0.0.1:5000/api/music")
    print("Press CTRL+C to stop the application server wrapper.\n")
    app.run(host="127.0.0.1", port=5000, debug=True)