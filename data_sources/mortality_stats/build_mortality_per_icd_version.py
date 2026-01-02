"""
Build mortality dataset by processing each ICD version independently.
Per-version code description matching (NO cross-version lookup).
Output: Compiled by-cause file with ICD version column.
"""

import pandas as pd
import logging
from pathlib import Path
import zipfile
import io
import warnings

warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent
ONS_DOWNLOADS = DATA_DIR / "ons_downloads" / "extracted"

# ICD version definitions: (file, year_range, sheet_pattern, code_column_name)
ICD_VERSIONS = [
    ("icd1.xls", (1901, 1910), "ICD1", "icd_1"),
    ("icd2.xls", (1911, 1920), "icd2_[12]", "ICD_"),
    ("icd3.xls", (1921, 1930), "icd3_[12]", "ICD_3"),
    ("icd4.xls", (1931, 1939), "icd4_[12]", "ICD_4"),
    ("icd5.xls", (1940, 1949), "icd5_[12]", "ICD_5"),
    ("icd6.xls", (1950, 1957), "icd6_[12]", "ICD_6"),
    ("icd7.xlsx", (1958, 1967), "icd7_[123]", "ICD_7"),
    ("icd8.xls", (1968, 1978), "icd8_[123]", "ICD_8"),
    ("icd9_a.xlsx", (1979, 1984), "icd9_[12]", "ICD_9"),
    ("icd9_b.xls", (1985, 1993), "icd9_[345]", "ICD_9"),
    ("icd9_c.xls", (1994, 2000), "icd9_[678]", "ICD_9"),
]


def load_icd_version_data(file_pattern, year_range, sheet_pattern, code_col):
    """Load all data sheets for an ICD version, return combined DataFrame."""
    file_path = ONS_DOWNLOADS / file_pattern
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return pd.DataFrame()
    
    logger.info(f"Loading {file_pattern}")
    
    try:
        xls = pd.ExcelFile(file_path)
        dfs = []
        
        import re
        sheet_pattern_re = re.compile(sheet_pattern, re.IGNORECASE)
        
        for sheet_name in xls.sheet_names:
            if not sheet_pattern_re.search(sheet_name):
                continue
            
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                if df.empty:
                    continue
                
                # Standardize column names
                df.columns = df.columns.str.lower().str.strip()
                
                # Find year column
                year_col = None
                for col in df.columns:
                    if 'yr' in col or 'year' in col:
                        year_col = col
                        break
                
                if year_col is None:
                    logger.warning(f"  No year column found in sheet {sheet_name}")
                    continue
                
                # Filter by year range
                df['year'] = pd.to_numeric(df[year_col], errors='coerce')
                df = df[df['year'].between(year_range[0], year_range[1])]
                
                if not df.empty:
                    logger.debug(f"  Loaded sheet '{sheet_name}': {len(df)} rows")
                    dfs.append(df)
            
            except Exception as e:
                logger.warning(f"  Error reading sheet {sheet_name}: {e}")
                continue
        
        if dfs:
            combined = pd.concat(dfs, ignore_index=True, sort=False)
            logger.info(f"  Total: {len(combined)} rows, years {combined['year'].min():.0f}-{combined['year'].max():.0f}")
            return combined
        
        return pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Error loading {file_pattern}: {e}")
        return pd.DataFrame()


def get_descriptions_from_icd_sheet(file_pattern):
    """Extract code descriptions from the 'description' sheet of an ICD Excel file."""
    file_path = ONS_DOWNLOADS / file_pattern
    if not file_path.exists():
        return {}
    
    try:
        xls = pd.ExcelFile(file_path)
        desc_sheet = None
        
        for sheet in xls.sheet_names:
            if 'descr' in sheet.lower():
                desc_sheet = sheet
                break
        
        if not desc_sheet:
            logger.warning(f"No description sheet found in {file_pattern}")
            return {}
        
        df_desc = pd.read_excel(file_path, sheet_name=desc_sheet)
        
        # Find code and description columns
        code_col = None
        desc_col = None
        
        for col in df_desc.columns:
            if 'code' in col.lower() or col.lower() in ['icd', 'icd_1']:
                code_col = col
            if 'descr' in col.lower() or 'meaning' in col.lower() or col.lower() == 'title':
                desc_col = col
        
        if code_col is None or desc_col is None:
            logger.warning(f"Could not find code/description columns in {file_pattern}")
            return {}
        
        # Create mapping
        df_desc[code_col] = df_desc[code_col].astype(str).str.strip()
        df_desc[desc_col] = df_desc[desc_col].astype(str).str.strip()
        
        desc_map = dict(zip(df_desc[code_col], df_desc[desc_col]))
        logger.info(f"  Loaded {len(desc_map)} descriptions from {file_pattern}")
        return desc_map
    
    except Exception as e:
        logger.warning(f"Error extracting descriptions from {file_pattern}: {e}")
        return {}


def standardize_icd_data(df, icd_version_name, code_col):
    """Standardize a single ICD version's data."""
    if df.empty:
        return df
    
    df = df.copy()
    df.columns = df.columns.str.lower().str.strip()
    
    # Find and normalize code column (may be 'icd_1', 'icd_', 'icd_3', etc)
    code_col_lower = code_col.lower()
    actual_code_col = None
    
    for col in df.columns:
        if col == code_col_lower or col == code_col_lower.replace('_', '').lower():
            actual_code_col = col
            break
    
    if actual_code_col is None:
        logger.warning(f"  Could not find code column '{code_col}' in {icd_version_name}")
        logger.warning(f"  Available columns: {df.columns.tolist()}")
        return pd.DataFrame()
    
    df['cause'] = df[actual_code_col].astype(str).str.strip()
    
    # Standardize other columns
    if 'yr' in df.columns:
        df['year'] = pd.to_numeric(df['yr'], errors='coerce')
    elif 'year' in df.columns:
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
    else:
        logger.warning(f"  No year column found in {icd_version_name}")
        return pd.DataFrame()
    
    # Sex standardization
    if 'sex' in df.columns:
        df['sex'] = df['sex'].astype(str).str.lower()
        df['sex'] = df['sex'].replace({
            '1': 'Male', 'male': 'Male', 'm': 'Male',
            '2': 'Female', 'female': 'Female', 'f': 'Female',
            '': 'All', 'all': 'All'
        })
    else:
        df['sex'] = 'All'
    
    # Age standardization
    if 'age' not in df.columns:
        df['age'] = 'All ages'
    else:
        df['age'] = df['age'].astype(str).str.strip()
    
    # Deaths
    deaths_col = None
    for col in df.columns:
        if 'ndth' in col or 'death' in col or 'count' in col:
            deaths_col = col
            break
    
    if deaths_col:
        df['deaths'] = pd.to_numeric(df[deaths_col], errors='coerce')
    else:
        df['deaths'] = 1
    
    # Add ICD version
    df['icd_version'] = icd_version_name
    
    # Select standard columns
    keep_cols = ['year', 'cause', 'sex', 'age', 'deaths', 'icd_version']
    df = df[[c for c in keep_cols if c in df.columns]]
    
    # Filter
    df = df.dropna(subset=['year', 'deaths'])
    df = df[df['deaths'] > 0]
    
    return df


def main():
    logger.info("\n" + "=" * 70)
    logger.info("BUILDING MORTALITY DATASET BY ICD VERSION")
    logger.info("=" * 70)
    
    all_data = []
    
    for file_pattern, year_range, sheet_pattern, code_col in ICD_VERSIONS:
        icd_version_name = file_pattern.split('.')[0].upper()
        if icd_version_name.startswith('ICD'):
            icd_version_name = icd_version_name  # e.g., "ICD1", "ICD2"
        else:
            icd_version_name = "ICD-" + icd_version_name.split('_')[1][0]  # e.g., "ICD-9" from "ICD9_A"
        
        logger.info(f"\n{icd_version_name} ({year_range[0]}-{year_range[1]})")
        logger.info("-" * 70)
        
        # Load data
        df = load_icd_version_data(file_pattern, year_range, sheet_pattern, code_col)
        if df.empty:
            logger.warning(f"  No data loaded for {icd_version_name}")
            continue
        
        # Get descriptions
        desc_map = get_descriptions_from_icd_sheet(file_pattern)
        
        # Standardize
        df = standardize_icd_data(df, icd_version_name, code_col)
        if df.empty:
            logger.warning(f"  No valid records for {icd_version_name}")
            continue
        
        # Attach descriptions
        df['cause_description'] = df['cause'].map(desc_map)
        matched_desc = df['cause_description'].notna().sum()
        total = len(df)
        match_pct = (matched_desc / total * 100) if total > 0 else 0
        logger.info(f"  Descriptions matched: {matched_desc:,} / {total:,} ({match_pct:.1f}%)")
        
        # For unmatched descriptions, use cause as fallback
        df['cause_description'] = df['cause_description'].fillna(df['cause'])
        
        all_data.append(df)
    
    if not all_data:
        logger.error("No data loaded from any ICD version!")
        return False
    
    # Combine all versions
    logger.info(f"\n{'=' * 70}")
    logger.info("COMBINING ALL ICD VERSIONS")
    logger.info("=" * 70)
    
    combined = pd.concat(all_data, ignore_index=True, sort=False)
    logger.info(f"Total records: {len(combined):,}")
    logger.info(f"Year range: {combined['year'].min():.0f} - {combined['year'].max():.0f}")
    logger.info(f"ICD versions: {sorted(combined['icd_version'].unique())}")
    
    # Save compiled file as ZIP (avoids GitHub size limits)
    output_file_csv = DATA_DIR / "uk_mortality_by_cause_1901_onwards_compiled.csv"
    output_file_zip = DATA_DIR / "uk_mortality_by_cause_1901_onwards_compiled.zip"
    
    # Save as CSV temporarily, then ZIP it
    combined.to_csv(output_file_csv, index=False)
    logger.info(f"\n[OK] Compiled mortality file created: {output_file_csv.name}")
    
    # Compress to ZIP
    import zipfile
    with zipfile.ZipFile(output_file_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(output_file_csv, output_file_csv.name)
    
    # Remove CSV version
    output_file_csv.unlink()
    
    logger.info(f"[OK] Compressed to ZIP: {output_file_zip.name}")
    logger.info(f"     {len(combined):,} records")
    
    # Summary by ICD version
    logger.info(f"\nRecords by ICD version:")
    for version in sorted(combined['icd_version'].unique()):
        count = len(combined[combined['icd_version'] == version])
        print(f"  {version}: {count:,}")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
