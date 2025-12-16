"""
Script to fetch all available datasets from ONS API and save to file.
Outputs dataset name, description, and URL to a CSV file.
"""
import requests
import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT_URL = "https://api.beta.ons.gov.uk/v1/"
BASE_DIR = Path(__file__).parent


def _most_recent_extract_dir() -> Path:
    """Return the most recent extract directory, or create a new one."""
    extract_dirs = [p for p in BASE_DIR.iterdir() if p.is_dir() and p.name.startswith("extract_")]
    if extract_dirs:
        return max(extract_dirs, key=lambda p: p.stat().st_mtime)
    
    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    new_dir = BASE_DIR / f"extract_{ts}"
    new_dir.mkdir(parents=True, exist_ok=True)
    return new_dir


def get_all_datasets():
    """Fetch all available datasets from ONS API.

    Returns
    -------
    list of dicts
        Metadata objects for each available dataset.
    """
    datasets = []
    offset = 0
    page_size = 100

    logger.info("Fetching ONS datasets...")
    while True:
        try:
            r = requests.get(ROOT_URL + "datasets", params={"offset": offset, "limit": page_size})
            r.raise_for_status()
            results = r.json()

            items = results.get("items", [])
            if not items:
                break

            datasets.extend(items)
            num_retrieved = results.get("count", 0)
            offset += num_retrieved

            logger.info(f"Retrieved {len(datasets)} datasets so far...")

            if num_retrieved == 0:
                break
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching datasets: {e}")
            break

    logger.info(f"Total datasets found: {len(datasets)}")
    return datasets


def extract_dataset_info(datasets):
    """Extract name, description, and URL from dataset metadata.

    Parameters
    ----------
    datasets : list of dicts
        Raw dataset objects from API

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: name, description, url
    """
    data = []
    for ds in datasets:
        info = {
            "name": ds.get("title", "N/A"),
            "description": ds.get("description", ""),
            "url": ds.get("links", {}).get("self", {}).get("href", ""),
            "release_date": ds.get("release_date", ""),
        }
        data.append(info)

    df = pd.DataFrame(data)
    return df.sort_values("name").reset_index(drop=True)


def save_datasets_to_file(df, output_path):
    """Save dataset information to CSV file.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with dataset information
    output_path : Path
        Path where CSV file will be saved
    """
    df.to_csv(output_path, index=False)
    logger.info(f"Datasets saved to: {output_path}")
    logger.info(f"Total datasets: {len(df)}")
    print(f"\n✓ Saved {len(df)} datasets to {output_path}\n")
    print(df.to_string())


def main():
    """Main function to fetch and save datasets."""
    datasets = get_all_datasets()
    df = extract_dataset_info(datasets)
    extract_dir = _most_recent_extract_dir()
    output_file = extract_dir / "ons_datasets.csv"
    save_datasets_to_file(df, output_file)
    """Main entry point."""
    datasets = get_all_datasets()
    df = extract_dataset_info(datasets)
    save_datasets_to_file(df, OUTPUT_FILE)


if __name__ == "__main__":
    main()
