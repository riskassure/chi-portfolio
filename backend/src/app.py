import sqlite3
from flask import Flask, jsonify
from pathlib import Path

app = Flask(__name__)

# Locate the portfolio database relative to this script file
SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR.parent / "portfolio.db"

@app.route("/api/music", methods=["GET"])
def get_music_catalog():
    """Connects to SQLite and streams the production music catalog down to the frontend grid."""
    if not DB_PATH.exists():
        return jsonify({"error": "Database warehouse file not discovered. Please run load_to_db.py first."}), 404

    try:
        conn = sqlite3.connect(DB_PATH)
        # Allows accessing columns by name like row['composer']
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        # Pull all tracks out of the production music catalog
        cursor.execute("""
            SELECT spotify_playlist, genre, composition_name, unit_name, 
                   track_name, composer, performer, album_name, 
                   release_date, duration_string, popularity, track_id 
            FROM music_catalog;
        """)
        
        rows = cursor.fetchall()
        
        # Convert SQLite row objects into a clean list of standard Python dictionaries
        catalog_list = [dict(row) for row in rows]
        
        # Wrap the list in a secure JSON response payload
        response = jsonify(catalog_list)
        
        # Enable CORS (Cross-Origin Resource Sharing) headers so your frontend page 
        # can safely talk to the backend server while developing locally
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    except sqlite3.Error as e:
        return jsonify({"error": f"Database transaction failed: {str(e)}"}), 500
    finally:
        conn.close()

if __name__ == "__main__":
    print("\n🚀 Starting Local Web App Gateway Server...")
    print(f"📡 API Endpoint listening at: http://127.0.0.1:5000/api/music")
    print("Press CTRL+C to stop the application server wrapper.\n")
    # Run the server locally on port 5000
    app.run(host="127.0.0.1", port=5000, debug=True)