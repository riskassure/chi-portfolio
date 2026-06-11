import csv
import json
import re
from pathlib import Path

def get_all_csv_files(raw_data_dir: Path):
    """Job 1: Scout the landing zone for CSV files."""
    return list(raw_data_dir.glob("*.csv"))


def convert_single_csv_to_json(csv_path: Path, processed_dir: Path, top_n=20):
    """
    Job 2: Parse a single CSV, inject the playlist tag, 
    AND save it as an individual JSON file for future DB use.
    """
    json_filename = f"{csv_path.stem}.json"
    json_path = processed_dir / json_filename
    
    playlist_tag = re.sub(r'[-_]', ' ', csv_path.stem).title()
    tracks_list = []
    
    try:
        with csv_path.open(mode='r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for index, row in enumerate(csv_reader):
                if index >= top_n:
                    break
                track_data = dict(row)
                track_data["Spotify Playlist"] = playlist_tag
                tracks_list.append(track_data)
                
        # Write individual file (Great for future DB ingestion!)
        with json_path.open(mode='w', encoding='utf-8') as json_file:
            json.dump(tracks_list, json_file, indent=4, ensure_ascii=False)
            
        print(f"📄 Saved individual file: {json_filename} ({len(tracks_list)} tracks)")
        return tracks_list # Return the data so the orchestrator can collect it
        
    except Exception as e:
        print(f"❌ Error processing {csv_path.name}: {e}")
        return []


def run_pipeline(top_n_tracks=20):
    """
    The Orchestrator: Saves individual files for the future DB,
    and aggregates them into one master file for today's frontend.
    """
    script_dir = Path(__file__).resolve().parent
    raw_dir = script_dir.parent / "data" / "raw"
    processed_dir = script_dir.parent / "data" / "processed"
    
    csv_files = get_all_csv_files(raw_dir)
    
    if not csv_files:
        print(f"⚠️ No CSV files discovered inside: {raw_dir}")
        return
        
    print(f"📂 Pipeline found {len(csv_files)} playlist(s) to process.\n")
    
    master_tracks_list = []
    
    # 1. Process individual files and accumulate master list simultaneously
    for file_path in csv_files:
        playlist_tracks = convert_single_csv_to_json(file_path, processed_dir, top_n=top_n_tracks)
        master_tracks_list.extend(playlist_tracks)
        
    # 2. Write out the master file for the frontend search/scroll engine
    master_json_path = processed_dir / "all_playlists.json"
    
    try:
        with master_json_path.open(mode='w', encoding='utf-8') as json_file:
            json.dump(master_tracks_list, json_file, indent=4, ensure_ascii=False)
            
        print(f"\n🚀 Master file compiled successfully: {master_json_path.name}")
        print(f"🏁 Complete! {len(master_tracks_list)} total tracks processed across both architectures.")
    except Exception as e:
        print(f"❌ Error writing master JSON file: {e}")


if __name__ == "__main__":
    run_pipeline(top_n_tracks=20)