import os
from pathlib import Path

# 1. Establish the base anchor point (backend/src/)
CONFIG_DIR = Path(__file__).resolve().parent

# 2. Establish the Project Root (Climb up 2 levels: src -> backend -> Project Root)
PROJECT_ROOT = CONFIG_DIR.parent.parent

# 3. Define Global, Absolute Paths for the Entire Application Suite
DB_PATH = PROJECT_ROOT / "backend" / "portfolio.db"

# Data Directories
MUSIC_RAW_DIR = PROJECT_ROOT / "backend" / "data" / "music" / "raw"
MUSIC_PROCESSED_DIR = PROJECT_ROOT / "backend" / "data" / "music" / "processed"
PHOTO_RAW_DIR = PROJECT_ROOT / "backend" / "data" / "photos" / "raw"

# Frontend Asset Targets
PHOTO_TARGET_DIR = PROJECT_ROOT / "frontend" / "images" / "photography"

def verify_system_directories():
    """Optional helper to ensure folders exist on disk before running utilities."""
    dirs = [MUSIC_RAW_DIR, MUSIC_PROCESSED_DIR, PHOTO_RAW_DIR, PHOTO_TARGET_DIR]
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created missing system directory: {d}")

# Automatically ensure directories exist when config is imported
verify_system_directories()