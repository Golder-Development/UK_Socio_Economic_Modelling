"""
Script to fetch Tenure data from the ONS API.

Tenure data provides Census 2021 information about housing tenure types 
(e.g., owned outright, owned with mortgage, rented from local authority, 
private rented, etc.) across different geographic areas.

Note: This dataset uses direct CSV download as it's a Census table,
not the observations API endpoint.
"""
import requests
import pandas as pd
import logging
from pathlib import Path
from io import StringIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT_URL = "https://api.beta.ons.gov.uk/v1/"
OUTPUT_DIR = Path(__file__).parent
DATASET_ID = "TS054"  # Tenure dataset ID


def _most_recent_extract_dir() -> Path:
    """Return the most recent extract directory, or create a new one."""
    extract_dirs = [p for p in OUTPUT_DIR.iterdir() if p.is_dir() and p.name.startswith("extract_")]
    if extract_dirs:
        return max(extract_dirs, key=lambda p: p.stat().st_mtime)
    
    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    new_dir = OUTPUT_DIR / f"extract_{ts}"
    new_dir.mkdir(parents=True, exist_ok=True)
    return new_dir


def main():
    """Main entry point."""
    logger.info(f"Fetching Tenure data (Census 2021)")

    # Step 1: Get the dataset metadata
    try:
        dataset_url = f"{ROOT_URL}datasets/{DATASET_ID}"
        logger.info(f"Fetching dataset metadata from: {dataset_url}")
        r = requests.get(dataset_url)
        r.raise_for_status()
        dataset = r.json()
        
        logger.info(f"Found dataset: {dataset.get('title', DATASET_ID)}")
        logger.info(f"Description: {dataset.get('description', 'N/A')[:200]}...")
    except Exception as e:
        logger.error(f"Error fetching dataset metadata: {e}")
        return

    # Step 2: Get the latest version
    try:
        latest_version_url = dataset.get("links", {}).get("latest_version", {}).get("href")
        if not latest_version_url:
            logger.error("Could not find latest version URL")
            return
        
        logger.info(f"\nFetching latest version from: {latest_version_url}")
        r = requests.get(latest_version_url)
        r.raise_for_status()
        version_data = r.json()
        
        logger.info(f"Version: {version_data.get('version')}")
        logger.info(f"Edition: {version_data.get('edition')}")
        logger.info(f"Release date: {version_data.get('release_date')}")
    except Exception as e:
        logger.error(f"Error fetching version data: {e}")
        return

    # Step 3: Get the CSV download link
    downloads = version_data.get("downloads", {})
    csv_download = downloads.get("csv", {})
    csv_url = csv_download.get("href")
    
    if not csv_url:
        logger.error("No CSV download link found")
        logger.info(f"Available downloads: {list(downloads.keys())}")
        return
    
    logger.info(f"\nCSV download URL: {csv_url}")
    logger.info(f"File size: {csv_download.get('size', 'unknown')} bytes")

    # Step 4: Download the CSV data
    logger.info("\nDownloading CSV data...")
    try:
        r = requests.get(csv_url, timeout=120)
        r.raise_for_status()
        
        # Parse CSV
        df = pd.read_csv(StringIO(r.text))
        logger.info(f"✓ Downloaded and parsed CSV")
        logger.info(f"✓ Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        
    except Exception as e:
        logger.error(f"Error downloading CSV: {e}")
        return

    # Step 5: Display info about the data
    logger.info(f"\nColumns: {list(df.columns)}")
    logger.info(f"\nFirst few rows:")
    print(df.head(10))
    
    # Step 6: Save to output directory
    extract_dir = _most_recent_extract_dir()
    output_file = extract_dir / "tenure_data.csv"
    df.to_csv(output_file, index=False)
    
    logger.info(f"\n✓ Data saved to: {output_file}")
    logger.info(f"✓ Total records: {len(df)}")
    
    # Display summary statistics if numeric columns exist
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        logger.info(f"\nNumeric column summary:")
        print(df[numeric_cols].describe())


if __name__ == "__main__":
    main()
