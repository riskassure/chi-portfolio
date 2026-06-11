import csv
import json
import os

def convert_playlist_csv_to_json(csv_filename, json_filename, top_n=20):
    """
    Reads a Spotify playlist CSV, extracts ALL columns for the top N tracks,
    and saves them as a structured JSON file for inspection and downstream use.
    """
    tracks_list = []
    
    # Establish absolute paths based on your clean backend architecture
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.abspath(os.path.join(script_dir, '..', 'data', 'raw', csv_filename))
    json_path = os.path.abspath(os.path.join(script_dir, '..', 'data', 'processed', json_filename))
    
    print(f"Reading raw data from: {csv_path}")
    
    try:
        with open(csv_path, mode='r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            
            for index, row in enumerate(csv_reader):
                # The adjustable row ceiling
                if index >= top_n:
                    break
                
                # COMPROMISE MAGIC: Convert the entire CSV row dictionary 
                # directly to ingest all available columns automatically.
                track_data = dict(row)
                tracks_list.append(track_data)
                
        with open(json_path, mode='w', encoding='utf-8') as json_file:
            json.dump(tracks_list, json_file, indent=4, ensure_ascii=False)
            
        print(f"🚀 Success! Captured ALL columns for the top {len(tracks_list)} tracks.")
        print(f"Inspected downstream file saved to: {json_path}")
        
    except FileNotFoundError:
        print(f"❌ Error: '{csv_filename}' not found in backend/data/raw/")

if __name__ == "__main__":
    # Update 'jazz-classics.csv' to match your actual file name!
    # If you want 50 songs later, just change the 20 to 50 below.
    convert_playlist_csv_to_json("jazz-classics.csv", "jazz-classics.json", top_n=20)