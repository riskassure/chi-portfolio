import os
import sys
from PIL import Image

# Tell Python to look up one folder level (out of utils/ into src/) to find config.py
sys.path.append(str(sys.path[0] + '/..'))
from config import PHOTO_RAW_DIR, PHOTO_TARGET_DIR

def batch_convert_to_webp(quality=80, max_width=1920):
    """
    Scans the configured raw source directory for JPEGs, resizes them down to a clean monitor width 
    if they are too large, and converts them to web-optimized .webp files.
    """
    # Create the target images directory if it doesn't exist yet
    if not PHOTO_TARGET_DIR.exists():
        PHOTO_TARGET_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created target directory: {PHOTO_TARGET_DIR}")

    # Supported source extensions
    valid_extensions = ('.jpg', '.jpeg', '.JPG', '.JPEG')
    
    # Track files processed
    converted_count = 0

    print("🚀 Starting bulk landscape optimization engine...")
    print("-" * 60)

    # Read filenames out of the config path object
    for filename in os.listdir(str(PHOTO_RAW_DIR)):
        if filename.endswith(valid_extensions):
            source_path = PHOTO_RAW_DIR / filename
            
            # Create a clean lowercase filename using underscores instead of spaces
            clean_base_name = source_path.stem.lower().replace(" ", "_")
            target_filename = f"{clean_base_name}.webp"
            target_path = PHOTO_TARGET_DIR / target_filename

            try:
                with Image.open(str(source_path)) as img:
                    original_size_mb = source_path.stat().st_size / (1024 * 1024)
                    
                    # 1. OPTIONAL RESIZING: Keep aspect ratio but scale down massive camera raw dimensions
                    if img.width > max_width:
                        w_percent = (max_width / float(img.width))
                        h_size = int((float(img.height) * float(w_percent)))
                        img = img.resize((max_width, h_size), Image.Resampling.LANCZOS)
                    
                    # 2. TRANSCODE TO WEBP: Strip metadata and compress to the sweet-spot quality
                    img.save(str(target_path), "WEBP", quality=quality, optimize=True)
                    
                    new_size_kb = target_path.stat().st_size / 1024
                    print(f"✅ Optimized: {filename} ({original_size_mb:.2f} MB) ➡️ {target_filename} ({new_size_kb:.1f} KB)")
                    converted_count += 1
                    
            except Exception as e:
                print(f"❌ Failed to process {filename}: {str(e)}")

    print("-" * 60)
    print(f"🎉 Complete! Successfully moved and optimized {converted_count} landscape assets into WebP format.")

# --- RUN EXECUTION ---
if __name__ == "__main__":
    batch_convert_to_webp(quality=80, max_width=1920)