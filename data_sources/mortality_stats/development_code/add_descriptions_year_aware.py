"""
Add cause code descriptions to mortality CSV files with proper year range matching.
Each ICD version's codes are only valid for specific year ranges.
"""

import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent

# Define year ranges for each ICD version
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
    # For years after 2000, we might not have ICD mapping yet
    return None


def add_descriptions_to_mortality_file(input_file, output_file, descriptions_df):
    """Add description column to mortality data file with year-aware matching"""
    logger.info(f"\nProcessing {input_file.name}")

    # Load mortality data
    df = pd.read_csv(input_file, low_memory=False)
    logger.info(f"  Loaded {len(df):,} rows")
    logger.info(f"  Columns: {df.columns.tolist()}")

    # Check if 'cause' column exists
    if "cause" not in df.columns:
        logger.warning(f"  No 'cause' column found in {input_file.name}, skipping")
        return

    # Check if 'year' column exists
    if "year" not in df.columns:
        logger.warning(f"  No 'year' column found in {input_file.name}, skipping")
        return

    # Convert cause to string for matching
    df["cause"] = df["cause"].astype(str).str.strip()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    # Determine ICD version for each row based on year
    df["icd_version"] = df["year"].apply(get_icd_version_for_year)

    # Prepare descriptions for merging
    desc_lookup = descriptions_df.copy()
    desc_lookup["code"] = desc_lookup["code"].astype(str).str.strip()

    # Merge descriptions based on both code AND ICD version
    df = df.merge(
        desc_lookup[["code", "description", "icd_version"]],
        left_on=["cause", "icd_version"],
        right_on=["code", "icd_version"],
        how="left",
    )

    # Drop the extra 'code' column from merge
    if "code" in df.columns:
        df = df.drop(columns=["code"])

    # Drop the temporary icd_version column
    if "icd_version" in df.columns:
        df = df.drop(columns=["icd_version"])

    # Rename description column to be more descriptive
    if "description" in df.columns:
        df = df.rename(columns={"description": "cause_description"})

    # Reorder columns to put description right after cause
    cols = df.columns.tolist()
    if "cause_description" in cols:
        # Remove cause_description from its current position
        cols.remove("cause_description")
        # Find position of 'cause'
        if "cause" in cols:
            cause_idx = cols.index("cause")
            # Insert cause_description right after cause
            cols.insert(cause_idx + 1, "cause_description")
        df = df[cols]

    # Count matches
    matched = df["cause_description"].notna().sum()
    total = len(df)
    match_rate = (matched / total * 100) if total > 0 else 0

    logger.info(f"  Matched descriptions: {matched:,} / {total:,} ({match_rate:.1f}%)")

    # Show detailed breakdown by year range
    logger.info(f"\n  Breakdown by ICD version:")
    for icd_version, (start_year, end_year) in ICD_YEAR_RANGES.items():
        year_mask = (df["year"] >= start_year) & (df["year"] <= end_year)
        year_data = df[year_mask]
        if len(year_data) > 0:
            year_matched = year_data["cause_description"].notna().sum()
            year_total = len(year_data)
            year_match_rate = (year_matched / year_total * 100) if year_total > 0 else 0
            logger.info(
                f"    {icd_version}: {year_matched:,}/{year_total:,} ({year_match_rate:.1f}%)"
            )

    # Show some examples of unmatched codes by year range
    unmatched_df = df[df["cause_description"].isna()]
    if len(unmatched_df) > 0:
        logger.info(f"\n  Sample unmatched codes by year:")
        for icd_version, (start_year, end_year) in list(ICD_YEAR_RANGES.items())[:3]:
            year_mask = (unmatched_df["year"] >= start_year) & (
                unmatched_df["year"] <= end_year
            )
            year_unmatched = unmatched_df[year_mask]["cause"].unique()
            if len(year_unmatched) > 0:
                logger.info(f"    {start_year}-{end_year}: {list(year_unmatched[:5])}")

    # Save with descriptions
    df.to_csv(output_file, index=False)
    logger.info(f"\n  ✓ Saved to: {output_file}")


def main():
    logger.info("=" * 80)
    logger.info("ADDING CAUSE DESCRIPTIONS TO MORTALITY FILES (YEAR-AWARE)")
    logger.info("=" * 80)

    # Load code descriptions with ICD versions
    desc_file = DATA_DIR / "icd_code_descriptions.csv"

    if not desc_file.exists():
        logger.error(f"Description file not found: {desc_file}")
        logger.error("Please run build_code_descriptions.py first")
        return

    logger.info(f"\nLoading code descriptions from: {desc_file}")
    descriptions_df = pd.read_csv(desc_file)
    logger.info(f"Loaded {len(descriptions_df):,} code descriptions")
    logger.info(f"\nBreakdown by ICD version:")
    for icd_version in descriptions_df["icd_version"].unique():
        count = len(descriptions_df[descriptions_df["icd_version"] == icd_version])
        logger.info(f"  {icd_version}: {count:,} codes")

    # Process mortality files
    mortality_files = [
        "uk_mortality_by_cause_1901_2025.csv",
        "uk_mortality_comprehensive_1901_2025.csv",
        "uk_mortality_by_cause.csv",
    ]

    for filename in mortality_files:
        input_file = DATA_DIR / filename

        if not input_file.exists():
            logger.warning(f"File not found: {filename}")
            continue

        # Create output filename (with descriptions)
        output_file = DATA_DIR / filename.replace(".csv", "_with_descriptions.csv")

        add_descriptions_to_mortality_file(input_file, output_file, descriptions_df)

    logger.info("\n" + "=" * 80)
    logger.info("COMPLETE")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
