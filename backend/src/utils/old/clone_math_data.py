import subprocess
import os
import json

def clone_planetmath_repos(target_dir):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # 1. Get list of repos from PlanetMath
    print("Fetching repository list...")
    result = subprocess.run(
        ["gh", "repo", "list", "planetmath", "--limit", "200", "--json", "name"], 
        capture_output=True, text=True, check=True
    )
    repos = json.loads(result.stdout)

    # 2. Loop and clone
    for repo in repos:
        name = repo['name']
        if name.startswith(tuple("0123456789")): # Filters for 03_, 04_, etc.
            repo_path = os.path.join(target_dir, name)
            if not os.path.exists(repo_path):
                print(f"Cloning {name}...")
                subprocess.run(["git", "clone", f"https://github.com/planetmath/{name}.git", repo_path])
            else:
                print(f"Skipping {name}, already exists.")

if __name__ == "__main__":
    target = r"C:\Development\planetmath_data"
    clone_planetmath_repos(target)