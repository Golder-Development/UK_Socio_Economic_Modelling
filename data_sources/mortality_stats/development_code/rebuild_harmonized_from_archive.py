"""
Rebuild harmonized mortality data using the correct source file.
The current harmonized files used corrupted data with "Unknown" causes post-1910.
This script uses the archived comprehensive file which has proper ICD codes throughout.
"""

import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
ARCHIVE_DIR = BASE_DIR / "development_code" / "archive_csv"
SOURCE_FILE = ARCHIVE_DIR / "uk_mortality_comprehensive_1901_2019.csv"
DESC_FILE = BASE_DIR / "icd_code_descriptions.csv"
HARMONIZED_MAP = BASE_DIR / "icd_harmonized_categories.csv"
OVERRIDES_FILE = BASE_DIR / "icd_harmonized_overrides.csv"

# ICD version year ranges
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
    """Determine ICD version based on year."""
    for version, (start, end) in ICD_YEAR_RANGES.items():
        if start <= year <= end:
            return version
    return None


def main():
    logger.info("Starting rebuild of harmonized mortality data...")
    logger.info(f"Source: {SOURCE_FILE}")
    
    # Load source data
    logger.info("Loading source mortality data...")
    df = pd.read_csv(SOURCE_FILE)
    # Limit to years covered by harmonization mappings (<= 2000)
    df = df[df["year"] <= 2000].copy()
    logger.info(f"Loaded {len(df):,} rows ({df['year'].min()}-{df['year'].max()})")
    logger.info(f"Unique causes by decade:")
    for year in [1901, 1911, 1921, 1931, 1941, 1951, 1961, 1971, 1981, 1991, 2001, 2011]:
        subset = df[df['year']==year]
        if len(subset) > 0:
            logger.info(f"  {year}: {subset['cause'].nunique()} unique causes")
    
    # Add ICD version column
    logger.info("\nAdding ICD version...")
    df['icd_version'] = df['year'].apply(get_icd_version_for_year)
    
    # Normalize cause codes to align with description code formats per ICD version
    def normalize_code(val, version):
        s = str(val)
        if version.startswith("ICD-1"):
            # ICD-1 codes are like 10.0, 20.0 in descriptions; archived uses integers
            # Append .0 for pure integer codes
            return f"{int(s)}.0"
        # Other ICD versions already use alphanumeric codes (e.g., 100A, 3A)
        return s

    df['cause'] = df.apply(lambda r: normalize_code(r['cause'], r['icd_version']), axis=1)
    
    # Load descriptions with year-aware matching
    logger.info("Loading code descriptions...")
    desc_df = pd.read_csv(DESC_FILE)
    desc_df['code'] = desc_df['code'].astype(str)
    logger.info(f"Loaded {len(desc_df):,} code descriptions")
    
    # Merge with year-aware matching (code + ICD version)
    logger.info("Merging descriptions (year-aware)...")
    df = df.merge(
        desc_df[['code', 'icd_version', 'description']],
        left_on=['cause', 'icd_version'],
        right_on=['code', 'icd_version'],
        how='left'
    )
    df = df.rename(columns={'description': 'cause_description'})
    df = df.drop(columns=['code'], errors='ignore')
    
    matched = df['cause_description'].notna().sum()
    total = len(df)
    match_rate = (matched / total) * 100
    logger.info(f"Description match rate: {matched:,} / {total:,} ({match_rate:.1f}%)")
    
    # Load harmonized categories
    logger.info("\nLoading harmonized categories...")
    harm_df = pd.read_csv(HARMONIZED_MAP)
    harm_df['code'] = harm_df['code'].astype(str)
    logger.info(f"Loaded {len(harm_df):,} harmonized mappings")

    # Load optional overrides (highest precedence)
    overrides_df = None
    if OVERRIDES_FILE.exists():
        logger.info(f"Loading overrides from: {OVERRIDES_FILE}")
        overrides_df = pd.read_csv(OVERRIDES_FILE)
        overrides_df['code'] = overrides_df['code'].astype(str)
        logger.info(f"Loaded {len(overrides_df):,} override rows")

    # First apply overrides if present
    if overrides_df is not None:
        logger.info("Applying overrides (year-aware)...")
        df = df.merge(
            overrides_df[['code', 'icd_version', 'harmonized_category', 'harmonized_category_name', 'classification_confidence']],
            left_on=['cause', 'icd_version'],
            right_on=['code', 'icd_version'],
            how='left',
            suffixes=(None, '_override')
        )
        # If override exists, take its values
        for col in ['harmonized_category', 'harmonized_category_name', 'classification_confidence']:
            df[col] = df[f"{col}_override"].combine_first(df[col])
        df = df.drop(columns=[c for c in df.columns if c.endswith('_override')] + ['code'], errors='ignore')

    # Then apply default mapping for remaining rows
    logger.info("Merging harmonized categories (defaults, year-aware)...")
    df = df.merge(
        harm_df[['code', 'icd_version', 'harmonized_category', 'harmonized_category_name', 'classification_confidence']],
        left_on=['cause', 'icd_version'],
        right_on=['code', 'icd_version'],
        how='left'
    )
    df = df.drop(columns=['code'], errors='ignore')

    harm_matched = df['harmonized_category'].notna().sum()
    harm_rate = (harm_matched / total) * 100
    logger.info(f"Harmonization match rate: {harm_matched:,} / {total:,} ({harm_rate:.1f}%)")
    
    # Reorder columns
    final_cols = ['year', 'cause', 'cause_description', 'harmonized_category', 
                  'harmonized_category_name', 'classification_confidence', 'sex', 'age', 'deaths']
    df = df[final_cols]
    
    # Save output
    output_file = BASE_DIR / "uk_mortality_by_cause_1901_2000_harmonized.csv"
    logger.info(f"\nSaving to: {output_file}")
    df.to_csv(output_file, index=False)
    logger.info(f"✅ Saved {len(df):,} rows")
    
    # Show sample stats
    logger.info("\n📊 Final Statistics:")
    logger.info(f"Year range: {df['year'].min()}-{df['year'].max()}")
    logger.info(f"Harmonized categories: {df['harmonized_category_name'].nunique()}")
    logger.info(f"Unique causes: {df['cause'].nunique()}")
    logger.info("\nTop 5 categories by deaths:")
    top_cats = df.groupby('harmonized_category_name')['deaths'].sum().nlargest(5)
    for cat, deaths in top_cats.items():
        logger.info(f"  {cat}: {deaths:,}")


if __name__ == "__main__":
    main()
