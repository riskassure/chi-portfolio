# backend/src/utils/math/math_data_manager.py

import json
import urllib.request
import subprocess
from pathlib import Path

# Standardize path configurations via Pathlib
TARGET_DIR = Path(r"C:\Development\planetmath_data")

def get_repo_list():
    """Fetches relevant PlanetMath repo names from GitHub API."""
    print("🌐 Connecting to GitHub API to fetch repository map...")
    url = "https://api.github.com/orgs/planetmath/repos?per_page=100"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        return [repo['name'] for repo in data if repo['name'][:2].isdigit()]

def clone_repos(repo_names):
    """Clones missing repos using your system's git."""
    if not TARGET_DIR.exists():
        TARGET_DIR.mkdir(parents=True, exist_ok=True)
        
    print(f"📁 Target local folder: {TARGET_DIR}")
    cloned_count = 0
    
    for name in repo_names:
        repo_path = TARGET_DIR / name
        if not repo_path.exists():
            print(f"⬇️ Cloning missing universe slice: {name}...")
            subprocess.run(["git", "clone", f"https://github.com/planetmath/{name}.git", str(repo_path)])
            cloned_count += 1
            
    if cloned_count == 0:
        print("✅ All PlanetMath GitHub repositories are already fully synced locally!")
    else:
        print(f"✅ Sync complete. Cloned {cloned_count} new repositories.")

def run_github_sync():
    """Public wrapper to allow other scripts to run this conditionally."""
    try:
        repos = get_repo_list()
        clone_repos(repos)
    except Exception as e:
        print(f"❌ Failed to sync with GitHub: {e}")
        print("⚠️ Pipeline will attempt to proceed with whatever local files are available.")

if __name__ == "__main__":
    print("🎬 Running Standalone PlanetMath GitHub Manager Sync...")
    run_github_sync()