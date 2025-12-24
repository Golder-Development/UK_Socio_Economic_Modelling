"""
CLI to extract individual population identity splits from ONS datasets and
save each to a separate CSV in the latest extract directory.

Examples:
    python identity_extract.py --religion
    python identity_extract.py --ethnicity --sexual-orientation
    python identity_extract.py --all

Optional:
    --geo "England and Wales" (default tries UK then England & Wales)
"""
import argparse
import logging
from typing import List

import pandas as pd

from fetch_ons_data import _most_recent_extract_dir, load_datasets_csv
from identity_utils import IdentityDataset, fetch_identity_split
from fetch_ons_data import get_dimensions, find_dataset_by_name, get_latest_version_url

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def build_configs(geo_pref: str, national: bool, heritage_dataset: str) -> List[IdentityDataset]:
    geo_labels = [geo_pref, "United Kingdom", "England and Wales"]
    if national:
        religion_name = "Religion"
        ethnicity_name = "Ethnic group"
        sexual_name = "Sexual orientation"
        heritage_name = "National identity" if heritage_dataset == "national_identity" else "Country of birth"
    else:
        religion_name = "Religion (detailed)"
        ethnicity_name = "Ethnic group (detailed)"
        sexual_name = "Sexual orientation (detailed)"
        heritage_name = "National identity (detailed)" if heritage_dataset == "national_identity" else "Country of birth (detailed)"

    return [
        IdentityDataset(
            domain="religion",
            search_name=religion_name,
            category_keywords=["religion"],
            geography_labels=geo_labels,
            notes="Religious identification split",
        ),
        IdentityDataset(
            domain="ethnicity",
            search_name=ethnicity_name,
            category_keywords=["ethnic"],
            geography_labels=geo_labels,
            notes="Ethnic identification split",
        ),
        IdentityDataset(
            domain="sexual_orientation",
            search_name=sexual_name,
            category_keywords=["sexual"],
            geography_labels=geo_labels,
            notes="Sexual orientation split for adults",
        ),
        IdentityDataset(
            domain="heritage_origin",
            search_name=heritage_name,
            category_keywords=["country", "birth"] if "Country of birth" in heritage_name else ["national", "identity"],
            geography_labels=geo_labels,
            notes="Heritage origin proxy",
        ),
    ]


def main():
    parser = argparse.ArgumentParser(description="Extract identity splits to CSV")
    parser.add_argument("--religion", action="store_true", help="Extract religion split")
    parser.add_argument("--ethnicity", action="store_true", help="Extract ethnicity split")
    parser.add_argument("--sexual-orientation", action="store_true", help="Extract sexual orientation split")
    parser.add_argument("--heritage-origin", action="store_true", help="Extract heritage origin split")
    parser.add_argument("--all", action="store_true", help="Extract all splits")
    parser.add_argument("--geo", default="England and Wales", help="Preferred geography label")
    parser.add_argument("--national", action="store_true", help="Use broad national/regional datasets instead of detailed ones")
    parser.add_argument("--heritage-dataset", choices=["country_of_birth", "national_identity"], default="country_of_birth", help="Choose the dataset for heritage origin proxy")
    parser.add_argument("--geo-dim", help="Override geography dimension name (e.g., 'ltla', 'country')")
    parser.add_argument("--geo-code", help="Override geography code to query (e.g., 'E92000001')")
    parser.add_argument("--list-dimensions", action="store_true", help="List dimensions and sample options for selected domains")
    args = parser.parse_args()

    datasets_df = load_datasets_csv()
    if datasets_df is None:
        return

    configs = build_configs(args.geo, args.national, args.heritage_dataset)
    selected_domains = set()
    if args.all:
        selected_domains = {c.domain for c in configs}
    else:
        if args.religion:
            selected_domains.add("religion")
        if args.ethnicity:
            selected_domains.add("ethnicity")
        if args.sexual_orientation:
            selected_domains.add("sexual_orientation")
        if args.heritage_origin:
            selected_domains.add("heritage_origin")

    if not selected_domains:
        logger.info("No domains selected. Use --all or one of the flags.")
        return

    extract_dir = _most_recent_extract_dir()
    if args.list_dimensions:
        # Print dimension names and first few options for each selected domain
        for cfg in configs:
            if cfg.domain not in selected_domains:
                continue
            ds_row = find_dataset_by_name(datasets_df, cfg.search_name)
            if not ds_row:
                logger.error("Dataset not found for %s", cfg.search_name)
                continue
            edition_url = get_latest_version_url(ds_row["url"])
            dims = get_dimensions(edition_url)
            logger.info("\nDimensions for %s:", cfg.search_name)
            for dim_name, options in dims.items():
                sample = list(options.items())[:10]
                logger.info("  %s: %d options", dim_name, len(options))
                for opt_id, label in sample:
                    logger.info("    %s: %s", opt_id, label)
        return
    for cfg in configs:
        if cfg.domain not in selected_domains:
            continue
        logger.info("\n===== Extracting %s (%s) =====", cfg.domain, cfg.search_name)
        df = fetch_identity_split(
            cfg,
            datasets_df,
            geo_dim_override=args.geo_dim,
            geo_code_override=args.geo_code,
        )
        if df is None:
            logger.error("No data for %s", cfg.domain)
            continue
        out_path = extract_dir / f"{cfg.domain}.csv"
        df.to_csv(out_path, index=False)
        logger.info("Saved %s rows to %s", len(df), out_path)


if __name__ == "__main__":
    main()
