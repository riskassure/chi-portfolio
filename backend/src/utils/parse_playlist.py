import csv
import json
import re
import sys
from pathlib import Path

# Tell Python to look up one folder level (out of utils/ into src/) to find config.py
sys.path.append(str(sys.path[0] + '/..'))
from config import MUSIC_RAW_DIR, MUSIC_PROCESSED_DIR

def get_all_csv_files(raw_data_dir: Path):
    """Job 1: Scout the landing zone for CSV files."""
    return list(raw_data_dir.glob("*.csv"))


def extract_tracks_from_csv(csv_path: Path, top_n=20):
    """
    Job 2: Parse a single CSV, clean it, inject the playlist tag,
    SORT all tracks by global Popularity, and return the top N.
    """
    playlist_tag = re.sub(r'[-_]', ' ', csv_path.stem).title()
    all_playlist_tracks = []
    
    try:
        with csv_path.open(mode='r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            
            for row in csv_reader:
                track_data = dict(row)
                track_data["Spotify Playlist"] = playlist_tag
                
                try:
                    track_data["Popularity"] = int(track_data.get("Popularity", 0))
                except ValueError:
                    track_data["Popularity"] = 0
                    
                all_playlist_tracks.append(track_data)
        
        all_playlist_tracks.sort(key=lambda x: x["Popularity"], reverse=True)
        top_tracks = all_playlist_tracks[:top_n]
        
        print(f"🔥 Extracted Top {len(top_tracks)} MOST POPULAR tracks from: {csv_path.name}")
        return top_tracks
        
    except Exception as e:
        print(f"❌ Error reading {csv_path.name}: {e}")
        return []


def run_pipeline(top_n_tracks=20):
    """
    The Orchestrator: Saves individual files and compiles the 
    consolidated master file, both now sorted by track popularity.
    """
    csv_files = get_all_csv_files(MUSIC_RAW_DIR)
    
    if not csv_files:
        print(f"⚠️ No CSV files discovered inside: {MUSIC_RAW_DIR}")
        return
        
    print(f"📂 Pipeline running Popularity Sort across {len(csv_files)} playlist(s).\n")
    
    master_tracks_list = []
    
    for file_path in csv_files:
        playlist_tracks = extract_tracks_from_csv(file_path, top_n=top_n_tracks)
        master_tracks_list.extend(playlist_tracks)
        
        json_filename = f"{file_path.stem}.json"
        try:
            with (MUSIC_PROCESSED_DIR / json_filename).open(mode='w', encoding='utf-8') as ind_file:
                json.dump(playlist_tracks, ind_file, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error writing individual JSON {json_filename}: {e}")
        
    master_json_path = MUSIC_PROCESSED_DIR / "all_playlists.json"
    try:
        with master_json_path.open(mode='w', encoding='utf-8') as json_file:
            json.dump(master_tracks_list, json_file, indent=4, ensure_ascii=False)
            
        print(f"\n🚀 Popularity-sorted Master file compiled: {master_json_path.name}")
        print(f"🏁 Complete! {len(master_tracks_list)} total tracks processed.")
    except Exception as e:
        print(f"❌ Error writing master JSON file: {e}")


if __name__ == "__main__":
    run_pipeline(top_n_tracks=20)