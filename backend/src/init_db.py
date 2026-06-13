import sqlite3
from pathlib import Path

def initialize_database():
    script_dir = Path(__file__).resolve().parent
    db_path = script_dir.parent / "portfolio.db"
    
    print(f"Connecting to SQLite database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Drop existing production catalog if it exists to ensure a clean build
    print("Dropping old production catalog tables...")
    cursor.execute("DROP TABLE IF EXISTS music_catalog;")
    
    # 2. Re-create pristine production schema with explicit classical columns
    create_prod_table = """
    CREATE TABLE music_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        spotify_playlist TEXT,
        genre TEXT,
        composition_name TEXT,
        unit_name TEXT,
        track_order INTEGER,
        track_name TEXT NOT NULL,
        composer TEXT,
        performer TEXT,
        album_name TEXT,
        release_date TEXT,
        duration_string TEXT,
        popularity INTEGER,
        track_id TEXT UNIQUE
    );
    """
    
    try:
        cursor.execute(create_prod_table)
        conn.commit()
        print("🚀 Success! Production catalog table cleanly re-created.")
    except sqlite3.Error as e:
        print(f"❌ Database error encountered during initialization: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()