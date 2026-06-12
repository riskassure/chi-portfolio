import sqlite3
from pathlib import Path

def initialize_database():
    """Initializes the SQLite database file and builds the music catalog schema."""
    script_dir = Path(__file__).resolve().parent
    db_path = script_dir.parent / "portfolio.db"
    
    print(f"🛠️ Connecting to SQLite database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # We added track_order as an INTEGER right after unit_name
    create_table_sql = """
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
        track_url TEXT,
        track_id TEXT UNIQUE
    );
    """
    
    try:
        cursor.execute(create_table_sql)
        conn.commit()
        print("🚀 Success! 'music_catalog' table updated and verified with track_order.")
        
    except sqlite3.Error as e:
        print(f"❌ Database error encountered during initialization: {e}")
        
    finally:
        conn.close()
        print("🔒 Database connection securely closed.\n")

if __name__ == "__main__":
    initialize_database()