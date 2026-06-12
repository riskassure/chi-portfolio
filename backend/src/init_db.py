import sqlite3
from pathlib import Path

def initialize_database():
    """Initializes the SQLite database with staging and production layers."""
    script_dir = Path(__file__).resolve().parent
    db_path = script_dir.parent / "portfolio.db"
    
    print(f"🛠️ Connecting to SQLite database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Staging Table (Landing zone - flat structure, no unique constraints)
    create_staging_table = """
    CREATE TABLE IF NOT EXISTS stg_spotify_import (
        track_id TEXT,
        track_name TEXT,
        artist_composer TEXT,
        album_name TEXT,
        release_date TEXT,
        duration_ms INTEGER,
        popularity INTEGER,
        spotify_playlist TEXT
    );
    """
    
    # 2. Production Table (The Golden Record - holds your manual curation safely)
    create_prod_table = """
    CREATE TABLE IF NOT EXISTS music_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        spotify_playlist TEXT,
        genre TEXT,
        composition_name TEXT,
        unit_name TEXT,
        track_order INTEGER,
        track_name TEXT NOT NULL,
        artist_composer TEXT,
        album_name TEXT,
        release_date TEXT,
        duration_ms INTEGER,
        popularity INTEGER,
        track_id TEXT UNIQUE
    );
    """
    
    try:
        cursor.execute(create_staging_table)
        cursor.execute(create_prod_table)
        conn.commit()
        print("🚀 Success! Both 'stg_spotify_import' and 'music_catalog' tables are verified.")
        
    except sqlite3.Error as e:
        print(f"❌ Database error encountered during initialization: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()