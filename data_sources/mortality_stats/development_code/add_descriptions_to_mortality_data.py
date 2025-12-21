"""
Add cause code descriptions to mortality CSV files.
Merges the ICD code descriptions with the mortality data.
"""

import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent


def add_descriptions_to_mortality_file(input_file, output_file, descriptions_df):
    """Add description column to mortality data file"""
    logger.info(f"\nProcessing {input_file.name}")
    
    # Load mortality data
    df = pd.read_csv(input_file, low_memory=False)
    logger.info(f"  Loaded {len(df):,} rows")
    logger.info(f"  Columns: {df.columns.tolist()}")
    
    # Check if 'cause' column exists
    if 'cause' not in df.columns:
        logger.warning(f"  No 'cause' column found in {input_file.name}, skipping")
        return
    
    # Convert cause to string for matching
    df['cause'] = df['cause'].astype(str).str.strip()
    
    # Prepare descriptions for merging
    desc_lookup = descriptions_df.copy()
    desc_lookup['code'] = desc_lookup['code'].astype(str).str.strip()
    
    # Merge descriptions
    df = df.merge(
        desc_lookup[['code', 'description']], 
        left_on='cause', 
        right_on='code', 
        how='left'
    )
    
    # Drop the extra 'code' column from merge
    if 'code' in df.columns:
        df = df.drop(columns=['code'])
    
    # Rename description column to be more descriptive
    if 'description' in df.columns:
        df = df.rename(columns={'description': 'cause_description'})
    
    # Reorder columns to put description right after cause
    cols = df.columns.tolist()
    if 'cause_description' in cols:
        # Remove cause_description from its current position
        cols.remove('cause_description')
        # Find position of 'cause'
        if 'cause' in cols:
            cause_idx = cols.index('cause')
            # Insert cause_description right after cause
            cols.insert(cause_idx + 1, 'cause_description')
        df = df[cols]
    
    # Count matches
    matched = df['cause_description'].notna().sum()
    total = len(df)
    match_rate = (matched / total * 100) if total > 0 else 0
    
    logger.info(f"  Matched descriptions: {matched:,} / {total:,} ({match_rate:.1f}%)")
    
    # Show some examples of unmatched codes
    unmatched = df[df['cause_description'].isna()]['cause'].unique()
    if len(unmatched) > 0:
        logger.info(f"  Unmatched codes (first 10): {list(unmatched[:10])}")
    
    # Save with descriptions
    df.to_csv(output_file, index=False)
    logger.info(f"  ✓ Saved to: {output_file}")


def main():
    logger.info("=" * 80)
    logger.info("ADDING CAUSE DESCRIPTIONS TO MORTALITY FILES")
    logger.info("=" * 80)
    
    # Load code descriptions
    desc_file = DATA_DIR / "icd_code_descriptions_simplified.csv"
    
    if not desc_file.exists():
        logger.error(f"Description file not found: {desc_file}")
        logger.error("Please run build_code_descriptions.py first")
        return
    
    logger.info(f"\nLoading code descriptions from: {desc_file}")
    descriptions_df = pd.read_csv(desc_file)
    logger.info(f"Loaded {len(descriptions_df):,} code descriptions")
    
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
        output_file = DATA_DIR / filename.replace('.csv', '_with_descriptions.csv')
        
        add_descriptions_to_mortality_file(input_file, output_file, descriptions_df)
    
    logger.info("\n" + "=" * 80)
    logger.info("COMPLETE")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
