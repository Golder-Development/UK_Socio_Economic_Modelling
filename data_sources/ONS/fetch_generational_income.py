"""
Script to fetch all data for "Generational income: The effects of taxes and benefits"
from the ONS API and save to CSV.
"""
import requests
import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT_URL = "https://api.beta.ons.gov.uk/v1/"
OUTPUT_DIR = Path(__file__).parent
DATASET_NAME = "Generational income: The effects of taxes and benefits"


def _most_recent_extract_dir() -> Path:
    """Return the most recent extract directory, or create a new one."""
    extract_dirs = [p for p in OUTPUT_DIR.iterdir() if p.is_dir() and p.name.startswith("extract_")]
    if extract_dirs:
        return max(extract_dirs, key=lambda p: p.stat().st_mtime)
    
    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    new_dir = OUTPUT_DIR / f"extract_{ts}"
    new_dir.mkdir(parents=True, exist_ok=True)
    return new_dir


def get_list_of_datasets():
    """Get list of all datasets available from API.

    Returns
    -------
    list of dicts
        Metadata objects for each available dataset.
    """
    datasets = []

    logger.info("Fetching available datasets...")
    try:
        r = requests.get(ROOT_URL + "datasets")
        r.raise_for_status()
        results = r.json()
        items = results.get("items", [])

        if items:
            datasets.extend(items)

        logger.info(f"Found {len(datasets)} datasets")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching datasets: {e}")

    return datasets


def get_dataset_by_name(datasets, target_name):
    """Get a dataset by matching on its title.

    Parameters
    ----------
    datasets : List
        List of dataset objects
    target_name : str
        name (or partial name) of target dataset

    Returns
    -------
    dict
        Dataset object (or None, if no match is found)
    """
    for ds in datasets:
        if target_name.lower() in ds.get("title", "").lower():
            logger.info(f"Found dataset '{ds.get('title')}'")
            return ds

    logger.warning(f"No dataset found matching '{target_name}'")
    return None


def get_edition(dataset, preferred_edition="time-series"):
    """Get edition URL for a dataset.

    Parameters
    ----------
    dataset : dict
        Dataset metadata
    preferred_edition : str, optional
        Name of edition, by default "time-series"

    Returns
    -------
    str
        URL of edition
    """
    try:
        editions_url = dataset.get("links", {}).get("editions", {}).get("href")
        if not editions_url:
            # Fallback to latest version
            return dataset.get("links", {}).get("latest_version", {}).get("href")

        r = requests.get(editions_url)
        r.raise_for_status()
        results = r.json()

        for row in results.get("items", []):
            if row.get("edition") == preferred_edition:
                edition = row.get("links", {}).get("latest_version", {}).get("href")
                if edition:
                    logger.info(f"Using edition: {preferred_edition}")
                    return edition

        # Default to latest version
        latest = dataset.get("links", {}).get("latest_version", {}).get("href")
        logger.info("Using latest version")
        return latest
    except Exception as e:
        logger.error(f"Error getting edition: {e}")
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

        for dimension in results.get("items", []):
            dim_name = dimension.get("name")
            dim_label = dimension.get("label")
            logger.info(f"Processing dimension: {dim_name} ({dim_label})")

            dim_id = dimension.get("links", {}).get("options", {}).get("id")
            options_url = f"{edition_url}/dimensions/{dim_id}/options"

            # Fetch options with pagination
            options_dict = {}
            sr = requests.get(options_url)
            sr.raise_for_status()
            sresults = sr.json()

            for item in sresults.get("items", []):
                options_dict[item.get("option")] = item.get("label")

            logger.info(f"  Found {len(options_dict)} options")
            valid_dimensions[dim_name] = options_dict

    except Exception as e:
        logger.error(f"Error getting dimensions: {e}")

    return valid_dimensions


def get_observations_paginated(edition_url, dimensions):
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
        logger.info(f"Requesting URL: {url}")
        logger.info(f"Parameters: {dimensions}")

        r = requests.get(url, params=dimensions)

        if r.status_code != 200:
            logger.error(f"Status code: {r.status_code}")
            logger.error(f"Response text: {r.text}")
            r.raise_for_status()

        results = r.json()

        obs_list = results.get("observations", [])
        if obs_list:
            observations.extend(obs_list)
            logger.info(f"Retrieved {len(observations)} observations")
        else:
            logger.warning("No observations found in response")

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error fetching observations: {e}")
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


def main():
    """Main entry point."""
    logger.info(f"Fetching data for: {DATASET_NAME}")

    # Step 1: Get all datasets
    all_datasets = get_list_of_datasets()

    # Step 2: Find the target dataset
    dataset = get_dataset_by_name(all_datasets, DATASET_NAME)
    if not dataset:
        logger.error(f"Could not find dataset: {DATASET_NAME}")
        return

    # Step 3: Get edition URL
    edition_url = get_edition(dataset)
    if not edition_url:
        logger.error("Could not get edition URL")
        return

    logger.info(f"Edition URL: {edition_url}")

    # Step 4: Get dimensions and their options
    logger.info("\nFetching dimensions...")
    valid_dimensions = get_dimensions(edition_url)
    logger.info(f"Found {len(valid_dimensions)} dimensions")

    # Step 5: Prepare dimensions for API call (use wildcard for time to get all)
    api_dimensions = {}
    for dim_name, options_dict in valid_dimensions.items():
        if dim_name.lower() == "time":
            api_dimensions[dim_name] = "*"
        else:
            # Use first available option for other dimensions
            first_option = next(iter(options_dict.keys()))
            api_dimensions[dim_name] = first_option
            logger.info(f"  Using first option for {dim_name}: {first_option}")

    logger.info(f"\nFinal API dimensions:")
    for k, v in api_dimensions.items():
        logger.info(f"  {k}: {v}")

    # Step 6: Fetch observations
    logger.info("\nFetching observations...")
    observations = get_observations_paginated(edition_url, api_dimensions)
    logger.info(f"Total observations retrieved: {len(observations)}")

    if not observations:
        logger.warning("No observations found!")
        return

    # Step 7: Convert to DataFrame and save
    logger.info("\nConverting to DataFrame...")
    df = observations_to_dataframe(observations)

    extract_dir = _most_recent_extract_dir()
    output_file = extract_dir / "generational_income_data.csv"
    df.to_csv(output_file, index=False)
    logger.info(f"\n✓ Data saved to: {output_file}")
    logger.info(f"✓ Total records: {len(df)}")
    logger.info(f"\nFirst few rows:")
    print(df.head(10))


if __name__ == "__main__":
    main()
