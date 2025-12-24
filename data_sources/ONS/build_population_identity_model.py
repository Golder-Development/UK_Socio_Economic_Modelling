"""
Build a harmonised population identity model using ONS Census 2021 datasets.

This script pulls religion, ethnic group, sexual orientation, and country-of-birth
splits for England and Wales (or UK-wide where available) using the ONS API. It
uses the helper functions in fetch_ons_data.py and caches results into the most
recent extract directory under data_sources/ONS/.

Usage:
    python build_population_identity_model.py

Prerequisites:
    1) Run `python list_datasets.py` to refresh ons_datasets.csv
    2) Ensure requests and pandas are installed (see requirements)
"""
import logging
from typing import List, Optional

import pandas as pd

from fetch_ons_data import (
    _most_recent_extract_dir,
    load_datasets_csv,
)
from identity_utils import IdentityDataset, fetch_identity_split

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


TARGET_DATASETS = [
    IdentityDataset(
        domain="religion",
        search_name="Religion (detailed)",
        category_keywords=["religion"],
        geography_labels=["United Kingdom", "England and Wales"],
        notes="Detailed religious identification split",
    ),
    IdentityDataset(
        domain="ethnicity",
        search_name="Ethnic group (detailed)",
        category_keywords=["ethnic"],
        geography_labels=["United Kingdom", "England and Wales"],
        notes="Detailed ethnic identification split",
    ),
    IdentityDataset(
        domain="sexual_orientation",
        search_name="Sexual orientation (detailed)",
        category_keywords=["sexual"],
        geography_labels=["United Kingdom", "England and Wales"],
        notes="Sexual orientation split for adults",
    ),
    IdentityDataset(
        domain="heritage_origin",
        search_name="Country of birth (detailed)",
        category_keywords=["country", "birth"],
        geography_labels=["United Kingdom", "England and Wales"],
        notes="Country of birth used as a proxy for heritage origin",
    ),
]



def build_identity_model() -> Optional[pd.DataFrame]:
    datasets_df = load_datasets_csv()
    if datasets_df is None:
        return None

    results: List[pd.DataFrame] = []
    for cfg in TARGET_DATASETS:
        logger.info("\n===== Fetching %s (%s) =====", cfg.domain, cfg.search_name)
        df = fetch_identity_split(cfg, datasets_df)
        if df is not None:
            results.append(df)
        else:
            logger.error("Skipping %s due to previous errors", cfg.domain)

    if not results:
        logger.error("No datasets fetched; aborting")
        return None

    combined = pd.concat(results, ignore_index=True)
    extract_dir = _most_recent_extract_dir()
    output_path = extract_dir / "population_identity_model.csv"
    combined.to_csv(output_path, index=False)

    logger.info("\n✓ Saved harmonised identity model to %s", output_path)
    logger.info("Dataset coverage:\n%s", combined.groupby("domain").agg({"value": "sum", "category_code": "nunique"}))
    return combined


if __name__ == "__main__":
    build_identity_model()
