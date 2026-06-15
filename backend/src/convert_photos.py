import os
from PIL import Image

def batch_convert_to_webp(source_dir, target_dir, quality=80, max_width=1920):
    """
    Scans a source directory for JPEGs, resizes them down to a clean monitor width 
    if they are too large, and converts them to web-optimized .webp files.
    """
    # Create the target images directory if it doesn't exist yet
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"Created target directory: {target_dir}")

    # Supported source extensions
    valid_extensions = ('.jpg', '.jpeg', '.JPG', '.JPEG')
    
    # Track files processed
    converted_count = 0

    print("🚀 Starting bulk landscape optimization engine...")
    print("-" * 60)

    for filename in os.listdir(source_dir):
        if filename.endswith(valid_extensions):
            source_path = os.path.join(source_dir, filename)
            
            # Create a clean lowercase filename using underscores instead of spaces
            clean_base_name = os.path.splitext(filename)[0].lower().replace(" ", "_")
            target_filename = f"{clean_base_name}.webp"
            target_path = os.path.join(target_dir, target_filename)

            try:
                with Image.open(source_path) as img:
                    original_size_mb = os.path.getsize(source_path) / (1024 * 1024)
                    
                    # 1. OPTIONAL RESIZING: Keep aspect ratio but scale down massive camera raw dimensions
                    if img.width > max_width:
                        w_percent = (max_width / float(img.width))
                        h_size = int((float(img.height) * float(w_percent)))
                        img = img.resize((max_width, h_size), Image.Resampling.LANCZOS)
                    
                    # 2. TRANSCODE TO WEBP: Strip metadata and compress to the sweet-spot quality
                    img.save(target_path, "WEBP", quality=quality, optimize=True)
                    
                    new_size_kb = os.path.getsize(target_path) / 1024
                    print(f"✅ Optimized: {filename} ({original_size_mb:.2f} MB) ➡️ {target_filename} ({new_size_kb:.1f} KB)")
                    converted_count += 1
                    
            except Exception as e:
                print(f"❌ Failed to process {filename}: {str(e)}")

    print("-" * 60)
    print(f"🎉 Complete! Successfully moved and optimized {converted_count} landscape assets into WebP format.")

# --- RUN EXECUTION ---
if __name__ == "__main__":
    # ".." jumps up out of src/ so Python can see the data and frontend folders
    SOURCE_FOLDER = r"../data/photos/raw"
    TARGET_FOLDER = r"../../frontend/images/photography"
    
    batch_convert_to_webp(SOURCE_FOLDER, TARGET_FOLDER, quality=80, max_width=1920)