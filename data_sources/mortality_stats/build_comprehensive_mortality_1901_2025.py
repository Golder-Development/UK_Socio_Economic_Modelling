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
import zipfile
import io

warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent
ONS_DOWNLOADS = DATA_DIR / "ons_downloads" / "extracted"


def add_cause_descriptions(df):
    """
    Add cause descriptions to dataframe if 'cause' column exists.
    Preserves existing ICD10 descriptions for modern data (2001+).
    """
    if 'cause' not in df.columns:
        return df

    desc_file = DATA_DIR / "icd_code_descriptions_simplified.csv"

    if not desc_file.exists():
        logger.warning("Code descriptions file not found. Run build_code_descriptions.py first.")
        return df

    try:
        logger.info("Loading code descriptions...")
        descriptions_df = pd.read_csv(desc_file)
        descriptions_df['code'] = descriptions_df['code'].astype(str).str.strip()

        # Convert cause to string for matching
        df_copy = df.copy()
        df_copy['cause'] = df_copy['cause'].astype(str).str.strip()

        # Merge descriptions
        df_copy = df_copy.merge(
            descriptions_df[['code', 'description']],
            left_on='cause',
            right_on='code',
            how='left'
        )

        # Drop the extra 'code' column from merge
        if 'code' in df_copy.columns:
            df_copy = df_copy.drop(columns=['code'])

        # Rename description column
        if 'description' in df_copy.columns:
            df_copy = df_copy.rename(columns={'description': 'cause_description'})

        # For ICD-10 data (2001+), prefer the ICD10 descriptions if available
        if 'icd10_description' in df_copy.columns and 'cause_description' in df_copy.columns:
            # Keep ICD10 descriptions where they exist (they're more specific)
            mask = df_copy['icd10_description'].notna()
            df_copy.loc[mask, 'cause_description'] = df_copy.loc[mask, 'icd10_description']
            # Drop the icd10_description column as we've merged it into cause_description
            df_copy = df_copy.drop(columns=['icd10_description'])
            logger.debug(f"Preserved {mask.sum()} ICD-10 descriptions in cause_description")

        # Reorder columns to put description right after cause
        cols = df_copy.columns.tolist()
        if 'cause_description' in cols:
            cols.remove('cause_description')
            if 'cause' in cols:
                cause_idx = cols.index('cause')
                cols.insert(cause_idx + 1, 'cause_description')
            df_copy = df_copy[cols]

        # Count matches
        matched = df_copy['cause_description'].notna().sum()
        total = len(df_copy)
        match_rate = (matched / total * 100) if total > 0 else 0
        logger.info(f"Added descriptions: {matched:,} / {total:,} ({match_rate:.1f}%)")

        return df_copy
    except Exception as e:
        logger.error(f"Error adding descriptions: {e}")
        return df


def _detect_header_row(df_like):
    """Attempt to detect the header row index in a DataFrame read with header=None."""
    try:
        # search first 25 rows for any cell containing year keywords
        max_rows = min(25, len(df_like))
        year_keywords = ['year', 'yr', 'year of death']
        for i in range(max_rows):
            row_vals = df_like.iloc[i].astype(str).str.lower().tolist()
            if any(any(kw in val for kw in year_keywords) for val in row_vals):
                return i
        return None
    except Exception:
        return None


def _clean_and_filter_years(df, year_range=None):
    """Normalize year column and filter plausible rows."""
    # unify columns to lowercase for detection, robust to non-string names
    df.columns = df.columns.map(lambda x: str(x).strip())
    lower_cols = pd.Index([str(c).lower() for c in df.columns])

    # choose a year column
    year_col = None
    for candidate in ['year', 'yr', 'year of death']:
        if candidate in lower_cols.tolist():
            year_col = df.columns[lower_cols.tolist().index(candidate)]
            break

    if year_col is None:
        # if first column looks like a year, use it
        first_col = df.columns[0]
        years = pd.to_numeric(df[first_col], errors='coerce')
        plausible = years.between(1800, 2100)
        if plausible.sum() > 5:  # at least a few plausible year values
            year_col = first_col

    if year_col is None:
        return pd.DataFrame()

    df['year'] = pd.to_numeric(df[year_col], errors='coerce')

    # filter by plausible year range
    df = df[df['year'].between(1800, 2100)]
    if year_range and isinstance(year_range, tuple) and len(year_range) == 2:
        df = df[df['year'].between(year_range[0], year_range[1])]

    # drop header/footer noise rows
    df = df.dropna(subset=['year'])

    return df


def load_icd_file(xlsx_path, year_range=None):
    """Load ICD files reliably, merging all relevant sheets (2+ for ICD2–ICD6, 3+ for ICD7+)."""
    logger.info(f"Loading {xlsx_path.name}")

    xls = pd.ExcelFile(xlsx_path)
    dfs = []

    # Exclude known non-data sheets
    excluded = {'metadata', 'description', 'correction notice', 'contents', 'readme'}
    data_sheets = [s for s in xls.sheet_names if str(s).lower().strip() not in excluded]
    
    logger.debug(f"  Found {len(data_sheets)} data sheets: {data_sheets}")

    for sheet_name in data_sheets:
        try:
            # First attempt: standard parse with inferred header
            df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
            if df is not None and len(df) > 0:
                # detect year columns in a case-insensitive way
                year_cols = [c for c in df.columns if isinstance(c, str) and ('yr' in c.lower() or 'year' in c.lower())]
                if year_cols:
                    parsed = _clean_and_filter_years(df, year_range)
                    if not parsed.empty:
                        logger.debug(f"  ✓ Parsed sheet '{sheet_name}' via default header; rows: {len(parsed)}")
                        dfs.append(parsed)
                        continue

            # Second attempt: read without headers and detect header row
            df_no_header = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=None)
            header_row = _detect_header_row(df_no_header)
            if header_row is not None:
                df2 = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=header_row)
                parsed2 = _clean_and_filter_years(df2, year_range)
                if not parsed2.empty:
                    logger.debug(
                        "  ✓ Parsed sheet '%s' via header row %s; rows: %d",
                        sheet_name,
                        header_row,
                        len(parsed2),
                    )
                    dfs.append(parsed2)
                    continue

            # Final attempt: heuristic on first column years from headerless read
            parsed3 = _clean_and_filter_years(df_no_header, year_range)
            if not parsed3.empty:
                logger.debug(f"  ✓ Parsed sheet '{sheet_name}' via headerless heuristic; rows: {len(parsed3)}")
                dfs.append(parsed3)
                continue

            logger.debug(f"  Skipping sheet '{sheet_name}' — unable to detect year column")

        except Exception as e:
            logger.warning(f"Error reading sheet {sheet_name}: {e}")
            continue

    if dfs:
        combined = pd.concat(dfs, ignore_index=True, sort=False)
        logger.debug(f"  Combined {len(combined)} rows from {len(dfs)} sheets")
        logger.debug(f"  Columns available: {list(combined.columns)}")
        logger.debug(f"  Sample data:\n{combined.head(3)}")
        
        # NO deduplication at this stage - preserve all granular data
        # Deduplication will happen later during aggregation if needed
        return combined
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
                if 'yr' in df.columns or 'year' in df.columns:
                    year_col = 'yr' if 'yr' in df.columns else 'year'
                    df['year'] = pd.to_numeric(df[year_col], errors='coerce')
                    actual_min = df['year'].min()
                    actual_max = df['year'].max()
                    logger.info(f"  ✓ Loaded {len(df):,} rows, year range: {actual_min:.0f}-{actual_max:.0f}")
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
        if 'year' in combined.columns:
            logger.info(f"Year range: {combined['year'].min():.0f}-{combined['year'].max():.0f}")
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
        'Year': 'year',
        'YEAR': 'year',
        'YR': 'year',
        'yr': 'year',
        'year': 'year',

        'Sex': 'sex',
        'SEX': 'sex',
        'sex': 'sex',
        'GENDER': 'sex',

        'Age': 'age',
        'AGE': 'age',
        'age': 'age',
        'Age Group': 'age',
        'AgeGroup': 'age',

        'Cause': 'cause',
        'CAUSE': 'cause',
        'Cause of Death': 'cause',
        'ICD Code': 'cause',
        'ICD-10': 'cause',
        'ICD-10 Code': 'cause',
        'ICD_10': 'cause',
        'ICD Code Code': 'cause',
        'ICD_1': 'icd_code',
        'ICD_': 'icd_code',

        'Deaths': 'deaths',
        'DEATHS': 'deaths',
        'Total Deaths': 'deaths',
        'Number of Deaths': 'deaths',
        'No.': 'deaths',
        'Count': 'deaths',
        'death': 'deaths',
        'NDTHS': 'deaths',
        'ndths': 'deaths',
    }

    # Rename columns
    df.rename(columns=column_mapping, inplace=True)

    # Coalesce duplicate standard columns (e.g., 'yr' and 'year' both → 'year')
    for name in ['year', 'sex', 'age', 'deaths', 'cause']:
        try:
            same_cols = [c for c in df.columns if c == name]
            if len(same_cols) > 1:
                combined = df[same_cols].bfill(axis=1).ffill(axis=1).iloc[:, 0]
                # Drop duplicate occurrences for this name, keep first
                dup_mask = (pd.Index(df.columns) == name) & pd.Index(df.columns).duplicated(keep='first')
                df = df.loc[:, ~dup_mask]
                df[name] = combined
        except Exception:
            pass

    # Ensure year column exists
    if 'year' not in df.columns:
        logger.warning("Year column not found!")

    # Remove completely empty columns
    df.dropna(axis=1, how='all', inplace=True)

    # Finally, drop any remaining duplicate columns defensively
    df = df.loc[:, ~df.columns.duplicated(keep='first')]

    logger.info(f"Standardized columns: {list(df.columns)}")
    return df


def load_icd10_codes_mapping():
    """Load ICD-10 code descriptions from Excel file"""
    logger.info("Loading ICD-10 code descriptions...")
    
    icd10_path = ONS_DOWNLOADS / "ICD10_codes.xlsx"
    
    if not icd10_path.exists():
        logger.warning(f"ICD-10 codes file not found: {icd10_path}")
        return {}
    
    try:
        # Try to load from the first sheet
        df = pd.read_excel(icd10_path, sheet_name=0)
        
        # Look for ICD-10 code and description columns
        icd_col = None
        desc_col = None
        
        for col in df.columns:
            col_lower = str(col).lower()
            if 'icd' in col_lower and '10' in col_lower:
                icd_col = col
            elif 'description' in col_lower:
                desc_col = col
        
        if icd_col is None or desc_col is None:
            logger.warning(f"Could not find ICD-10 and Description columns in {icd10_path.name}")
            # Try with actual column names
            if 'ICD-10' in df.columns and 'Description2' in df.columns:
                icd_col = 'ICD-10'
                desc_col = 'Description2'
            else:
                return {}
        
        # Create mapping dictionary
        mapping = dict(zip(
            df[icd_col].astype(str).str.strip(),
            df[desc_col].astype(str).str.strip()
        ))
        
        logger.info(f"  ✓ Loaded {len(mapping)} ICD-10 code descriptions")
        return mapping
    except Exception as e:
        logger.error(f"Failed to load ICD-10 codes: {e}")
        return {}


def load_existing_2001_2025_data():
    """Load existing compiled data for 2001-2025"""
    logger.info("\n" + "=" * 70)
    logger.info("PROCESSING EXISTING DATA (2001-2025)")
    logger.info("=" * 70)

    dfs = []
    
    # Load ICD-10 code descriptions for use with new data
    icd10_mapping = load_icd10_codes_mapping()

    # Try to load compiled_mortality files from ons_downloads/extracted
    compiled_files = [
        ONS_DOWNLOADS / "compiled_mortality_2001_2019.csv",
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
                if 'yr' not in df.columns and 'year' not in df.columns:
                    logger.warning(f"  No year column found in {filepath.name}")
                    continue

                if 'yr' in df.columns:
                    df['year'] = pd.to_numeric(df['yr'], errors='coerce')
                else:
                    df['year'] = pd.to_numeric(df['year'], errors='coerce')

                # Add ICD-10 code descriptions if available
                if icd10_mapping and ('icd-10' in df.columns or 'icd_10' in df.columns):
                    icd_col = 'icd-10' if 'icd-10' in df.columns else 'icd_10'
                    df['icd10_description'] = df[icd_col].astype(str).str.strip().map(icd10_mapping)
                    logger.debug(f"  Added ICD-10 descriptions to {(df['icd10_description'].notna()).sum()} records")

                logger.info(f"  ✓ Loaded {len(df):,} rows, year range: {df['year'].min():.0f}-{df['year'].max():.0f}")
                dfs.append(df)
            except Exception as e:
                logger.error(f"Failed to load {filepath.name}: {e}")

    if dfs:
        combined = pd.concat(dfs, ignore_index=True, sort=False)
        # Remove duplicates by year, sex, age, cause if they exist
        dup_cols = ['year'] + [c for c in ['sex', 'age', 'icd-10', 'icd_1'] if c in combined.columns]
        dup_cols = [c for c in dup_cols if c in combined.columns]
        if len(dup_cols) > 1:
            combined = combined.drop_duplicates(subset=dup_cols, keep='first')
        min_year = combined['year'].min()
        max_year = combined['year'].max()
        logger.info(
            "Combined existing data: %s rows, year range: %s-%s",
            f"{len(combined):,}",
            f"{min_year:.0f}",
            f"{max_year:.0f}",
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
    if 'yr' in df.columns:
        df['year'] = pd.to_numeric(df['yr'], errors='coerce')
    elif 'year' in df.columns:
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
    else:
        logger.warning("Missing year column")
        return pd.DataFrame()

    # Handle deaths column - might be 'ndths', 'deaths', etc.
    deaths_cols = [c for c in df.columns if 'ndth' in c or 'death' in c or 'count' in c]
    if deaths_cols:
        deaths_col = deaths_cols[0]
        df['deaths'] = pd.to_numeric(df[deaths_col], errors='coerce')
    else:
        logger.warning("Missing deaths column")
        return pd.DataFrame()

def standardize_mortality_data(df):
    """
    Standardize mortality data into a consistent format
    Output: year, cause, sex, age, deaths, [icd10_description]
    """
    if df.empty:
        return df

    logger.info("\nStandardizing mortality data format...")

    # Create a working copy
    df = df.copy()

    # Normalize column names to lowercase
    df.columns = df.columns.str.lower().str.strip()

    # Handle year column - might be 'yr' or 'year'
    if 'yr' in df.columns:
        df['year'] = pd.to_numeric(df['yr'], errors='coerce')
    elif 'year' in df.columns:
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
    else:
        logger.warning("Missing year column")
        return pd.DataFrame()

    # Handle deaths column - might be 'ndths', 'deaths', etc.
    deaths_cols = [c for c in df.columns if 'ndth' in c or 'death' in c or 'count' in c]
    if deaths_cols:
        deaths_col = deaths_cols[0]
        df['deaths'] = pd.to_numeric(df[deaths_col], errors='coerce')
    else:
        logger.warning("Missing deaths column")
        return pd.DataFrame()

    # Handle sex column
    if 'sex' in df.columns:
        df['sex'] = df['sex'].fillna('All').astype(str).str.strip().str.lower()
        df['sex'] = df['sex'].replace({
            'male': 'Male',
            'male.': 'Male',
            'males': 'Male',
            'm': 'Male',
            '1': 'Male',
            'female': 'Female',
            'female.': 'Female',
            'females': 'Female',
            'f': 'Female',
            '2': 'Female',
            '': 'All',
            'all': 'All',
            'both': 'All',
            'persons': 'All',
        })
    else:
        df['sex'] = 'All'

    # Handle age column - just keep as string
    if 'age' in df.columns:
        df['age'] = df['age'].fillna('All ages').astype(str).str.strip()
    else:
        df['age'] = 'All ages'

    # Handle cause column - look for any ICD code columns and take the first non-null per row
    # Exclude description columns from this search
    cause_candidates = [c for c in df.columns if 'icd' in c and 'description' not in c]
    if cause_candidates:
        # Build a combined series from the first non-null across ICD columns
        combined = df[cause_candidates[0]]
        for c in cause_candidates[1:]:
            combined = combined.combine_first(df[c])
        if 'cause' in df.columns:
            combined = combined.combine_first(df['cause'])
        df['cause'] = combined.astype(str).str.strip()
    elif 'cause' in df.columns:
        df['cause'] = df['cause'].fillna('Unknown').astype(str).str.strip()
    else:
        df['cause'] = 'All causes'

    # Select standard columns (keep icd10_description if present)
    standard_cols = ['year', 'cause', 'sex', 'age', 'deaths']
    if 'icd10_description' in df.columns:
        standard_cols.append('icd10_description')
    
    extra_cols = [
        c for c in df.columns
        if c not in standard_cols
        and (not deaths_cols or c not in (cause_candidates + ['yr', deaths_cols[0]]))
    ]
    keep_cols = [c for c in (standard_cols + extra_cols) if c in df.columns]
    keep_cols = [c for c in keep_cols if c in df.columns]
    df = df[keep_cols]

    # Filter valid records
    df = df.dropna(subset=['year', 'deaths'])
    df = df[(df['deaths'] > 0) | (df['deaths'].isna())]  # Keep some nulls but filter obvious zeros
    df['deaths'] = pd.to_numeric(df['deaths'], errors='coerce')
    df = df[df['deaths'] > 0]

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
    df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
    df['deaths'] = pd.to_numeric(df['deaths'], errors='coerce').astype('Int64')

    # Group by available dimensions
    group_cols = [c for c in ['year', 'cause', 'sex', 'age'] if c in df.columns]
    
    # Include icd10_description if present (preserve ICD-10 descriptions through aggregation)
    if 'icd10_description' in df.columns:
        group_cols.append('icd10_description')

    if len(group_cols) > 0:
        summary = df.groupby(group_cols, as_index=False, dropna=False)['deaths'].sum()
        summary = summary.sort_values(['year'] + [c for c in group_cols if c != 'year'])
        logger.info(f"Aggregated to {len(summary)} summary records")
        return summary

    return df


def create_yearly_totals(df):
    """Create simple yearly total deaths table"""
    if df.empty:
        return pd.DataFrame()

    logger.info("\nCreating yearly totals...")

    df = df.copy()
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['deaths'] = pd.to_numeric(df['deaths'], errors='coerce')

    yearly = df.groupby('year', as_index=False)['deaths'].sum()
    yearly = yearly.sort_values('year')

    # Format for readability
    yearly['total_deaths'] = yearly['deaths'].astype('Int64')
    yearly = yearly[['year', 'total_deaths']]

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
    if 'year' in all_data.columns:
        logger.info(f"Year range: {all_data['year'].min():.0f} - {all_data['year'].max():.0f}")

    # Aggregate to summary format
    all_data = aggregate_to_summary(all_data)

    # Create yearly totals
    yearly = create_yearly_totals(all_data)

    # Save outputs
    logger.info("\n" + "=" * 70)
    logger.info("SAVING OUTPUTS")
    logger.info("=" * 70)
    
    def _write_df_to_zip(df: pd.DataFrame, zip_path: Path, inner_csv_name: str):
        """Write a DataFrame to a zip file containing a single CSV."""
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(inner_csv_name, csv_bytes)

    output_comprehensive_zip = DATA_DIR / "uk_mortality_comprehensive_1901_2025.zip"
    output_by_cause_zip = DATA_DIR / "uk_mortality_by_cause_1901_2025.zip"
    output_yearly = DATA_DIR / "uk_mortality_yearly_totals_1901_2025.csv"

    # Save comprehensive dataset
    yearly.to_csv(output_yearly, index=False)
    logger.info(f"✓ Saved yearly totals: {output_yearly.name} ({len(yearly)} records)")

    # Add descriptions to data before saving
    all_data_with_desc = add_cause_descriptions(all_data)

    # Save comprehensive by all dimensions (zipped CSV)
    _write_df_to_zip(
        all_data_with_desc,
        output_comprehensive_zip,
        "uk_mortality_comprehensive_1901_2025.csv",
    )
    logger.info(f"✓ Saved comprehensive data: {output_comprehensive_zip.name} ({len(all_data_with_desc)} records)")

    # Save by cause (filter to only where cause is defined)
    if 'cause' in all_data_with_desc.columns:
        by_cause = all_data_with_desc[all_data_with_desc['cause'] != 'All causes'].copy()
        if not by_cause.empty:
            _write_df_to_zip(
                by_cause,
                output_by_cause_zip,
                "uk_mortality_by_cause_1901_2025.csv",
            )
            logger.info(f"✓ Saved by cause: {output_by_cause_zip.name} ({len(by_cause)} records)")

    # Print sUmmary statistics
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 70)

    if 'year' in yearly.columns:
        logger.info("\nYearly Data (1901-2025):")
        logger.info(f"  Total years: {len(yearly)}")
        logger.info(f"  Year range: {yearly['year'].min():.0f} - {yearly['year'].max():.0f}")
        logger.info(f"  Total deaths across all years: {yearly['total_deaths'].sum():,.0f}")
        logger.info(f"  Average annual deaths: {yearly['total_deaths'].mean():,.0f}")

        # Show sample years
        logger.info("\n  Sample years:")
        sample_years = [int(yearly['year'].min()), 1950, 2000, 2020, int(yearly['year'].max())]
        sample_years = [y for y in sample_years if y in yearly['year'].values]
        for year in sample_years:
            deaths = yearly[yearly['year'] == year]['total_deaths'].values
            if len(deaths) > 0:
                logger.info(f"    {int(year):4d}: {int(deaths[0]):>10,} deaths")

    logger.info("\n" + "=" * 70)
    logger.info("COMPLETE!")
    logger.info("=" * 70)

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
