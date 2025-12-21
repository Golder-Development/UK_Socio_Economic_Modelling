"""
Add harmonized disease categories to mortality data files.
This enables longitudinal analysis across different ICD periods using consistent categories.
"""

import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent

# Define year ranges for each ICD version (same as year-aware matching)
ICD_YEAR_RANGES = {
    "ICD-1 (1901-1910)": (1901, 1910),
    "ICD-2 (1911-1920)": (1911, 1920),
    "ICD-3 (1921-1930)": (1921, 1930),
    "ICD-4 (1931-1939)": (1931, 1939),
    "ICD-5 (1940-1949)": (1940, 1949),
    "ICD-6 (1950-1957)": (1950, 1957),
    "ICD-7 (1958-1967)": (1958, 1967),
    "ICD-8 (1968-1978)": (1968, 1978),
    "ICD-9a (1979-1984)": (1979, 1984),
    "ICD-9b (1985-1993)": (1985, 1993),
    "ICD-9c (1994-2000)": (1994, 2000),
}


def get_icd_version_for_year(year):
    """Determine which ICD version applies to a given year"""
    for icd_version, (start_year, end_year) in ICD_YEAR_RANGES.items():
        if start_year <= year <= end_year:
            return icd_version
    return None


def add_harmonized_categories_to_file(input_file, output_file, harmonized_mapping):
    """Add harmonized category columns to mortality data"""
    logger.info(f"\nProcessing {input_file.name}")

    # Load mortality data
    df = pd.read_csv(input_file, low_memory=False)
    logger.info(f"  Loaded {len(df):,} rows")

    # Check required columns
    if "cause" not in df.columns or "year" not in df.columns:
        logger.warning(f"  Missing required columns, skipping")
        return

    # Prepare data
    df["cause"] = df["cause"].astype(str).str.strip()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    # Determine ICD version for each row
    df["icd_version"] = df["year"].apply(get_icd_version_for_year)

    # Prepare harmonized mapping
    harmonized_lookup = harmonized_mapping.copy()
    harmonized_lookup["code"] = harmonized_lookup["code"].astype(str).str.strip()

    # Merge harmonized categories based on code AND ICD version
    df = df.merge(
        harmonized_lookup[
            [
                "code",
                "icd_version",
                "harmonized_category",
                "harmonized_category_name",
                "classification_confidence",
            ]
        ],
        left_on=["cause", "icd_version"],
        right_on=["code", "icd_version"],
        how="left",
    )

    # Drop temporary columns
    if "code" in df.columns:
        df = df.drop(columns=["code"])
    if "icd_version" in df.columns:
        df = df.drop(columns=["icd_version"])

    # Reorder columns to put harmonized categories after cause/cause_description
    cols = df.columns.tolist()

    # Remove harmonized columns from their current position
    harm_cols = [
        "harmonized_category",
        "harmonized_category_name",
        "classification_confidence",
    ]
    for col in harm_cols:
        if col in cols:
            cols.remove(col)

    # Find insertion point (after cause_description if it exists, otherwise after cause)
    if "cause_description" in cols:
        insert_idx = cols.index("cause_description") + 1
    elif "cause" in cols:
        insert_idx = cols.index("cause") + 1
    else:
        insert_idx = 0

    # Insert harmonized columns
    for i, col in enumerate(harm_cols):
        if col in df.columns:
            cols.insert(insert_idx + i, col)

    df = df[cols]

    # Calculate statistics
    matched = df["harmonized_category"].notna().sum()
    total = len(df)
    match_rate = (matched / total * 100) if total > 0 else 0

    logger.info(
        f"  Matched harmonized categories: {matched:,} / {total:,} ({match_rate:.1f}%)"
    )

    # Show category distribution
    if "harmonized_category_name" in df.columns:
        logger.info(f"\n  Distribution of deaths by harmonized category:")
        cat_summary = (
            df.groupby("harmonized_category_name")["deaths"]
            .sum()
            .sort_values(ascending=False)
        )
        total_deaths = df["deaths"].sum()
        for cat, deaths in cat_summary.head(10).items():
            pct = (deaths / total_deaths * 100) if total_deaths > 0 else 0
            logger.info(f"    {cat:50s}: {deaths:>10,.0f} deaths ({pct:5.1f}%)")

    # Save
    df.to_csv(output_file, index=False)
    logger.info(f"\n  ✓ Saved to: {output_file}")

    return df


def main():
    logger.info("=" * 80)
    logger.info("ADDING HARMONIZED CATEGORIES TO MORTALITY DATA")
    logger.info("=" * 80)

    # Load harmonized mapping
    mapping_file = DATA_DIR / "icd_harmonized_categories.csv"

    if not mapping_file.exists():
        logger.error(f"Harmonized mapping not found: {mapping_file}")
        logger.error("Please run build_harmonized_categories.py first")
        return

    logger.info(f"\nLoading harmonized category mapping...")
    harmonized_mapping = pd.read_csv(mapping_file)
    logger.info(f"Loaded {len(harmonized_mapping):,} code mappings")
    logger.info(
        f"Categories: {harmonized_mapping['harmonized_category_name'].nunique()}"
    )

    # Process mortality files
    files_to_process = [
        (
            "uk_mortality_by_cause_1901_2025_with_descriptions.csv",
            "uk_mortality_by_cause_1901_2025_harmonized.csv",
        ),
        (
            "uk_mortality_comprehensive_1901_2025_with_descriptions.csv",
            "uk_mortality_comprehensive_1901_2025_harmonized.csv",
        ),
    ]

    for input_filename, output_filename in files_to_process:
        input_file = DATA_DIR / input_filename

        if not input_file.exists():
            logger.warning(f"File not found: {input_filename}")
            continue

        output_file = DATA_DIR / output_filename
        add_harmonized_categories_to_file(input_file, output_file, harmonized_mapping)

    logger.info("\n" + "=" * 80)
    logger.info("COMPLETE")
    logger.info("=" * 80)
    logger.info("\nYou can now perform longitudinal analysis using:")
    logger.info("- harmonized_category (short code)")
    logger.info("- harmonized_category_name (human-readable)")
    logger.info("\nThese categories are consistent across all ICD versions (1901-2000)")


if __name__ == "__main__":
    main()
