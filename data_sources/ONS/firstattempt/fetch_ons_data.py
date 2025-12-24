"""
Generic script to fetch data from any ONS dataset.
Reads from ons_datasets.csv to find the dataset and uses its URL directly.
"""
import requests
import pandas as pd
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent


def _most_recent_extract_dir() -> Path:
    """Return the most recent extract directory, or create a new one."""
    extract_dirs = [p for p in DATA_DIR.iterdir() if p.is_dir() and p.name.startswith("extract_")]
    if extract_dirs:
        return max(extract_dirs, key=lambda p: p.stat().st_mtime)
    
    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    new_dir = DATA_DIR / f"extract_{ts}"
    new_dir.mkdir(parents=True, exist_ok=True)
    return new_dir


def load_datasets_csv():
    """Load the ONS datasets CSV file.

    Returns
    -------
    pd.DataFrame
        DataFrame with dataset metadata
    """
    # Try loading from extract directory first
    extract_dir = _most_recent_extract_dir()
    csv_path = extract_dir / "ons_datasets.csv"
    
    # Fall back to local file
    if not csv_path.exists():
        csv_path = DATA_DIR / "ons_datasets.csv"
    
    if not csv_path.exists():
        logger.error(f"ons_datasets.csv not found at {csv_path}")
        logger.info("Run 'python list_datasets.py' first to generate it")
        return None

    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} datasets from {csv_path}")
    return df


def find_dataset_by_name(datasets_df, dataset_name):
    """Find a dataset by name (case-insensitive substring match).

    Parameters
    ----------
    datasets_df : pd.DataFrame
        DataFrame with all available datasets
    dataset_name : str
        Name (or partial name) to search for

    Returns
    -------
    dict or None
        Dataset row as dict, or None if not found
    """
    search_term = dataset_name.strip().lower()
    matches = datasets_df[
        datasets_df["name"].str.lower().str.contains(search_term, na=False, regex=False)
    ]

    if len(matches) == 0:
        logger.error(f"No dataset found matching '{dataset_name}'")
        return None

    if len(matches) > 1:
        logger.warning(f"Found {len(matches)} matches. Using first one:")
        for idx, row in matches.iterrows():
            logger.info(f"  - {row['name']}")

    dataset = matches.iloc[0].to_dict()
    logger.info(f"\nSelected dataset: {dataset['name']}")
    logger.info(f"URL: {dataset['url']}")
    return dataset


def get_latest_version_url(dataset_url):
    """Get the latest version URL from the dataset URL.

    Parameters
    ----------
    dataset_url : str
        Base dataset URL from the CSV

    Returns
    -------
    str or None
        Latest version URL
    """
    try:
        # The URL in the CSV points to the dataset, we need the latest version
        r = requests.get(dataset_url)
        r.raise_for_status()
        results = r.json()

        latest_url = results.get("links", {}).get("latest_version", {}).get("href")
        if latest_url:
            logger.info(f"Latest version URL: {latest_url}")
            return latest_url

        logger.error("Could not find latest version URL")
        return None
    except Exception as e:
        logger.error(f"Error getting latest version: {e}")
        return None


def get_dimensions(edition_url):
    """Get all dimensions and their valid options for a dataset.

    Parameters
    ----------
    edition_url : str
        URL of the dataset edition

    Returns
    -------
    dict of dicts
        Map of {dimension_name: {option_value: option_label}}
    """
    valid_dimensions = {}
    try:
        r = requests.get(edition_url + "/dimensions")
        r.raise_for_status()
        results = r.json()

        logger.info(f"\nAvailable dimensions:")
        for dimension in results.get("items", []):
            dim_name = dimension.get("name")
            dim_label = dimension.get("label")
            logger.info(f"  - {dim_name}: {dim_label}")

            dim_id = dimension.get("links", {}).get("options", {}).get("id")
            options_url = f"{edition_url}/dimensions/{dim_id}/options"

            try:
                sr = requests.get(options_url)
                sr.raise_for_status()
                sresults = sr.json()

                options_dict = {
                    item.get("option"): item.get("label")
                    for item in sresults.get("items", [])
                }

                logger.info(f"    Available options ({len(options_dict)}):")
                for opt_key, opt_label in list(options_dict.items())[:5]:
                    logger.info(f"      • {opt_key}: {opt_label}")
                if len(options_dict) > 5:
                    logger.info(f"      ... and {len(options_dict) - 5} more")

                valid_dimensions[dim_name] = options_dict
            except Exception as e:
                logger.error(f"    Error fetching options: {e}")

    except Exception as e:
        logger.error(f"Error getting dimensions: {e}")

    return valid_dimensions


def get_observations(edition_url, dimensions):
    """Fetch all observations for given dimensions.

    Parameters
    ----------
    edition_url : str
        URL of the dataset edition
    dimensions : dict
        Dimension filters

    Returns
    -------
    list of dicts
        All observations
    """
    observations = []

    try:
        url = edition_url + "/observations"
        logger.info(f"\nFetching observations from: {url}")
        logger.info(f"Parameters: {dimensions}")

        r = requests.get(url, params=dimensions)

        if r.status_code != 200:
            logger.error(f"Status code: {r.status_code}")
            logger.error(f"Response: {r.text[:500]}")
            r.raise_for_status()

        results = r.json()

        obs_list = results.get("observations", [])
        if obs_list:
            observations.extend(obs_list)
            logger.info(f"✓ Retrieved {len(observations)} observations")
        else:
            logger.warning("No observations found in response")

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e}")
    except Exception as e:
        logger.error(f"Error fetching observations: {e}")

    return observations


def observations_to_dataframe(observations):
    """Convert observations to a DataFrame.

    Parameters
    ----------
    observations : list of dicts
        Raw observation objects from API

    Returns
    -------
    pd.DataFrame
        Flattened dataframe with columns for each dimension and observation value
    """
    data = []
    for obs in observations:
        row = {"observation": obs.get("observation")}
        dims = obs.get("dimensions", {})
        for key, val_dict in dims.items():
            row[key] = val_dict.get("id")
        data.append(row)

    df = pd.DataFrame(data)
    logger.info(f"Created DataFrame with shape: {df.shape}")
    return df


def main(dataset_name):
    """Main entry point.

    Parameters
    ----------
    dataset_name : str
        Name (or partial name) of dataset to fetch
    """
    logger.info(f"Searching for dataset: '{dataset_name}'")

    # Step 1: Load datasets CSV
    datasets_df = load_datasets_csv()
    if datasets_df is None:
        return

    # Step 2: Find the dataset
    dataset = find_dataset_by_name(datasets_df, dataset_name)
    if not dataset:
        return

    # Step 3: Get latest version URL
    edition_url = get_latest_version_url(dataset["url"])
    if not edition_url:
        return

    # Step 4: Get dimensions and their options
    logger.info("\n" + "=" * 70)
    valid_dimensions = get_dimensions(edition_url)
    logger.info("=" * 70)

    if not valid_dimensions:
        logger.warning("No dimensions found!")
        return

    # Step 5: Prepare dimensions for API call (use wildcard for time to get all)
    api_dimensions = {}
    for dim_name, options_dict in valid_dimensions.items():
        if dim_name.lower() == "time":
            api_dimensions[dim_name] = "*"
        else:
            # Use first available option for other dimensions
            first_option = next(iter(options_dict.keys()))
            api_dimensions[dim_name] = first_option

    logger.info(f"\nFinal query dimensions:")
    for k, v in api_dimensions.items():
        logger.info(f"  {k}: {v}")

    # Step 6: Fetch observations
    logger.info("\n" + "=" * 70)
    observations = get_observations(edition_url, api_dimensions)
    logger.info("=" * 70)

    if not observations:
        logger.warning("No data retrieved!")
        return

    # Step 7: Convert to DataFrame and save
    logger.info("\nConverting to DataFrame...")
    df = observations_to_dataframe(observations)

    # Create safe filename from dataset name
    safe_name = "".join(c for c in dataset_name if c.isalnum() or c in (" ", "_", "-")).replace(" ", "_").lower()
    extract_dir = _most_recent_extract_dir()
    output_file = extract_dir / f"{safe_name}_data.csv"

    df.to_csv(output_file, index=False)
    logger.info(f"\n✓ Data saved to: {output_file}")
    logger.info(f"✓ Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    logger.info(f"\nFirst few rows:")
    print(df.head(10).to_string())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_ons_data.py '<dataset_name>'")
        print("\nExample:")
        print("  python fetch_ons_data.py 'Generational income'")
        print("  python fetch_ons_data.py 'Labour Market'")
        print("\nFirst, run 'python list_datasets.py' to generate ons_datasets.csv")
        sys.exit(1)

    dataset_name = sys.argv[1]
    main(dataset_name)
