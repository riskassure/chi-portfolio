import csv
import sqlite3
import re
from pathlib import Path

def run_etl_pipeline():
    script_dir = Path(__file__).resolve().parent
    raw_dir = script_dir.parent / "data" / "raw"
    db_path = script_dir.parent / "portfolio.db"
    
    # Scout for source files
    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        print(f"⚠️ No CSV source files discovered inside: {raw_dir}")
        return
        
    print(f"🔗 Establishing connection to database file...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # --- PHASE 1: TRUNCATE STAGING LAYER ---
        print("🧹 Cleaning out the staging landing zone...")
        cursor.execute("DELETE FROM stg_spotify_import;")
        
        # --- PHASE 2: INGEST RAW DATA TO STAGING ---
        staging_insert_sql = """
        INSERT INTO stg_spotify_import (
            spotify_playlist, track_name, artist_composer, album_name,
            release_date, duration_ms, popularity, track_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        
        total_staged = 0
        for file_path in csv_files:
            # Clean up the filename to make a beautiful playlist display name
            playlist_tag = re.sub(r'[-_]', ' ', file_path.stem).title()
            playlist_count = 0
            
            with file_path.open(mode='r', encoding='utf-8-sig') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    try:
                        pop = int(row.get("Popularity", 0))
                    except ValueError: pop = 0
                    try:
                        dur = int(row.get("Duration (ms)", 0))
                    except ValueError: dur = 0
                        
                    # Extract and clean the Track ID from the Track URI string
                    raw_uri = row.get("Track URI", "")
                    clean_track_id = raw_uri.split(":")[-1] if raw_uri else None
                    
                    record = (
                        playlist_tag,
                        row.get("Track Name", "Unknown Track"),
                        row.get("Artist Name(s)", "Unknown Artist"),
                        row.get("Album Name", "Unknown Album"),
                        row.get("Release Date", "Unknown Date"),
                        dur, 
                        pop,
                        clean_track_id
                    )
                    cursor.execute(staging_insert_sql, record)
                    playlist_count += 1
                    total_staged += 1
            print(f"   📥 Staged {playlist_count} tracks from: {file_path.name}")
            
        print(f"🔹 Phase 1 & 2 complete. {total_staged} raw records sitting in staging.")

        # --- PHASE 3: THE DATABASE MERGE (Our Stored Procedure Pattern) ---
        print("\n⚙️ Executing master merge transaction...")
        
        # Step A: Insert brand new entities into production catalog
        merge_insert_sql = """
        INSERT INTO music_catalog (
            track_id, track_name, artist_composer, album_name, 
            release_date, duration_ms, popularity, spotify_playlist
        )
        SELECT 
            s.track_id, s.track_name, s.artist_composer, s.album_name, 
            s.release_date, s.duration_ms, s.popularity, s.spotify_playlist
        FROM stg_spotify_import s
        WHERE s.track_id NOT IN (SELECT track_id FROM music_catalog WHERE track_id IS NOT NULL)
          AND s.track_id IS NOT NULL 
          AND s.track_id != '';
        """
        cursor.execute(merge_insert_sql)
        new_tracks_count = cursor.rowcount
        
        # Step B: Update only fluid streaming metrics for rows that match existing IDs
        # Your curated columns (composition_name, genre, track_order) are completely left untouched!
        merge_update_sql = """
        UPDATE music_catalog
        SET popularity = (
            SELECT popularity FROM stg_spotify_import 
            WHERE stg_spotify_import.track_id = music_catalog.track_id 
            LIMIT 1
        )
        WHERE track_id IN (SELECT track_id FROM stg_spotify_import);
        """
        cursor.execute(merge_update_sql)
        
        # Commit the whole transaction safely
        conn.commit()
        print(f"✨ Phase 3 complete! Integrated {new_tracks_count} brand-new tracks into the catalog.")
        print("🔒 Data warehouse synchronization successfully closed.\n")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ Transaction rolled back due to failure: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_etl_pipeline()