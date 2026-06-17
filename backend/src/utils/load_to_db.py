import csv
import sqlite3
import re
import sys
sys.path.append(str(sys.path[0] + '/..'))
from config import DB_PATH, MUSIC_RAW_DIR

def run_etl_pipeline():
    csv_files = list(MUSIC_RAW_DIR.glob("*.csv"))
    if not csv_files:
        print(f"⚠️ No CSV source files discovered inside: {MUSIC_RAW_DIR}")
        return
        
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # -------------------------------------------------------------
        # PHASE 1: EXTRACT & LOAD (Strict 1:1 Staging Reset)
        # -------------------------------------------------------------
        print("Dropping and re-creating 1:1 staging table...")
        cursor.execute("DROP TABLE IF EXISTS stg_spotify_import;")
        
        cursor.execute("""
            CREATE TABLE stg_spotify_import (
                playlist_name TEXT,
                track_name TEXT,
                artist_names TEXT,
                album_name TEXT,
                release_date TEXT,
                duration_ms INTEGER,
                popularity INTEGER,
                track_uri TEXT
            );
        """)
        
        staging_insert_sql = """
        INSERT INTO stg_spotify_import (
            playlist_name, track_name, artist_names, album_name, 
            release_date, duration_ms, popularity, track_uri
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        
        total_staged = 0
        for file_path in csv_files:
            playlist_tag = re.sub(r'[-_]', ' ', file_path.stem).title()
            playlist_count = 0
            
            with file_path.open(mode='r', encoding='utf-8-sig') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    try: pop = int(row.get("Popularity", 0))
                    except ValueError: pop = 0
                    try: dur = int(row.get("Duration (ms)", 0))
                    except ValueError: dur = 0
                    
                    record = (
                        playlist_tag,
                        row.get("Track Name", "Unknown Track"),
                        row.get("Artist Name(s)", "Unknown"),
                        row.get("Album Name", "Unknown Album"),
                        row.get("Release Date", "Unknown Date"),
                        dur, pop, 
                        row.get("Track URI", "")
                    )
                    cursor.execute(staging_insert_sql, record)
                    playlist_count += 1
                    total_staged += 1
            print(f"   📥 Loaded {playlist_count} raw rows from: {file_path.name}")
            
        print(f"🔹 Phase 1 Complete. Staging contains {total_staged} raw rows.")

        # -------------------------------------------------------------
        # PHASE 2: TRANSFORM & MERGE INTO PRODUCTION (With Inverted Naming Fallback)
        # -------------------------------------------------------------
        print("\n⚙️ Running transformation algorithms over raw staging data...")
        
        cursor.execute("SELECT playlist_name, track_name, artist_names, album_name, release_date, duration_ms, popularity, track_uri FROM stg_spotify_import;")
        staged_rows = cursor.fetchall()
        
        prod_insert_sql = """
        INSERT INTO music_catalog (
            track_id, track_name, composition_name, unit_name, composer, performer, 
            album_name, release_date, duration_string, popularity, spotify_playlist
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(track_id) DO UPDATE SET
            popularity = excluded.popularity;
        """
        
        new_tracks_count = 0
        for row in staged_rows:
            playlist_name, raw_track_name, raw_artists, album_name, release_date, duration_ms, popularity, raw_uri = row
            
            clean_track_id = raw_uri.split(":")[-1] if raw_uri else None
            if not clean_track_id:
                continue 
                
            # Colon Parsing Rule: Track Name -> Composition vs. Unit 🎼
            if ":" in raw_track_name:
                title_parts = raw_track_name.split(":", 1)
                composition_name = title_parts[0].strip()
                unit_name = title_parts[1].strip()
            else:
                composition_name = raw_track_name.strip()
                unit_name = ""

            # Semicolon Parsing Rule: Artist Name(s) -> Composer vs. Performer 🔎
            if ";" not in raw_artists:
                composer = raw_artists.strip()
                performer = "Solo / Unspecified"
            else:
                parts = raw_artists.split(";", 1)
                composer = parts[0].strip()
                performer = parts[1].strip()
                
            # Time Rule: Convert Milliseconds to MM:SS
            tot_seconds = duration_ms // 1000
            mins = tot_seconds // 60
            secs = tot_seconds % 60
            duration_string = f"{mins:02d}:{secs:02d}"
            
            cursor.execute(prod_insert_sql, (
                clean_track_id, raw_track_name, composition_name, unit_name,
                composer, performer, album_name, release_date, duration_string,
                popularity, playlist_name
            ))
            
            if cursor.rowcount == 1:
                new_tracks_count += 1
                
        conn.commit()
        print(f"✨ Phase 2 Complete! {new_tracks_count} parsed records integrated into catalog.")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ Pipeline transaction rolled back due to error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_etl_pipeline()