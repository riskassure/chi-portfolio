import sqlite3
import sys
# Add parent directory to path so python can find config.py
sys.path.append(str(sys.path[0] + '/..'))
from config import DB_PATH, PHOTO_TARGET_DIR

def auto_seed_photography():
    if not PHOTO_TARGET_DIR.exists():
        print(f"❌ Could not find frontend folder at: {PHOTO_TARGET_DIR}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Double check that the table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS photography_catalog (
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
    """)

    # Track structural assets
    seeded_count = 0
    active_count = 0
    
    print("🌱 Scanning assets and auto-seeding database...")
    print("-" * 60)

    # Use pathlib (.glob) to cleanly match files instead of legacy os.listdir
    for file_path in PHOTO_TARGET_DIR.glob("*.webp"):
        filename = file_path.name
        
        # Reconstruct the exact path string the frontend will need
        db_file_path = f"images/photography/{filename}"
        
        # Generate a clean human-readable title from the snake_case filename
        clean_title = file_path.stem.replace("_", " ").title()
        
        # Set the first 3 files to active (1), the rest to inactive (0)
        if active_count < 3:
            is_active = 1
            active_count += 1
        else:
            is_active = 0
        
        try:
            # INSERT OR IGNORE avoids creating duplicates if you run this twice
            cursor.execute("""
            INSERT OR IGNORE INTO photography_catalog 
            (file_path, title, location_name, latitude, longitude, is_currently_displayed)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (db_file_path, clean_title, "Unknown Location", 0.0, 0.0, is_active))
            
            if cursor.rowcount > 0:
                status = "ACTIVE" if is_active else "PENDING"
                print(f"✅ Added: {db_file_path} ➡️ Title: '{clean_title}' [{status}]")
                seeded_count += 1
            else:
                # If it already exists, track that we still accounted for an active record slot
                if is_active:
                    pass 
                    
        except Exception as e:
            print(f"❌ Error inserting {filename}: {str(e)}")

    # Commit changes and close down cleanly
    conn.commit()
    conn.close()
    
    print("-" * 60)
    print(f"🎉 Success! Processed files inside target asset directory.")
    print(f"   Newly Seeded: {seeded_count} records.")

if __name__ == "__main__":
    auto_seed_photography()