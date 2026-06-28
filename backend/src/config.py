# backend/src/config.py

from pathlib import Path

# 1. Establish the base anchor points
CONFIG_DIR = Path(__file__).resolve().parent          # backend/src/
BACKEND_DIR = CONFIG_DIR.parent                       # backend/
PROJECT_ROOT = BACKEND_DIR.parent                     # Project Root/

# Source Code Directories
ROUTES_DIR = CONFIG_DIR / "routes"

SERVICES_DIR = CONFIG_DIR / "services"
MATH_SERVICES_DIR = SERVICES_DIR / "math"

DATABASE_SRC_DIR = CONFIG_DIR / "database"
MATH_DATABASE_SRC_DIR = DATABASE_SRC_DIR / "math"
MATH_PIPELINE_SRC_DIR = MATH_DATABASE_SRC_DIR / "pipeline"
MATH_DIAGNOSTICS_SRC_DIR = MATH_DATABASE_SRC_DIR / "diagnostics"

UTILS_DIR = CONFIG_DIR / "utils"
MATH_UTILS_DIR = UTILS_DIR / "math"

# 2. Define Global, Absolute Paths for the Entire Application Suite
DB_PATH = BACKEND_DIR / "portfolio.db"

PLANETMATH_CACHE_DIR = Path(r"C:\Development\planetmath_data")

# Data Directories - Music & Photos
MUSIC_RAW_DIR = BACKEND_DIR / "data" / "music" / "raw"
MUSIC_PROCESSED_DIR = BACKEND_DIR / "data" / "music" / "processed"
PHOTO_RAW_DIR = BACKEND_DIR / "data" / "photos" / "raw"

# Data Directories - Mathematics
MATH_DATA_DIR = BACKEND_DIR / "data" / "math"
SOURCE_CSV_PATH = MATH_DATA_DIR / "msc_master_source.csv"

MATH_DIAGRAM_DIR = MATH_DATA_DIR / "diagrams"
MATH_TEMP_DIR = MATH_DATA_DIR / "temp"

# Frontend Asset Targets
PHOTO_TARGET_DIR = PROJECT_ROOT / "frontend" / "images" / "photography"



def verify_system_directories():
    """Ensures critical system workspace folders exist on disk before running utilities."""
    dirs = [
        MUSIC_RAW_DIR, 
        MUSIC_PROCESSED_DIR, 
        PHOTO_RAW_DIR, 
        PHOTO_TARGET_DIR,
        MATH_DATA_DIR,
        MATH_DIAGRAM_DIR,
        MATH_TEMP_DIR
    ]
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created missing system directory: {d}")

# Automatically ensure directories exist when config is imported
verify_system_directories()