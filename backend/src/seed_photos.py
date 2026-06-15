import os
import sqlite3

def auto_seed_photography():
    # Paths relative to backend/src/
    db_path = "../portfolio.db"
    photo_dir = "../../frontend/images/photography"
    
    if not os.path.exists(photo_dir):
        print(f"❌ Could not find frontend folder at: {photo_dir}")
        return

    # Connect to your SQLite database
    conn = sqlite3.connect(db_path)
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

    # Scan the frontend folder for the webp images you just converted
    seeded_count = 0
    active_count = 0
    
    print("🌱 Scanning assets and auto-seeding database...")
    print("-" * 60)

    for filename in os.listdir(photo_dir):
        if filename.endswith(".webp"):
            # Reconstruct the exact path string the frontend will need
            db_file_path = f"images/photography/{filename}"
            
            # Generate a clean human-readable title from the snake_case filename
            # e.g., "eastern_sierra.webp" -> "Eastern Sierra"
            clean_title = os.path.splitext(filename)[0].replace("_", " ").title()
            
            # To match our strategy: set the first 3 files to active (1), the rest to inactive (0)
            is_active = 1 if active_count < 3 else 0
            
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
                    if is_active:
                        active_count += 1
            except Exception as e:
                print(f"❌ Error inserting {filename}: {str(e)}")

    # Commit changes and close down cleanly
    conn.commit()
    conn.close()
    
    print("-" * 60)
    print(f"🎉 Success! Automatically seeded {seeded_count} records into your catalog.")
    print("   (The first 3 were marked active; you can easily tweak locations/coords in DB Browser later!)")

if __name__ == "__main__":
    auto_seed_photography()