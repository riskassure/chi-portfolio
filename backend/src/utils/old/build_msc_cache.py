# backend/src/utils/math/build_msc_cache.py

import os
import json
import csv
import time
import urllib.request
import urllib.error

# Dynamically locate paths based on this file's location
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))

# Targets your desired folder structure: backend/data/math/msc_cache.csv
DATA_MATH_DIR = os.path.join(BACKEND_DIR, "data", "math")
CSV_CACHE_PATH = os.path.join(DATA_MATH_DIR, "msc_cache.csv")

def fetch_from_api(code):
    """Queries the zbMATH public API for a single classification's description."""
    # Ensure code is completely stripped and uppercase for the API endpoint structure
    clean_code = code.strip().upper()
    url = f"https://api.zbmath.org/v1/msc/{clean_code}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'PortfolioMscBuilder/1.0'})
        with urllib.request.urlopen(req) as response:
            raw_data = response.read().decode('utf-8')
            data = json.loads(raw_data)
            return data.get('description', None)
    except urllib.error.HTTPError as e:
        # Trace exactly what the web server complains about if it fails
        return None
    except Exception:
        return None

def load_local_csv_cache():
    """Reads the CSV cache file from backend/data/math/ if it exists."""
    cache = {}
    if os.path.exists(CSV_CACHE_PATH):
        print(f"📖 Cache file found! Reading from: backend/data/math/msc_cache.csv")
        with open(CSV_CACHE_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip CSV header row
            for row in reader:
                if len(row) >= 2:
                    cache[row[0].strip().upper()] = row[1].strip()
    else:
        print("📁 No local CSV cache file exists yet. Generating folders...")
    return cache

def save_local_csv_cache(cache_data):
    """Forces creation of backend/data/math/ and writes the CSV mapping."""
    if not os.path.exists(DATA_MATH_DIR):
        print(f"🛠️ Creating missing directory pathway: {DATA_MATH_DIR}")
        os.makedirs(DATA_MATH_DIR)
        
    print(f"💾 Committing changes down to local file: {CSV_CACHE_PATH}")
    with open(CSV_CACHE_PATH, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["code", "description"])  # Header row
        for code, description in sorted(cache_data.items()):
            writer.writerow([code, description])

def sync_msc_descriptions(target_codes):
    """
    Checks local CSV file cache first. Fallback queries the API for missing items,
    and guarantees a local file is generated to hold the mappings.
    """
    local_cache = load_local_csv_cache()
    cache_updated = False
    
    # Standardize our targeted checking inputs to uppercase strings
    clean_targets = [c.strip().upper() for c in target_codes]
    missing_codes = [c for c in clean_targets if c not in local_cache]
    
    if not missing_codes:
        print("✅ All target codes are already accounted for in your CSV data cache.")
        return local_cache

    print(f"📡 Processing {len(missing_codes)} lookups across the web API layer...")
    
    for idx, code in enumerate(missing_codes, 1):
        print(f" 🌐 [{idx}/{len(missing_codes)}] Querying zbMATH API for code: {code}")
        description = fetch_from_api(code)
        
        if description:
            print(f"   📥 Found string: {description[:50]}...")
            local_cache[code] = description
            cache_updated = True
        else:
            print(f"   ❌ API endpoint returned empty for code: {code}")
            # Write a placeholder description string so it creates a line item 
            # and won't repeatedly slam the web API for dead links next time.
            local_cache[code] = "Classification Category Name Unavailable"
            cache_updated = True
            
        # Standard polite citizen internet pacing break
        time.sleep(0.2)
            
    # Forceful update check: Make sure a physical file is written down to backend/data/math
    save_local_csv_cache(local_cache)
    return local_cache

if __name__ == "__main__":
    print("🎬 Running Standalone MSC Cache Builder...")
    
    # These exact codes are actively indexed leaf nodes in the zbMATH REST API
    sample_codes = ["11G05", "14F05", "53C25"]
    
    resulting_map = sync_msc_descriptions(sample_codes)
    
    print("\n📊 Verification of final output metrics:")
    print(f"   Destination File Path Exists: {os.path.exists(CSV_CACHE_PATH)}")