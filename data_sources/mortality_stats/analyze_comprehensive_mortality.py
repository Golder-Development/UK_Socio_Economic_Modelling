"""
Comprehensive UK mortality analysis using existing local data and API supplements.
Extracts:
1. Total deaths by year (1900s-present)
2. Deaths by cause (ICD-10 codes) where available
3. Combined from multiple sources:
   - Local CSV files (compiled_mortality_2001_2019.csv, compiled_mortality_21c_2017.csv)
   - ONS API (2020-2025)
   - Future: Add more historical files as needed
"""
import pandas as pd
import logging
from pathlib import Path
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent


def load_compiled_mortality_2001_2019():
    """Load the compiled mortality 2001-2019 CSV with ICD codes."""
    file_path = DATA_DIR / "compiled_mortality_2001_2019.csv"
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    
    logger.info(f"Loading: {file_path.name}")
    df = pd.read_csv(file_path, low_memory=False)
    logger.info(f"  Shape: {df.shape}")
    logger.info(f"  Columns: {list(df.columns)}")
    
    return df


def load_compiled_mortality_21c_2017():
    """Load the 21st century mortality CSV."""
    file_path = DATA_DIR / "compiled_mortality_21c_2017.csv"
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    
    logger.info(f"Loading: {file_path.name}")
    df = pd.read_csv(file_path, low_memory=False)
    logger.info(f"  Shape: {df.shape}")
    logger.info(f"  Columns: {list(df.columns)}")
    
    return df


def load_api_data():
    """Load the API-fetched data for all available years."""
    file_path = DATA_DIR / "uk_mortality_totals_by_year.csv"
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    
    logger.info(f"Loading: {file_path.name}")
    df = pd.read_csv(file_path)
    logger.info(f"  Shape: {df.shape}")
    logger.info(f"  Year range: {df['year'].min():.0f} - {df['year'].max():.0f}")
    
    return df


def extract_yearly_totals(df, year_col='YR', deaths_col='NDTHS'):
    """Extract yearly death totals from a dataframe."""
    if year_col not in df.columns or deaths_col not in df.columns:
        logger.warning(f"Columns not found: {year_col}, {deaths_col}")
        return None
    
    # Convert to numeric
    df['year'] = pd.to_numeric(df[year_col], errors='coerce')
    df['deaths'] = pd.to_numeric(df[deaths_col], errors='coerce')
    
    # Filter valid
    df_valid = df[df['year'].notna() & df['deaths'].notna()].copy()
    
    # Group by year
    yearly = df_valid.groupby('year', as_index=False)['deaths'].sum()
    yearly.columns = ['year', 'total_deaths']
    yearly['year'] = yearly['year'].astype(int)
    yearly['total_deaths'] = yearly['total_deaths'].astype(int)
    
    return yearly


def extract_deaths_by_cause(df, year_col='YR', icd_col='ICD-10', deaths_col='NDTHS'):
    """Extract deaths by ICD-10 cause code and year."""
    required_cols = [year_col, icd_col, deaths_col]
    if not all(col in df.columns for col in required_cols):
        logger.warning(f"Columns not found: {required_cols}")
        return None
    
    # Convert to numeric
    df['year'] = pd.to_numeric(df[year_col], errors='coerce')
    df['deaths'] = pd.to_numeric(df[deaths_col], errors='coerce')
    df['icd10'] = df[icd_col].astype(str).str.strip()
    
    # Filter valid
    df_valid = df[df['year'].notna() & df['deaths'].notna() & (df['icd10'] != '')].copy()
    
    # Extract ICD-10 chapter (first letter)
    df_valid['icd10_chapter'] = df_valid['icd10'].str[0]
    
    # Group by year and ICD chapter
    by_cause = df_valid.groupby(['year', 'icd10_chapter'], as_index=False)['deaths'].sum()
    by_cause.columns = ['year', 'icd10_chapter', 'total_deaths']
    by_cause['year'] = by_cause['year'].astype(int)
    by_cause['total_deaths'] = by_cause['total_deaths'].astype(int)
    
    # Also get detailed ICD codes (top causes)
    by_code = df_valid.groupby(['year', 'icd10'], as_index=False)['deaths'].sum()
    by_code.columns = ['year', 'icd10_code', 'total_deaths']
    by_code['year'] = by_code['year'].astype(int)
    by_code['total_deaths'] = by_code['total_deaths'].astype(int)
    
    return by_cause, by_code


def get_icd10_chapter_names():
    """Return mapping of ICD-10 chapter codes to names."""
    return {
        'A': 'Certain infectious and parasitic diseases (A00-B99)',
        'B': 'Certain infectious and parasitic diseases (A00-B99)',
        'C': 'Neoplasms (C00-D48)',
        'D': 'Neoplasms / Blood diseases (D00-D89)',
        'E': 'Endocrine, nutritional and metabolic diseases (E00-E90)',
        'F': 'Mental and behavioural disorders (F00-F99)',
        'G': 'Diseases of the nervous system (G00-G99)',
        'H': 'Diseases of the eye/ear (H00-H95)',
        'I': 'Diseases of the circulatory system (I00-I99)',
        'J': 'Diseases of the respiratory system (J00-J99)',
        'K': 'Diseases of the digestive system (K00-K93)',
        'L': 'Diseases of the skin (L00-L99)',
        'M': 'Diseases of the musculoskeletal system (M00-M99)',
        'N': 'Diseases of the genitourinary system (N00-N99)',
        'O': 'Pregnancy, childbirth and the puerperium (O00-O99)',
        'P': 'Certain conditions originating in the perinatal period (P00-P96)',
        'Q': 'Congenital malformations (Q00-Q99)',
        'R': 'Symptoms, signs and abnormal findings (R00-R99)',
        'S': 'Injury, poisoning (S00-T98)',
        'T': 'Injury, poisoning (S00-T98)',
        'V': 'External causes of morbidity and mortality (V01-Y98)',
        'W': 'External causes of morbidity and mortality (V01-Y98)',
        'X': 'External causes of morbidity and mortality (V01-Y98)',
        'Y': 'External causes of morbidity and mortality (V01-Y98)',
        'Z': 'Factors influencing health status (Z00-Z99)'
    }


def main():
    """Main entry point."""
    logger.info("=" * 70)
    logger.info("Comprehensive UK Mortality Analysis")
    logger.info("=" * 70)
    
    all_yearly_totals = []
    all_cause_data = []
    
    # 1. Load and process 2001-2019 data
    logger.info("\n" + "=" * 70)
    logger.info("Processing: compiled_mortality_2001_2019.csv")
    logger.info("=" * 70)
    
    df_2001_2019 = load_compiled_mortality_2001_2019()
    if df_2001_2019 is not None:
        # Extract yearly totals
        yearly = extract_yearly_totals(df_2001_2019)
        if yearly is not None:
            logger.info(f"✓ Extracted {len(yearly)} years: {yearly['year'].min()}-{yearly['year'].max()}")
            all_yearly_totals.append(yearly)
        
        # Extract deaths by cause
        by_cause, by_code = extract_deaths_by_cause(df_2001_2019)
        if by_cause is not None:
            logger.info(f"✓ Extracted {len(by_cause)} cause records")
            all_cause_data.append(by_cause)
    
    # 2. Load and process 21c_2017 data
    logger.info("\n" + "=" * 70)
    logger.info("Processing: compiled_mortality_21c_2017.csv")
    logger.info("=" * 70)
    
    df_21c = load_compiled_mortality_21c_2017()
    if df_21c is not None:
        # This file has different structure, check columns
        if 'YR' in df_21c.columns and 'NDTHS' in df_21c.columns:
            yearly = extract_yearly_totals(df_21c)
            if yearly is not None:
                logger.info(f"✓ Extracted {len(yearly)} years: {yearly['year'].min()}-{yearly['year'].max()}")
                all_yearly_totals.append(yearly)
            
            by_cause, by_code = extract_deaths_by_cause(df_21c)
            if by_cause is not None:
                logger.info(f"✓ Extracted {len(by_cause)} cause records")
                all_cause_data.append(by_cause)
    
    # 3. Load API data for all years
    logger.info("\n" + "=" * 70)
    logger.info("Processing: API data (2010-2025)")
    logger.info("=" * 70)
    
    df_api = load_api_data()
    if df_api is not None:
        logger.info(f"✓ Loaded {len(df_api)} years from API: {df_api['year'].min():.0f}-{df_api['year'].max():.0f}")
        all_yearly_totals.append(df_api)
    
    # 4. Combine all yearly totals
    logger.info("\n" + "=" * 70)
    logger.info("Combining all data sources...")
    logger.info("=" * 70)
    
    if all_yearly_totals:
        combined_yearly = pd.concat(all_yearly_totals, ignore_index=True)
        combined_yearly = combined_yearly.sort_values('year')
        
        # For overlapping years, take the max to avoid duplicates
        combined_yearly = combined_yearly.groupby('year', as_index=False)['total_deaths'].max()
        
        # Save
        output_file = DATA_DIR / "uk_mortality_comprehensive.csv"
        combined_yearly.to_csv(output_file, index=False)
        
        logger.info(f"\n✓ Saved comprehensive totals: {output_file}")
        logger.info(f"✓ Years covered: {len(combined_yearly)}")
        logger.info(f"✓ Range: {combined_yearly['year'].min():.0f} - {combined_yearly['year'].max():.0f}")
        logger.info(f"\n📊 Yearly totals:")
        print(combined_yearly.to_string(index=False))
    
    # 5. Save deaths by cause
    if all_cause_data:
        combined_cause = pd.concat(all_cause_data, ignore_index=True)
        combined_cause = combined_cause.sort_values(['year', 'icd10_chapter'])
        combined_cause = combined_cause.groupby(['year', 'icd10_chapter'], as_index=False)['total_deaths'].sum()
        
        # Add chapter names
        chapter_names = get_icd10_chapter_names()
        combined_cause['cause_category'] = combined_cause['icd10_chapter'].map(chapter_names)
        
        # Save
        output_file = DATA_DIR / "uk_mortality_by_cause.csv"
        combined_cause.to_csv(output_file, index=False)
        
        logger.info(f"\n✓ Saved deaths by cause: {output_file}")
        logger.info(f"✓ Records: {len(combined_cause)}")
        logger.info(f"\n📊 Sample (top causes in 2019):")
        sample = combined_cause[combined_cause['year'] == 2019].nlargest(10, 'total_deaths')
        print(sample[['year', 'icd10_chapter', 'cause_category', 'total_deaths']].to_string(index=False))


if __name__ == "__main__":
    main()
