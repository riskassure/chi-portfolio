import csv
import json
from pathlib import Path

def get_all_csv_files(raw_data_dir: Path):
    """
    Job 1: Scout the landing zone using modern pathlib objects.
    Using .glob() directly on the directory object.
    """
    # Returns a generator of Path objects for every CSV found
    return list(raw_data_dir.glob("*.csv"))


def convert_single_csv_to_json(csv_path: Path, processed_dir: Path, top_n=20):
    """
    Job 2: Transform the data.
    Takes a Path object, parses it, and creates a clean JSON target.
    """
    # Path objects have built-in properties like .stem (filename without extension)
    json_filename = f"{csv_path.stem}.json"
    json_path = processed_dir / json_filename  # The modern slash '/' operator joins paths!
    
    print(f"Parsing: {csv_path.name} ➡️ {json_filename}")
    tracks_list = []
    
    try:
        with csv_path.open(mode='r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            
            for index, row in enumerate(csv_reader):
                if index >= top_n:
                    break
                tracks_list.append(dict(row))
                
        with json_path.open(mode='w', encoding='utf-8') as json_file:
            json.dump(tracks_list, json_file, indent=4, ensure_ascii=False)
            
        print(f"🚀 Success! Extracted {len(tracks_list)} tracks.\n")
        return True
        
    except Exception as e:
        print(f"❌ Error converting {csv_path.name}: {e}\n")
        return False


def run_pipeline(top_n_tracks=20):
    """
    The Orchestrator / Controller:
    Coordinates pathing using Path.resolve() and manages the execution flow.
    """
    # Path(__file__).resolve() gives the absolute path of this script file
    script_dir = Path(__file__).resolve().parent
    
    # Modern path chaining using parent and the slash '/' operator
    raw_dir = script_dir.parent / "data" / "raw"
    processed_dir = script_dir.parent / "data" / "processed"
    
    # 1. Gather the target files
    csv_files = get_all_csv_files(raw_dir)
    
    if not csv_files:
        print(f"⚠️ No CSV files discovered inside: {raw_dir}")
        return
        
    print(f"📂 Modern Pipeline found {len(csv_files)} playlist(s) to process.\n")
    
    # 2. Map the work across our specialized converter function
    success_count = 0
    for file_path in csv_files:
        if convert_single_csv_to_json(file_path, processed_dir, top_n=top_n_tracks):
            success_count += 1
            
    print(f"🏁 Pipeline Complete! Successfully built {success_count}/{len(csv_files)} JSON payloads.")


if __name__ == "__main__":
    run_pipeline(top_n_tracks=20)