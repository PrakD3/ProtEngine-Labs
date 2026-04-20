import gdown
import os
import sys
import argparse
from pathlib import Path

# The ID provided by the user
GOOGLE_DRIVE_ID = "1e0fhTNt3yGOmYSZGsJpAbpDvb6zySyEd"

def download_cosmic(force=False):
    # Ensure we are in the correct directory relative to the script
    # This script is in backend/scripts/, so data is at ../data/
    script_dir = Path(__file__).resolve().parent
    data_dir = script_dir.parent / "data" / "cosmic"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    output = data_dir / "cmc_export.tsv"
    
    if not force and output.exists() and output.stat().st_size > 1000000000: # Simple check for >1GB
        print(f"✅ COSMIC dataset already exists and looks valid at {output}")
        return

    print(f"🚀 Starting COSMIC dataset download (1.7GB) from Google Drive...")
    print(f"📂 Destination: {output}")
    
    url = f"https://drive.google.com/uc?id={GOOGLE_DRIVE_ID}"
    
    try:
        gdown.download(url, str(output), quiet=False)
        print(f"✨ Download complete! Local search will be available on next restart.")
    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download COSMIC search index dataset")
    parser.add_argument("--download", action="store_true", help="Force download without checking existing file")
    args = parser.parse_args()
    
    download_cosmic(force=args.download)
