"""
Comprehensive UK Mortality Database Builder - Simplified
============================================

Consolidates ALL available mortality data from:
- 1901-2000 (ICD-1 through ICD-9c)
- 2001-2019 (compiled mortality files)

Outputs:
- uk_mortality_comprehensive_1901_2019.csv: Complete dataset with all dimensions
- uk_mortality_yearly_totals_1901_2019.csv: Annual death totals
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent
ONS_DOWNLOADS = DATA_DIR / "ons_downloads" / "extracted"


def load_historical_1901_2000():
    """Load all ICD1-ICD9 files (1901-2000)"""
    logger.info("=" * 70)
    logger.info("LOADING HISTORICAL DATA (1901-2000)")
    logger.info("=" * 70)
    
    all_data = []
    files = [
        ("icd1.xls", "ICD1"),
        ("icd2.xls", "icd2_1"),
        ("icd3.xls", "icd3_1"),
        ("icd4.xls", "icd4_1"),
        ("icd5.xls", "icd5_1"),
        ("icd6.xls", "icd6_1"),
        ("icd7.xlsx", "icd7_1"),
        ("icd8.xls", "icd8_1"),
        ("icd9_a.xlsx", "icd9_1"),
        ("icd9_b.xls", "icd9_3"),
        ("icd9_c.xls", "icd9_6"),
    ]
    
    for filename, sheet_name in files:
        filepath = ONS_DOWNLOADS / filename
        if not filepath.exists():
            logger.warning(f"File not found: {filepath.name}")
            continue
        
        try:
            logger.info(f"Loading {filename}...")
            df = pd.read_excel(filepath, sheet_name=sheet_name)
            
            if not df.empty:
                # Standardize columns
                df.columns = df.columns.str.lower().str.strip()
                
                # Ensure we have the key columns
                if 'yr' in df.columns:
                    df['year'] = df['yr']
                
                # Find deaths column
                death_cols = [c for c in df.columns if 'ndth' in c or 'death' in c]
                if death_cols:
                    df['deaths'] = df[death_cols[0]]
                
                # Find cause columns (ICD code)
                cause_cols = [c for c in df.columns if 'icd' in c]
                if cause_cols:
                    df['cause'] = df[cause_cols[0]].astype(str).str.strip()
                    df['cause'] = df['cause'].replace(['nan', 'NaN', 'None'], 'Unknown')
                else:
                    df['cause'] = 'Unknown'
                
                # Normalize sex: 1=Male, 2=Female
                if 'sex' in df.columns:
                    df['sex'] = df['sex'].astype(str).map({
                        '1': 'Male', '1.0': 'Male',
                        '2': 'Female', '2.0': 'Female',
                    }).fillna('All')
                else:
                    df['sex'] = 'All'
                
                # Keep age as is
                if 'age' not in df.columns:
                    df['age'] = 'All ages'
                
                # Select and clean
                df = df[['year', 'cause', 'sex', 'age', 'deaths']].copy()
                df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
                df['deaths'] = pd.to_numeric(df['deaths'], errors='coerce').astype('Int64')
                
                df = df.dropna(subset=['year', 'deaths'])
                df = df[df['deaths'] > 0]
                
                logger.info(f"  ✓ {len(df):,} rows ({df['year'].min():.0f}-{df['year'].max():.0f})")
                all_data.append(df)
            else:
                logger.warning(f"  ⚠ Empty sheet {sheet_name}")
                
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
    
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        logger.info(f"\nHistorical total: {len(combined):,} records ({combined['year'].min():.0f}-{combined['year'].max():.0f})")
        return combined
    
    return pd.DataFrame()


def load_compiled_2001_2019():
    """Load the compiled mortality data for 2001-2019"""
    logger.info("\n" + "=" * 70)
    logger.info("LOADING COMPILED DATA (2001-2019)")
    logger.info("=" * 70)
    
    filepath = DATA_DIR / "downloaded_sourcefiles" / "compiled_mortality_2001_2019.csv"
    
    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return pd.DataFrame()
    
    try:
        logger.info(f"Loading {filepath.name}...")
        df = pd.read_csv(filepath, low_memory=False)
        
        # Standardize columns
        df.columns = df.columns.str.lower().str.strip()
        
        # Create standard columns
        df['year'] = pd.to_numeric(df.get('yr', df.get('year')), errors='coerce').astype('Int64')
        
        # Cause is ICD-10 code
        icd_cols = [c for c in df.columns if 'icd' in c]
        if icd_cols:
            df['cause'] = df[icd_cols[0]].astype(str).str.strip()
            df['cause'] = df['cause'].replace(['nan', 'NaN', 'None'], 'Unknown')
        else:
            df['cause'] = 'Unknown'
        
        # Sex: 1=Male, 2=Female
        if 'sex' in df.columns:
            df['sex'] = df['sex'].astype(str).map({
                '1': 'Male', '1.0': 'Male',
                '2': 'Female', '2.0': 'Female',
            }).fillna('All')
        else:
            df['sex'] = 'All'
        
        # Keep age as is
        if 'age' not in df.columns:
            df['age'] = 'All ages'
        
        # Deaths
        death_cols = [c for c in df.columns if 'ndth' in c or 'death' in c]
        if death_cols:
            df['deaths'] = pd.to_numeric(df[death_cols[0]], errors='coerce').astype('Int64')
        else:
            df['deaths'] = 0
        
        # Select and clean
        df = df[['year', 'cause', 'sex', 'age', 'deaths']].copy()
        df = df.dropna(subset=['year', 'deaths'])
        df = df[df['deaths'] > 0]
        
        logger.info(f"  ✓ {len(df):,} rows ({df['year'].min():.0f}-{df['year'].max():.0f})")
        return df
        
    except Exception as e:
        logger.error(f"Failed to load {filepath.name}: {e}")
        return pd.DataFrame()


def main():
    logger.info("\n")
    logger.info("╔" + "═" * 68 + "╗")
    logger.info("║" + " " * 68 + "║")
    logger.info("║" + "UK MORTALITY COMPREHENSIVE DATABASE BUILDER".center(68) + "║")
    logger.info("║" + "1901-2019 Complete Historical Dataset".center(68) + "║")
    logger.info("║" + " " * 68 + "║")
    logger.info("╚" + "═" * 68 + "╝")
    logger.info("")
    
    # Load all data
    hist_1901_2000 = load_historical_1901_2000()
    comp_2001_2019 = load_compiled_2001_2019()
    
    # Combine
    logger.info("\n" + "=" * 70)
    logger.info("CONSOLIDATING DATA")
    logger.info("=" * 70)
    
    if hist_1901_2000.empty and comp_2001_2019.empty:
        logger.error("No data loaded!")
        return False
    
    if not hist_1901_2000.empty and not comp_2001_2019.empty:
        all_data = pd.concat([hist_1901_2000, comp_2001_2019], ignore_index=True)
        logger.info(f"Combined: {len(all_data):,} records")
    elif not hist_1901_2000.empty:
        all_data = hist_1901_2000
        logger.info(f"Using historical data only: {len(all_data):,} records")
    else:
        all_data = comp_2001_2019
        logger.info(f"Using compiled data only: {len(all_data):,} records")
    
    # Aggregate by year, cause, sex, age
    logger.info("\nAggregating by dimensions...")
    summary = all_data.groupby(['year', 'cause', 'sex', 'age'], as_index=False, dropna=False)['deaths'].sum()
    summary = summary.sort_values(['year', 'cause', 'sex', 'age'])
    logger.info(f"Created {len(summary):,} summary records")
    
    # Create yearly totals
    logger.info("Creating yearly totals...")
    yearly = all_data.groupby('year', as_index=False)['deaths'].sum()
    yearly.columns = ['year', 'total_deaths']
    yearly = yearly.sort_values('year')
    logger.info(f"Created {len(yearly):,} yearly records")
    
    # Save outputs
    logger.info("\n" + "=" * 70)
    logger.info("SAVING OUTPUTS")
    logger.info("=" * 70)
    
    out_comprehensive = DATA_DIR / "uk_mortality_comprehensive_1901_2019.csv"
    out_yearly = DATA_DIR / "uk_mortality_yearly_totals_1901_2019.csv"
    
    summary.to_csv(out_comprehensive, index=False)
    logger.info(f"✓ Saved comprehensive: {out_comprehensive.name} ({len(summary):,} records)")
    
    yearly.to_csv(out_yearly, index=False)
    logger.info(f"✓ Saved yearly totals: {out_yearly.name} ({len(yearly):,} records)")
    
    # Summary statistics
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 70)
    logger.info(f"\nYearly Data (1901-2019):")
    logger.info(f"  Total years: {len(yearly)}")
    logger.info(f"  Year range: {yearly['year'].min():.0f} - {yearly['year'].max():.0f}")
    logger.info(f"  Total deaths all time: {yearly['total_deaths'].sum():,.0f}")
    logger.info(f"  Average annual deaths: {yearly['total_deaths'].mean():,.0f}")
    logger.info(f"  Min year: {yearly.loc[yearly['total_deaths'].idxmin(), 'year']:.0f} ({yearly['total_deaths'].min():,.0f} deaths)")
    logger.info(f"  Max year: {yearly.loc[yearly['total_deaths'].idxmax(), 'year']:.0f} ({yearly['total_deaths'].max():,.0f} deaths)")
    
    logger.info(f"\nDimensions in comprehensive dataset:")
    logger.info(f"  Years: {summary['year'].min():.0f} - {summary['year'].max():.0f} ({summary['year'].nunique()} distinct)")
    logger.info(f"  Causes: {summary['cause'].nunique()} distinct")
    logger.info(f"  Sexes: {summary['sex'].unique().tolist()}")
    logger.info(f"  Age groups: {summary['age'].nunique()} distinct")
    
    logger.info("\n" + "=" * 70)
    logger.info("✓ BUILD COMPLETE!")
    logger.info("=" * 70 + "\n")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
