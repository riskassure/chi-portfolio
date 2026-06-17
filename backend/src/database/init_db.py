import sqlite3
import sys
# Add parent directory to path so python can find config.py
sys.path.append(str(sys.path[0] + '/..'))
from config import DB_PATH  # Simple, elegant import!

def initialize_database():
    print(f"Connecting to SQLite database at: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # 1. Drop existing production catalogs if they exist to ensure a clean build
    print("Dropping old production catalog tables...")
    cursor.execute("DROP TABLE IF EXISTS music_catalog;")
    cursor.execute("DROP TABLE IF EXISTS photography_catalog;")
    
    # 2. Re-create pristine production music schema
    create_music_table = """
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
    
    # 3. Re-create pristine production photography schema
    create_photo_table = """
    CREATE TABLE photography_catalog (
        image_id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        location_name TEXT,
        latitude REAL,
        longitude REAL,
        is_currently_displayed BOOLEAN DEFAULT 0,
        last_displayed_date TEXT,
        display_count INTEGER DEFAULT 0
    );
    """
    
    try:
        print("Creating music catalog table...")
        cursor.execute(create_music_table)
        
        print("Creating photography catalog table...")
        cursor.execute(create_photo_table)
        
        conn.commit()
        print("🚀 Success! All production catalog tables cleanly re-created.")
    except sqlite3.Error as e:
        print(f"❌ Database error encountered during initialization: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()