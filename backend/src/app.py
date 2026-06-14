import sqlite3
from flask import Flask, jsonify, request
from pathlib import Path

app = Flask(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR.parent / "portfolio.db"

@app.route("/api/music", methods=["GET"])
def get_music_catalog():
    """Queries SQLite and streams a precise slice of the music catalog based on pagination metrics."""
    if not DB_PATH.exists():
        return jsonify({"error": "Database warehouse file not discovered. Please run load_to_db.py first."}), 404

    try:
        # Read parameters from the browser URL (e.g., /api/music?page=2&per_page=25)
        # Default to Page 1 and 25 items per page if the parameters aren't supplied
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=25, type=int)
        
        # Calculate how many rows SQLite needs to skip to find the target page
        offset = (page - 1) * per_page

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        # 1. Query the database to find the absolute total row count
        cursor.execute("SELECT COUNT(*) FROM music_catalog;")
        total_records = cursor.fetchone()[0]
        
        # 2. Extract ONLY the precise 25-record slice needed for this page
        cursor.execute("""
            SELECT spotify_playlist, genre, composition_name, unit_name, 
                   track_name, composer, performer, album_name, 
                   release_date, duration_string, popularity, track_id 
            FROM music_catalog
            LIMIT ? OFFSET ?;
        """, (per_page, offset))
        
        rows = cursor.fetchall()
        catalog_list = [dict(row) for row in rows]
        
        # Calculate absolute total pages using integer ceiling division math
        total_pages = (total_records + per_page - 1) // per_page
        
        # Bundle our data rows and pagination control properties inside a single dictionary envelope
        payload = {
            "total_records": total_records,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "data": catalog_list
        }
        
        response = jsonify(payload)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    except sqlite3.Error as e:
        return jsonify({"error": f"Database transaction failed: {str(e)}"}), 500
    finally:
        conn.close()

if __name__ == "__main__":
    print("\nStarting Local Web App Gateway Server...")
    print("API Endpoint listening at: http://127.0.0.1:5000/api/music")
    print("Press CTRL+C to stop the application server wrapper.\n")
    app.run(host="127.0.0.1", port=5000, debug=True)