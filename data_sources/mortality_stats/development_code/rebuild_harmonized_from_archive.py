"""
Rebuild harmonized mortality data using the correct source file.
The current harmonized files used corrupted data with "Unknown" causes post-1910.
This script uses the archived comprehensive file which has proper ICD codes throughout.
"""

import pandas as pd
from pathlib import Path
import logging
import zipfile

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
ARCHIVE_DIR = BASE_DIR / "development_code" / "archive_csv"
# Use freshly built comprehensive by-cause dataset (preferred over archived CSV)
SOURCE_ZIP = BASE_DIR / "uk_mortality_by_cause_1901_2025.zip"
SOURCE_INNER = "uk_mortality_by_cause_1901_2025.csv"
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
    src_display = SOURCE_ZIP if SOURCE_ZIP.exists() else (BASE_DIR / SOURCE_INNER)
    logger.info(f"Source: {src_display}")
    
    # Load source data
    logger.info("Loading source mortality data...")
    if SOURCE_ZIP.exists():
        with zipfile.ZipFile(SOURCE_ZIP, 'r') as zf:
            with zf.open(SOURCE_INNER) as f:
                df = pd.read_csv(f)
    else:
        # Fallback to CSV if zip not found
        df = pd.read_csv(BASE_DIR / SOURCE_INNER)
    # Filter cause rows only if present (prefer by-cause file)
    if 'cause' in df.columns:
        df = df[df['cause'].notna()]
    # Limit to years covered by harmonization mappings (<= 2000)
    df = df[df["year"] <= 2000].copy()
    logger.info(f"Loaded {len(df):,} rows ({df['year'].min()}-{df['year'].max()})")
    logger.info(f"Unique causes by decade:")
    for year in [1901, 1911, 1921, 1931, 1941, 1951, 1961, 1971, 1981, 1991]:
        subset = df[df['year']==year]
        if len(subset) > 0:
            logger.info(f"  {year}: {subset['cause'].nunique()} unique causes")
    
    # Add ICD version column
    logger.info("\nAdding ICD version...")
    df['icd_version'] = df['year'].apply(get_icd_version_for_year)
    
    # Normalize cause codes to align with description code formats per ICD version
    def normalize_code(val, version):
        s = str(val).strip()
        if version.startswith("ICD-1"):
            # ICD-1 descriptions use integers with trailing .0 (e.g., 10.0, 20.0)
            try:
                f = float(s)
                if f.is_integer():
                    return f"{int(f)}.0"
                return s
            except ValueError:
                return s
        elif version.startswith(("ICD-6", "ICD-7", "ICD-8", "ICD-9")):
            # ICD-6 onwards use zero-padded codes: 10.0 → "0010", 1000.0 → "1000"
            try:
                f = float(s)
                if f.is_integer():
                    code_int = int(f)
                    # Pad to 4 digits for most codes, but preserve longer codes
                    return str(code_int).zfill(4) if code_int < 10000 else str(code_int)
                # Handle codes like "100A" that may already be strings
                return s
            except ValueError:
                return s
        # ICD-2 through ICD-5 use simple integer or alphanumeric codes
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
        # Support commented example rows; ignore lines starting with '#'
        overrides_df = pd.read_csv(OVERRIDES_FILE, comment='#')
        overrides_df['code'] = overrides_df['code'].astype(str)
        logger.info(f"Loaded {len(overrides_df):,} override rows")

    # Ensure target columns exist before applying overrides/defaults
    for col in ['harmonized_category', 'harmonized_category_name', 'classification_confidence']:
        if col not in df.columns:
            df[col] = pd.NA

    # First apply overrides if present
    if overrides_df is not None and len(overrides_df) > 0:
        logger.info("Applying overrides (year-aware)...")
        # Normalize override codes too
        overrides_df['code'] = overrides_df.apply(
            lambda r: normalize_code(r['code'], r['icd_version']), axis=1
        )
        df = df.merge(
            overrides_df[['code', 'icd_version', 'harmonized_category', 'harmonized_category_name', 'classification_confidence']],
            left_on=['cause', 'icd_version'],
            right_on=['code', 'icd_version'],
            how='left',
            suffixes=(None, '_override')
        )
        # If override exists, take its values - only for columns that have _override version
        override_matched = 0
        for col in ['harmonized_category', 'harmonized_category_name', 'classification_confidence']:
            override_col = f"{col}_override"
            if override_col in df.columns:
                override_matched += df[override_col].notna().sum()
                df[col] = df[override_col].combine_first(df[col])
                df = df.drop(columns=[override_col], errors='ignore')
        if override_matched > 0:
            logger.info(f"Overrides applied to {override_matched // 3:,} rows")
        df = df.drop(columns=['code'] if 'code' in df.columns else [], errors='ignore')

    # Then apply default mapping for remaining rows
    logger.info("Merging harmonized categories (defaults, year-aware)...")
    # Merge defaults unconditionally, then fill only missing values
    df = df.merge(
        harm_df[['code', 'icd_version', 'harmonized_category', 'harmonized_category_name', 'classification_confidence']],
        left_on=['cause', 'icd_version'],
        right_on=['code', 'icd_version'],
        how='left',
        suffixes=(None, '_default')
    )
    # Use defaults for any columns that are still NaN
    for col in ['harmonized_category', 'harmonized_category_name', 'classification_confidence']:
        default_col = f"{col}_default"
        if default_col in df.columns:
            df[col] = df[col].fillna(df[default_col])
            df = df.drop(columns=[default_col], errors='ignore')
    df = df.drop(columns=['code'], errors='ignore')

    harm_matched = df['harmonized_category'].notna().sum()
    harm_rate = (harm_matched / total) * 100
    logger.info(f"Harmonization match rate: {harm_matched:,} / {total:,} ({harm_rate:.1f}%)")
    
    # Show match rate by decade
    logger.info("\nMatch rates by decade:")
    for decade_start in [1901, 1911, 1921, 1931, 1941, 1951, 1961, 1971, 1981, 1991]:
        decade_df = df[df['year'].between(decade_start, decade_start + 9)]
        if len(decade_df) > 0:
            matched = decade_df['harmonized_category'].notna().sum()
            rate = (matched / len(decade_df)) * 100
            logger.info(f"  {decade_start}s: {matched:,}/{len(decade_df):,} ({rate:.1f}%)")
    
    # Reorder columns
    final_cols = ['year', 'cause', 'cause_description', 'harmonized_category', 
                  'harmonized_category_name', 'classification_confidence', 'sex', 'age', 'deaths']
    df = df[final_cols]
    
    # Save output
    output_zip = BASE_DIR / "uk_mortality_by_cause_1901_2000_harmonized.zip"
    logger.info(f"\nSaving to: {output_zip}")
    with zipfile.ZipFile(output_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("uk_mortality_by_cause_1901_2000_harmonized.csv", df.to_csv(index=False))
    logger.info(f"✅ Saved {len(df):,} rows (zipped)")
    
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
