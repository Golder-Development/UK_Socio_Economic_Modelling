"""
Comprehensive UK Mortality Database Builder
============================================

Consolidates ALL available mortality data from:
- 1901-1910 (ICD-1)
- 1911-1920 (ICD-2)
- 1921-1930 (ICD-3)
- 1931-1939 (ICD-4)
- 1940-1949 (ICD-5)
- 1950-1957 (ICD-6)
- 1958-1967 (ICD-7)
- 1968-1978 (ICD-8)
- 1979-1984 (ICD-9a)
- 1985-1993 (ICD-9b)
- 1994-2000 (ICD-9c)
- 2001-2025 (existing compiled data and API data)

Outputs:
- uk_mortality_comprehensive_1901_2025.csv: Deaths by year, sex, age
- uk_mortality_by_cause_1901_2025.csv: Deaths by year, cause, sex, age
"""

import pandas as pd
import logging
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent
ONS_DOWNLOADS = DATA_DIR / "ons_downloads" / "extracted"


def add_cause_descriptions(df):
    """Add cause descriptions to dataframe if 'cause' column exists"""
    if "cause" not in df.columns:
        return df

    desc_file = DATA_DIR / "icd_code_descriptions_simplified.csv"

    if not desc_file.exists():
        logger.warning(
            "Code descriptions file not found. Run build_code_descriptions.py first."
        )
        return df

    try:
        logger.info("Loading code descriptions...")
        descriptions_df = pd.read_csv(desc_file)
        descriptions_df["code"] = descriptions_df["code"].astype(str).str.strip()

        # Convert cause to string for matching
        df_copy = df.copy()
        df_copy["cause"] = df_copy["cause"].astype(str).str.strip()

        # Merge descriptions
        df_copy = df_copy.merge(
            descriptions_df[["code", "description"]],
            left_on="cause",
            right_on="code",
            how="left",
        )

        # Drop the extra 'code' column from merge
        if "code" in df_copy.columns:
            df_copy = df_copy.drop(columns=["code"])

        # Rename description column
        if "description" in df_copy.columns:
            df_copy = df_copy.rename(columns={"description": "cause_description"})

        # Reorder columns to put description right after cause
        cols = df_copy.columns.tolist()
        if "cause_description" in cols:
            cols.remove("cause_description")
            if "cause" in cols:
                cause_idx = cols.index("cause")
                cols.insert(cause_idx + 1, "cause_description")
            df_copy = df_copy[cols]

        # Count matches
        matched = df_copy["cause_description"].notna().sum()
        total = len(df_copy)
        match_rate = (matched / total * 100) if total > 0 else 0
        logger.info(f"Added descriptions: {matched:,} / {total:,} ({match_rate:.1f}%)")

        return df_copy
    except Exception as e:
        logger.error(f"Error adding descriptions: {e}")
        return df


def load_icd_file(xlsx_path, year_range=None):
    """Load ICD files - data is in a sheet with year in a column"""
    logger.info(f"Loading {xlsx_path.name}")

    xls = pd.ExcelFile(xlsx_path)
    dfs = []

    # Try different sheet names that contain data
    data_sheets = [
        s
        for s in xls.sheet_names
        if s.lower() not in ["metadata", "description", "correction notice"]
    ]

    for sheet_name in data_sheets:
        try:
            df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
            if df.empty or len(df) < 2:
                continue

            # Check if this sheet has year column
            year_cols = [
                c for c in df.columns if "yr" in c.lower() or "year" in c.lower()
            ]
            if year_cols:
                logger.debug(
                    f"  Found data sheet: {sheet_name}, year column: {year_cols[0]}"
                )
                dfs.append(df)
            else:
                logger.debug(f"  Skipping sheet {sheet_name} - no year column")
                continue

        except Exception as e:
            logger.warning(f"Error reading sheet {sheet_name}: {e}")
            continue

    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()


def process_historical_data():
    """Process all historical mortality files"""
    logger.info("=" * 70)
    logger.info("PROCESSING HISTORICAL MORTALITY DATA (1901-2000)")
    logger.info("=" * 70)

    all_data = []

    # Map of files to load with their typical year ranges
    files_to_load = [
        ("icd1.xls", (1901, 1910)),
        ("icd2.xls", (1911, 1920)),
        ("icd3.xls", (1921, 1930)),
        ("icd4.xls", (1931, 1939)),
        ("icd5.xls", (1940, 1949)),
        ("icd6.xls", (1950, 1957)),
        ("icd7.xlsx", (1958, 1967)),
        ("icd8.xls", (1968, 1978)),
        ("icd9_a.xlsx", (1979, 1984)),
        ("icd9_b.xls", (1985, 1993)),
        ("icd9_c.xls", (1994, 2000)),
    ]

    for filename, year_range in files_to_load:
        filepath = ONS_DOWNLOADS / filename

        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            continue

        try:
            df = load_icd_file(filepath)
            if not df.empty:
                # Get actual year range from data
                if "yr" in df.columns or "year" in df.columns:
                    year_col = "yr" if "yr" in df.columns else "year"
                    df["year"] = pd.to_numeric(df[year_col], errors="coerce")
                    actual_min = df["year"].min()
                    actual_max = df["year"].max()
                    logger.info(
                        f"  ✓ Loaded {len(df):,} rows, year range: {actual_min:.0f}-{actual_max:.0f}"
                    )
                else:
                    logger.info(f"  ✓ Loaded {len(df):,} rows")
                all_data.append(df)
            else:
                logger.warning(f"  ⚠ No data extracted from {filename}")
        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")
            import traceback

            traceback.print_exc()

    if all_data:
        combined = pd.concat(all_data, ignore_index=True, sort=False)
        logger.info(f"\nTotal historical records: {len(combined):,}")
        if "year" in combined.columns:
            logger.info(
                f"Year range: {combined['year'].min():.0f}-{combined['year'].max():.0f}"
            )
        logger.info(f"Columns: {list(combined.columns)}")
        return combined
    else:
        logger.error("No historical data loaded!")
        return pd.DataFrame()


def standardize_historical_columns(df):
    """Standardize column names across different ICD versions"""
    if df.empty:
        return df

    logger.info("\nStandardizing column names...")

    # Common column name variations
    column_mapping = {
        "Year": "year",
        "YEAR": "year",
        "YR": "year",
        "yr": "year",
        "year": "year",
        "Sex": "sex",
        "SEX": "sex",
        "sex": "sex",
        "GENDER": "sex",
        "Age": "age",
        "AGE": "age",
        "age": "age",
        "Age Group": "age",
        "AgeGroup": "age",
        "Cause": "cause",
        "CAUSE": "cause",
        "Cause of Death": "cause",
        "ICD Code": "cause",
        "ICD-10": "icd10",
        "ICD Code Code": "cause",
        "ICD_1": "icd_code",
        "ICD_": "icd_code",
        "Deaths": "deaths",
        "DEATHS": "deaths",
        "Total Deaths": "deaths",
        "Number of Deaths": "deaths",
        "No.": "deaths",
        "Count": "deaths",
        "death": "deaths",
        "NDTHS": "deaths",
        "ndths": "deaths",
    }

    # Rename columns
    df.rename(columns=column_mapping, inplace=True)

    # Ensure year column exists
    if "year" not in df.columns:
        logger.warning("Year column not found!")

    # Remove completely empty columns
    df.dropna(axis=1, how="all", inplace=True)

    logger.info(f"Standardized columns: {list(df.columns)}")
    return df


def load_existing_2001_2025_data():
    """Load existing compiled data for 2001-2025"""
    logger.info("\n" + "=" * 70)
    logger.info("PROCESSING EXISTING DATA (2001-2025)")
    logger.info("=" * 70)

    dfs = []

    # Try to load compiled_mortality files
    compiled_files = [
        DATA_DIR / "downloaded_sourcefiles" / "compiled_mortality_2001_2019.csv",
        DATA_DIR / "downloaded_sourcefiles" / "compiled_mortality_21c_2017.csv",
    ]

    for filepath in compiled_files:
        if filepath.exists():
            try:
                logger.info(f"Loading {filepath.name}")
                df = pd.read_csv(filepath, low_memory=False)

                # Standardize column names for this file
                df.columns = df.columns.str.lower().str.strip()

                # Ensure we have year column
                if "yr" not in df.columns and "year" not in df.columns:
                    logger.warning(f"  No year column found in {filepath.name}")
                    continue

                if "yr" in df.columns:
                    df["year"] = pd.to_numeric(df["yr"], errors="coerce")
                else:
                    df["year"] = pd.to_numeric(df["year"], errors="coerce")

                logger.info(
                    f"  ✓ Loaded {len(df):,} rows, year range: {df['year'].min():.0f}-{df['year'].max():.0f}"
                )
                dfs.append(df)
            except Exception as e:
                logger.error(f"Failed to load {filepath.name}: {e}")

    if dfs:
        combined = pd.concat(dfs, ignore_index=True, sort=False)
        # Remove duplicates by year, sex, age, cause if they exist
        dup_cols = ["year"] + [
            c for c in ["sex", "age", "icd-10", "icd_1"] if c in combined.columns
        ]
        dup_cols = [c for c in dup_cols if c in combined.columns]
        if len(dup_cols) > 1:
            combined = combined.drop_duplicates(subset=dup_cols, keep="first")
        logger.info(
            f"Combined existing data: {len(combined):,} rows, year range: {combined['year'].min():.0f}-{combined['year'].max():.0f}"
        )
        return combined

    logger.warning("No existing 2001-2025 data found")
    return pd.DataFrame()


def standardize_mortality_data(df):
    """
    Standardize mortality data into a consistent format
    Output: year, cause, sex, age, deaths
    """
    if df.empty:
        return df

    logger.info("\nStandardizing mortality data format...")

    # Create a working copy
    df = df.copy()

    # Normalize column names to lowercase
    df.columns = df.columns.str.lower().str.strip()

    # Handle year column - might be 'yr' or 'year'
    if "yr" in df.columns:
        df["year"] = pd.to_numeric(df["yr"], errors="coerce")
    elif "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
    else:
        logger.warning("Missing year column")
        return pd.DataFrame()

    # Handle deaths column - might be 'ndths', 'deaths', etc.
    deaths_cols = [c for c in df.columns if "ndth" in c or "death" in c or "count" in c]
    if deaths_cols:
        deaths_col = deaths_cols[0]
        df["deaths"] = pd.to_numeric(df[deaths_col], errors="coerce")
    else:
        logger.warning("Missing deaths column")
        return pd.DataFrame()

    # Handle sex column
    if "sex" in df.columns:
        df["sex"] = df["sex"].fillna("All").astype(str).str.strip().str.lower()
        df["sex"] = df["sex"].replace(
            {
                "male": "Male",
                "male.": "Male",
                "males": "Male",
                "m": "Male",
                "1": "Male",
                "female": "Female",
                "female.": "Female",
                "females": "Female",
                "f": "Female",
                "2": "Female",
                "": "All",
                "all": "All",
                "both": "All",
                "persons": "All",
            }
        )
    else:
        df["sex"] = "All"

    # Handle age column - just keep as string
    if "age" in df.columns:
        df["age"] = df["age"].fillna("All ages").astype(str).str.strip()
    else:
        df["age"] = "All ages"

    # Handle cause column - look for ICD codes first
    cause_candidates = [c for c in df.columns if "icd" in c]
    if cause_candidates:
        icd_col = cause_candidates[0]
        df["cause"] = (
            df[icd_col].fillna(df.get("cause", "Unknown")).astype(str).str.strip()
        )
    elif "cause" in df.columns:
        df["cause"] = df["cause"].fillna("Unknown").astype(str).str.strip()
    else:
        df["cause"] = "All causes"

    # Select standard columns
    standard_cols = ["year", "cause", "sex", "age", "deaths"]
    keep_cols = standard_cols + [
        c
        for c in df.columns
        if c not in standard_cols and c not in cause_candidates + ["yr", deaths_col]
        if deaths_cols
    ]
    keep_cols = [c for c in keep_cols if c in df.columns]
    df = df[keep_cols]

    # Filter valid records
    df = df.dropna(subset=["year", "deaths"])
    df = df[
        (df["deaths"] > 0) | (df["deaths"].isna())
    ]  # Keep some nulls but filter obvious zeros
    df["deaths"] = pd.to_numeric(df["deaths"], errors="coerce")
    df = df[df["deaths"] > 0]

    logger.info(f"Standardized: {len(df):,} valid records")
    return df


def aggregate_to_summary(df):
    """
    Create summary tables by year, cause, sex, and age
    """
    if df.empty:
        return df

    logger.info("\nAggregating to summary format...")

    # Ensure numeric columns
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["deaths"] = pd.to_numeric(df["deaths"], errors="coerce").astype("Int64")

    # Group by available dimensions
    group_cols = [c for c in ["year", "cause", "sex", "age"] if c in df.columns]

    if len(group_cols) > 0:
        summary = df.groupby(group_cols, as_index=False, dropna=False)["deaths"].sum()
        summary = summary.sort_values(["year"] + [c for c in group_cols if c != "year"])
        logger.info(f"Aggregated to {len(summary)} summary records")
        return summary

    return df


def create_yearly_totals(df):
    """Create simple yearly total deaths table"""
    if df.empty:
        return pd.DataFrame()

    logger.info("\nCreating yearly totals...")

    df = df.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["deaths"] = pd.to_numeric(df["deaths"], errors="coerce")

    yearly = df.groupby("year", as_index=False)["deaths"].sum()
    yearly = yearly.sort_values("year")

    # Format for readability
    yearly["total_deaths"] = yearly["deaths"].astype("Int64")
    yearly = yearly[["year", "total_deaths"]]

    logger.info(f"Created {len(yearly)} yearly records")
    return yearly


def main():
    logger.info("\n")
    logger.info("╔" + "═" * 68 + "╗")
    logger.info("║" + " " * 68 + "║")
    logger.info("║" + "UK MORTALITY COMPREHENSIVE DATABASE BUILDER".center(68) + "║")
    logger.info("║" + "1901-2025 Complete Analysis".center(68) + "║")
    logger.info("║" + " " * 68 + "║")
    logger.info("╚" + "═" * 68 + "╝")
    logger.info("")

    # Process historical data
    historical = process_historical_data()

    if historical.empty:
        logger.error("No historical data could be loaded!")
        return False

    # Standardize historical data
    historical = standardize_historical_columns(historical)
    historical = standardize_mortality_data(historical)

    # Load existing 2001-2025 data
    existing = load_existing_2001_2025_data()

    if not existing.empty:
        # Standardize existing data
        existing = standardize_historical_columns(existing)
        existing = standardize_mortality_data(existing)

    # Combine all data
    logger.info("\n" + "=" * 70)
    logger.info("COMBINING ALL DATA")
    logger.info("=" * 70)

    if not existing.empty:
        all_data = pd.concat([historical, existing], ignore_index=True, sort=False)
    else:
        all_data = historical

    logger.info(f"Total records: {len(all_data)}")
    if "year" in all_data.columns:
        logger.info(
            f"Year range: {all_data['year'].min():.0f} - {all_data['year'].max():.0f}"
        )

    # Aggregate to summary format
    all_data = aggregate_to_summary(all_data)

    # Create yearly totals
    yearly = create_yearly_totals(all_data)

    # Save outputs
    logger.info("\n" + "=" * 70)
    logger.info("SAVING OUTPUTS")
    logger.info("=" * 70)

    output_comprehensive = DATA_DIR / "uk_mortality_comprehensive_1901_2025.csv"
    output_by_cause = DATA_DIR / "uk_mortality_by_cause_1901_2025.csv"
    output_yearly = DATA_DIR / "uk_mortality_yearly_totals_1901_2025.csv"

    # Save comprehensive dataset
    yearly.to_csv(output_yearly, index=False)
    logger.info(f"✓ Saved yearly totals: {output_yearly.name} ({len(yearly)} records)")

    # Add descriptions to data before saving
    all_data_with_desc = add_cause_descriptions(all_data)

    # Save comprehensive by all dimensions
    all_data_with_desc.to_csv(output_comprehensive, index=False)
    logger.info(
        f"✓ Saved comprehensive data: {output_comprehensive.name} ({len(all_data_with_desc)} records)"
    )

    # Save by cause (filter to only where cause is defined)
    if "cause" in all_data_with_desc.columns:
        by_cause = all_data_with_desc[
            all_data_with_desc["cause"] != "All causes"
        ].copy()
        if not by_cause.empty:
            by_cause.to_csv(output_by_cause, index=False)
            logger.info(
                f"✓ Saved by cause: {output_by_cause.name} ({len(by_cause)} records)"
            )

    # Print summary statistics
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 70)

    if "year" in yearly.columns:
        logger.info(f"\nYearly Data (1901-2025):")
        logger.info(f"  Total years: {len(yearly)}")
        logger.info(
            f"  Year range: {yearly['year'].min():.0f} - {yearly['year'].max():.0f}"
        )
        logger.info(
            f"  Total deaths across all years: {yearly['total_deaths'].sum():,.0f}"
        )
        logger.info(f"  Average annual deaths: {yearly['total_deaths'].mean():,.0f}")

        # Show sample years
        logger.info(f"\n  Sample years:")
        sample_years = [
            int(yearly["year"].min()),
            1950,
            2000,
            2020,
            int(yearly["year"].max()),
        ]
        sample_years = [y for y in sample_years if y in yearly["year"].values]
        for year in sample_years:
            deaths = yearly[yearly["year"] == year]["total_deaths"].values
            if len(deaths) > 0:
                logger.info(f"    {int(year):4d}: {int(deaths[0]):>10,} deaths")

    logger.info("\n" + "=" * 70)
    logger.info("COMPLETE!")
    logger.info("=" * 70)

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
