"""
Fetch UK mortality statistics from the ONS API and aggregate by year.
Uses the "Deaths registered weekly in England and Wales by age and sex" dataset.
Outputs yearly totals to uk_mortality_totals_by_year.csv.
"""

import requests
import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent
DATASET_NAME = "Deaths registered weekly in England and Wales by age and sex"
DATASET_URL = "https://api.beta.ons.gov.uk/v1/datasets/weekly-deaths-age-sex"


def _most_recent_extract_dir() -> Path:
    """Return the most recent extract directory, or create a new one."""
    extract_dirs = [
        p for p in OUTPUT_DIR.iterdir() if p.is_dir() and p.name.startswith("extract_")
    ]
    if extract_dirs:
        return max(extract_dirs, key=lambda p: p.stat().st_mtime)

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    new_dir = OUTPUT_DIR / f"extract_{ts}"
    new_dir.mkdir(parents=True, exist_ok=True)
    return new_dir


def get_all_editions(dataset_url):
    """Get all available editions for a dataset.

    Parameters
    ----------
    dataset_url : str
        Base dataset URL

    Returns
    -------
    list of dict
        List of edition metadata with 'edition' and 'latest_version' URL
    """
    try:
        editions_url = f"{dataset_url}/editions"
        r = requests.get(editions_url)
        r.raise_for_status()
        results = r.json()

        editions = []
        for item in results.get("items", []):
            edition_name = item.get("edition")
            latest_url = item.get("links", {}).get("latest_version", {}).get("href")
            if edition_name and latest_url:
                editions.append({"edition": edition_name, "url": latest_url})

        logger.info(
            f"Found {len(editions)} editions: {[e['edition'] for e in editions]}"
        )
        return editions
    except Exception as e:
        logger.error(f"Error getting editions: {e}")
        return []


def get_latest_version_url(dataset_url):
    """Get the latest version URL from the dataset URL.

    Parameters
    ----------
    dataset_url : str
        Base dataset URL

    Returns
    -------
    str or None
        Latest version URL
    """
    try:
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


def extract_year_from_time(time_str):
    """Extract year from time dimension string.

    Examples: "2020-01-03", "2020-W01", "Jan-Mar 2020" -> 2020

    Parameters
    ----------
    time_str : str
        Time string from ONS API

    Returns
    -------
    int or None
        Year, or None if cannot be parsed
    """
    if pd.isna(time_str):
        return None

    # Try to extract 4-digit year
    import re

    match = re.search(r"(\d{4})", str(time_str))
    if match:
        return int(match.group(1))

    return None


def aggregate_by_year(df, year):
    """Aggregate death observations for a given year.

    Parameters
    ----------
    df : pd.DataFrame
        Raw observations with 'observation' column
    year : int
        Year for these observations

    Returns
    -------
    dict
        Dictionary with 'year' and 'total_deaths'
    """
    # Convert observation to numeric
    df["deaths"] = pd.to_numeric(df["observation"], errors="coerce")

    # Filter out nulls and sum
    total_deaths = df["deaths"].sum(skipna=True)

    return {"year": year, "total_deaths": int(total_deaths)}


def main():
    """Main entry point."""
    logger.info(f"Fetching mortality data: {DATASET_NAME}")

    # Step 1: Get all available editions (years)
    editions = get_all_editions(DATASET_URL)
    if not editions:
        logger.error("No editions found")
        return

    yearly_results = []

    # First, try to process the "2010-19" edition which has historical data from 2010-2019
    historical_edition = next((e for e in editions if e["edition"] == "2010-19"), None)
    if historical_edition:
        logger.info(f"\n{'=' * 70}")
        logger.info(f"Processing 2010-19 edition (historical data 2010-2019)")
        logger.info(f"Edition URL: {historical_edition['url']}")
        logger.info(f"{'=' * 70}")

        valid_dimensions = get_dimensions(historical_edition["url"])
        if valid_dimensions:
            # For 2010-19 edition, check if there's a 'year' or 'time' dimension with multiple years
            time_dim_name = None
            for dim_name in valid_dimensions.keys():
                if dim_name.lower() in ("time", "year"):
                    time_dim_name = dim_name
                    break

            if time_dim_name:
                # We'll fetch data for each year individually since wildcard is limited
                years_available = list(valid_dimensions[time_dim_name].keys())
                logger.info(f"Found years: {years_available}")

                for year_option in years_available:
                    year = extract_year_from_time(year_option)
                    if not year:
                        continue

                    logger.info(f"  Fetching year {year}...")
                    api_dimensions = {}
                    for dim_name, options_dict in valid_dimensions.items():
                        dim_lower = dim_name.lower()

                        if dim_name == time_dim_name:
                            api_dimensions[dim_name] = year_option
                        elif dim_lower == "week":
                            # Use wildcard for weeks
                            api_dimensions[dim_name] = "*"
                        elif dim_lower in ("agegroups", "age", "age_group"):
                            for opt_key, opt_label in options_dict.items():
                                if (
                                    "all" in opt_label.lower()
                                    and "age" in opt_label.lower()
                                ):
                                    api_dimensions[dim_name] = opt_key
                                    break
                            else:
                                api_dimensions[dim_name] = next(
                                    iter(options_dict.keys())
                                )
                        elif dim_lower in ("sex", "gender"):
                            for opt_key, opt_label in options_dict.items():
                                if opt_label.lower() == "all":
                                    api_dimensions[dim_name] = opt_key
                                    break
                            else:
                                api_dimensions[dim_name] = next(
                                    iter(options_dict.keys())
                                )
                        elif dim_lower in ("registrationoroccurrence", "registration"):
                            for opt_key, opt_label in options_dict.items():
                                if "registration" in opt_label.lower():
                                    api_dimensions[dim_name] = opt_key
                                    break
                            else:
                                api_dimensions[dim_name] = next(
                                    iter(options_dict.keys())
                                )
                        elif dim_lower in (
                            "administrative_geography",
                            "geography",
                            "area",
                        ):
                            for opt_key, opt_label in options_dict.items():
                                if (
                                    opt_key.startswith("E92")
                                    or opt_label.lower() == "england"
                                ):
                                    api_dimensions[dim_name] = opt_key
                                    break
                            else:
                                api_dimensions[dim_name] = next(
                                    iter(options_dict.keys())
                                )
                        elif dim_lower in ("deaths",):
                            # Special handling for 'deaths' dimension
                            api_dimensions[dim_name] = next(iter(options_dict.keys()))
                        else:
                            api_dimensions[dim_name] = next(iter(options_dict.keys()))

                    observations = get_observations(
                        historical_edition["url"], api_dimensions
                    )
                    if observations:
                        df = observations_to_dataframe(observations)
                        year_result = aggregate_by_year(df, year)
                        yearly_results.append(year_result)
                        logger.info(
                            f"    ✓ Year {year}: {year_result['total_deaths']:,} deaths"
                        )
            else:
                logger.warning("Could not find time/year dimension in 2010-19 edition")

    # Second, process the "covid-19" edition which likely has 2020-2023 data
    covid_edition = next((e for e in editions if e["edition"] == "covid-19"), None)
    if covid_edition:
        logger.info(f"\n{'=' * 70}")
        logger.info(f"Processing COVID-19 edition (likely 2020-2023)")
        logger.info(f"Edition URL: {covid_edition['url']}")
        logger.info(f"{'=' * 70}")

        valid_dimensions = get_dimensions(covid_edition["url"])
        if valid_dimensions:
            time_dim_name = None
            for dim_name in valid_dimensions.keys():
                if dim_name.lower() in ("time", "year"):
                    time_dim_name = dim_name
                    break

            if time_dim_name:
                years_available = list(valid_dimensions[time_dim_name].keys())
                logger.info(f"Found years: {years_available}")

                for year_option in years_available:
                    year = extract_year_from_time(year_option)
                    if not year:
                        continue

                    logger.info(f"  Fetching year {year}...")
                    api_dimensions = {}
                    for dim_name, options_dict in valid_dimensions.items():
                        dim_lower = dim_name.lower()

                        if dim_name == time_dim_name:
                            api_dimensions[dim_name] = year_option
                        elif dim_lower == "week":
                            api_dimensions[dim_name] = "*"
                        elif dim_lower in ("agegroups", "age", "age_group"):
                            for opt_key, opt_label in options_dict.items():
                                if (
                                    "all" in opt_label.lower()
                                    and "age" in opt_label.lower()
                                ):
                                    api_dimensions[dim_name] = opt_key
                                    break
                            else:
                                api_dimensions[dim_name] = next(
                                    iter(options_dict.keys())
                                )
                        elif dim_lower in ("sex", "gender"):
                            for opt_key, opt_label in options_dict.items():
                                if opt_label.lower() == "all":
                                    api_dimensions[dim_name] = opt_key
                                    break
                            else:
                                api_dimensions[dim_name] = next(
                                    iter(options_dict.keys())
                                )
                        elif dim_lower in ("registrationoroccurrence", "registration"):
                            for opt_key, opt_label in options_dict.items():
                                if "registration" in opt_label.lower():
                                    api_dimensions[dim_name] = opt_key
                                    break
                            else:
                                api_dimensions[dim_name] = next(
                                    iter(options_dict.keys())
                                )
                        elif dim_lower in (
                            "administrative_geography",
                            "geography",
                            "area",
                        ):
                            for opt_key, opt_label in options_dict.items():
                                if (
                                    opt_key.startswith("E92")
                                    or "england and wales" in opt_label.lower()
                                ):
                                    api_dimensions[dim_name] = opt_key
                                    break
                            else:
                                api_dimensions[dim_name] = next(
                                    iter(options_dict.keys())
                                )
                        else:
                            api_dimensions[dim_name] = next(iter(options_dict.keys()))

                    observations = get_observations(
                        covid_edition["url"], api_dimensions
                    )
                    if observations:
                        df = observations_to_dataframe(observations)
                        year_result = aggregate_by_year(df, year)
                        yearly_results.append(year_result)
                        logger.info(
                            f"    ✓ Year {year}: {year_result['total_deaths']:,} deaths"
                        )
            else:
                logger.warning("Could not find time/year dimension in covid-19 edition")

    # Process year-specific editions (2024, 2025, etc.)
    for edition_info in editions:
        edition_name = edition_info["edition"]
        edition_url = edition_info["url"]

        # Try to extract year from edition name
        year = None
        try:
            year = int(edition_name)
        except:
            logger.warning(f"Could not parse year from edition: {edition_name}")
            continue

        logger.info(f"\n{'=' * 70}")
        logger.info(f"Processing year: {year}")
        logger.info(f"Edition URL: {edition_url}")
        logger.info(f"{'=' * 70}")

        # Step 2: Get dimensions for this edition
        valid_dimensions = get_dimensions(edition_url)
        if not valid_dimensions:
            logger.warning(f"No dimensions found for {year}!")
            continue

        # Step 3: Prepare dimensions for API call
        # ONS API allows only ONE wildcard, so we use wildcard for week and specific values for others
        api_dimensions = {}
        wildcard_used = False

        for dim_name, options_dict in valid_dimensions.items():
            dim_lower = dim_name.lower()

            # Use wildcard for week dimension to get all weeks
            if dim_lower in ("week",) and not wildcard_used:
                api_dimensions[dim_name] = "*"
                wildcard_used = True
            elif dim_lower in ("agegroups", "age", "age_group"):
                # Get "all ages" option
                for opt_key, opt_label in options_dict.items():
                    if "all" in opt_label.lower() and "age" in opt_label.lower():
                        api_dimensions[dim_name] = opt_key
                        break
                else:
                    api_dimensions[dim_name] = next(iter(options_dict.keys()))
            elif dim_lower in ("sex", "gender"):
                # Get "all" option
                for opt_key, opt_label in options_dict.items():
                    if opt_label.lower() == "all":
                        api_dimensions[dim_name] = opt_key
                        break
                else:
                    api_dimensions[dim_name] = next(iter(options_dict.keys()))
            elif dim_lower in ("registrationoroccurrence", "registration"):
                # Prefer "registrations"
                for opt_key, opt_label in options_dict.items():
                    if "registration" in opt_label.lower():
                        api_dimensions[dim_name] = opt_key
                        break
                else:
                    api_dimensions[dim_name] = next(iter(options_dict.keys()))
            elif dim_lower in ("administrative_geography", "geography", "area"):
                # Get England code
                for opt_key, opt_label in options_dict.items():
                    if opt_key.startswith("E92") or opt_label.lower() == "england":
                        api_dimensions[dim_name] = opt_key
                        break
                else:
                    api_dimensions[dim_name] = next(iter(options_dict.keys()))
            else:
                # For any other dimension, use first option
                api_dimensions[dim_name] = next(iter(options_dict.keys()))

        logger.info(f"Query dimensions: {api_dimensions}")

        # Step 4: Fetch observations
        observations = get_observations(edition_url, api_dimensions)
        if not observations:
            logger.warning(f"No data retrieved for {year}!")
            continue

        # Step 5: Convert to DataFrame
        df = observations_to_dataframe(observations)

        # Step 6: Aggregate this year
        year_result = aggregate_by_year(df, year)
        yearly_results.append(year_result)
        logger.info(f"✓ Year {year}: {year_result['total_deaths']:,} deaths")

    if not yearly_results:
        logger.error("No data collected!")
        return

    # Step 7: Create final dataframe and save
    logger.info(f"\n{'=' * 70}")
    logger.info("Creating final summary...")
    yearly_df = pd.DataFrame(yearly_results).sort_values("year")

    yearly_output_file = OUTPUT_DIR / "uk_mortality_totals_by_year.csv"
    yearly_df.to_csv(yearly_output_file, index=False)
    logger.info(f"✓ Yearly totals saved to: {yearly_output_file}")
    logger.info(f"✓ Total years: {len(yearly_df)}")
    logger.info(f"\nYearly totals:")
    print(yearly_df.to_string(index=False))


if __name__ == "__main__":
    main()
