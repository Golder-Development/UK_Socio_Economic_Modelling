"""
Extract and consolidate all ICD code descriptions from ONS Excel files.
Creates a comprehensive mapping of codes to descriptions across all ICD versions.
"""

import xlrd
import pandas as pd
from pathlib import Path
import logging
import sys

# Import ICD-10 reference helper
try:
    from icd10_reference import get_icd10_description
except ImportError:
    # Fallback if import fails
    def get_icd10_description(code):
        return f'ICD-10 {code}'

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent
# Correct location for ONS extracted Excel files is the parent mortality_stats folder
ONS_DOWNLOADS = DATA_DIR.parent / "ons_downloads" / "extracted"
DOWNLOADED_SOURCES = DATA_DIR / "downloaded_sourcefiles"


def extract_descriptions_from_xls(filepath):
    """Extract code descriptions from .xls file"""
    try:
        wb = xlrd.open_workbook(filepath)
        sheet_names = wb.sheet_names()

        # Look for description sheet
        desc_sheet = None
        for name in sheet_names:
            if "descr" in name.lower():
                desc_sheet = name
                break

        if not desc_sheet:
            logger.warning(f"No description sheet found in {filepath.name}")
            return pd.DataFrame()

        ws = wb.sheet_by_name(desc_sheet)

        if ws.nrows == 0:
            return pd.DataFrame()

        # Get headers
        headers = [ws.cell_value(0, col) for col in range(ws.ncols)]

        # Extract data
        data = []
        for row_idx in range(1, ws.nrows):
            row_data = {}
            for col_idx, header in enumerate(headers):
                if header:  # Skip empty header columns
                    row_data[header] = ws.cell_value(row_idx, col_idx)
            if row_data:
                data.append(row_data)

        df = pd.DataFrame(data)
        logger.info(f"Extracted {len(df)} descriptions from {filepath.name}")
        return df

    except Exception as e:
        logger.error(f"Error processing {filepath.name}: {e}")
        return pd.DataFrame()


def extract_descriptions_from_xlsx(filepath):
    """Extract code descriptions from .xlsx file"""
    try:
        xls = pd.ExcelFile(filepath)
        sheet_names = xls.sheet_names

        # Look for description sheet
        desc_sheet = None
        for name in sheet_names:
            if "descr" in name.lower():
                desc_sheet = name
                break

        if not desc_sheet:
            logger.warning(f"No description sheet found in {filepath.name}")
            return pd.DataFrame()

        df = pd.read_excel(filepath, sheet_name=desc_sheet)
        logger.info(f"Extracted {len(df)} descriptions from {filepath.name}")
        return df

    except Exception as e:
        logger.error(f"Error processing {filepath.name}: {e}")
        return pd.DataFrame()


def standardize_description_columns(df, source_file):
    """Standardize column names across different ICD versions"""
    if df.empty:
        return df

    df = df.copy()

    # Normalize column names
    df.columns = df.columns.str.strip()

    # Handle different code column names
    if "CODE" in df.columns:
        df["code"] = df["CODE"]
    elif "icdcode" in df.columns:
        df["code"] = df["icdcode"]
    else:
        logger.warning(f"No code column found in {source_file}")
        return pd.DataFrame()

    # Handle description columns
    if "DESCRIPTION" in df.columns:
        df["description"] = df["DESCRIPTION"]
    elif "description" in df.columns:
        # Already has description column
        pass
    elif "description1" in df.columns and "description2" in df.columns:
        # Combine description1 and description2
        df["description"] = (
            df["description1"].fillna("") + " - " + df["description2"].fillna("")
        )
        df["description"] = df["description"].str.strip(" -")
    elif "description1" in df.columns:
        df["description"] = df["description1"]
    else:
        logger.warning(f"No description column found in {source_file}")
        return pd.DataFrame()

    # Convert code to string for consistency
    df["code"] = df["code"].astype(str).str.strip()
    df["description"] = df["description"].astype(str).str.strip()

    # Add source file info
    df["source_file"] = source_file

    # Keep only necessary columns
    df = df[["code", "description", "source_file"]]

    # Remove empty rows
    df = df[df["code"].notna() & (df["code"] != "") & (df["code"] != "nan")]
    df = df[
        df["description"].notna()
        & (df["description"] != "")
        & (df["description"] != "nan")
    ]

    return df


def extract_icd10_codes_from_data():
    """Extract unique ICD-10 codes from 21st century mortality data and create basic descriptions."""
    logger.info("\nExtracting ICD-10 codes from 21st century data...")
    
    # Try to load the compiled CSV with ICD-10 codes
    icd10_files = [
        DOWNLOADED_SOURCES / "compiled_mortality_21c_2017.csv",
        DATA_DIR / "compiled_mortality_2001_2019.csv",
    ]
    
    all_codes = set()
    for filepath in icd10_files:
        if filepath.exists():
            try:
                df = pd.read_csv(filepath, low_memory=False)
                if 'ICD-10' in df.columns:
                    codes = df['ICD-10'].dropna().astype(str).str.strip()
                    all_codes.update(codes.unique())
                    logger.info(f"  Found {len(codes.unique())} unique ICD-10 codes in {filepath.name}")
                elif 'icd-10' in df.columns:
                    codes = df['icd-10'].dropna().astype(str).str.strip()
                    all_codes.update(codes.unique())
                    logger.info(f"  Found {len(codes.unique())} unique ICD-10 codes in {filepath.name}")
            except Exception as e:
                logger.warning(f"  Could not read {filepath.name}: {e}")
    
    if not all_codes:
        logger.warning("No ICD-10 codes found in data files")
        return pd.DataFrame()
    
    # Create basic descriptions (code as description for now)
    # In production, these would be looked up from an ICD-10 reference
    icd10_data = []
    for code in sorted(all_codes):
        if code and code != 'nan':
            # Use reference lookup for descriptions
            description = get_icd10_description(code)
            icd10_data.append({
                'code': code,
                'description': description,
                'source_file': 'extracted_from_21c_data',
                'icd_version': 'ICD-10 (2001-)'
            })
    
    df = pd.DataFrame(icd10_data)
    logger.info(f"  Created {len(df)} ICD-10 code entries")
    return df


def build_code_description_mapping():
    """Build comprehensive code-to-description mapping from all ICD files"""
    logger.info("=" * 80)
    logger.info("BUILDING ICD CODE DESCRIPTION MAPPING")
    logger.info("=" * 80)

    icd_files = [
        ("icd1.xls", "ICD-1 (1901-1910)"),
        ("icd2.xls", "ICD-2 (1911-1920)"),
        ("icd3.xls", "ICD-3 (1921-1930)"),
        ("icd4.xls", "ICD-4 (1931-1939)"),
        ("icd5.xls", "ICD-5 (1940-1949)"),
        ("icd6.xls", "ICD-6 (1950-1957)"),
        ("icd7.xlsx", "ICD-7 (1958-1967)"),
        ("icd8.xls", "ICD-8 (1968-1978)"),
        ("icd9_a.xlsx", "ICD-9a (1979-1984)"),
        ("icd9_b.xls", "ICD-9b (1985-1993)"),
        ("icd9_c.xls", "ICD-9c (1994-2000)"),
    ]

    all_descriptions = []

    for filename, period in icd_files:
        filepath = ONS_DOWNLOADS / filename

        if not filepath.exists():
            logger.warning(f"File not found: {filename}")
            continue

        logger.info(f"\nProcessing {filename} - {period}")

        if filename.endswith(".xlsx"):
            df = extract_descriptions_from_xlsx(filepath)
        else:
            df = extract_descriptions_from_xls(filepath)

        if not df.empty:
            df = standardize_description_columns(df, filename)
            if not df.empty:
                # Add period info
                df["icd_version"] = period
                all_descriptions.append(df)

    # Extract ICD-10 codes from modern data
    icd10_df = extract_icd10_codes_from_data()
    if not icd10_df.empty:
        all_descriptions.append(icd10_df)

    if not all_descriptions:
        logger.error("No descriptions extracted!")
        return pd.DataFrame()

    # Combine all descriptions
    combined = pd.concat(all_descriptions, ignore_index=True)

    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total descriptions: {len(combined):,}")
    logger.info(f"Unique codes: {combined['code'].nunique():,}")
    logger.info(f"\nBy ICD version:")
    for version in combined["icd_version"].unique():
        count = len(combined[combined["icd_version"] == version])
        logger.info(f"  {version}: {count:,} codes")

    return combined


def main():
    # If an existing mapping is present, skip rebuild (idempotent prerequisite)
    # Write outputs to parent mortality_stats folder so downstream scripts find them
    output_file = DATA_DIR.parent / "icd_code_descriptions.csv"
    simplified_output = DATA_DIR.parent / "icd_code_descriptions_simplified.csv"
    if output_file.exists() and simplified_output.exists():
        try:
            existing = pd.read_csv(output_file)
            if not existing.empty:
                logger.info(
                    f"Existing code descriptions found ({len(existing):,} rows). Skipping rebuild."
                )
                sys.exit(0)
        except Exception:
            # If unreadable, continue to rebuild
            pass

    # Build the mapping
    descriptions_df = build_code_description_mapping()

    if descriptions_df.empty:
        logger.error("Failed to build description mapping (no input files found)")
        # Fail hard so orchestrator reports the step as failed
        sys.exit(1)

    # Save to CSV
    descriptions_df.to_csv(output_file, index=False)
    logger.info(f"\n✓ Saved code descriptions to: {output_file}")

    # Create a simplified mapping (just code -> description, using most recent)
    # For codes that appear in multiple ICD versions, keep the most recent
    simplified = descriptions_df.sort_values(
        "source_file", ascending=False
    ).drop_duplicates(subset=["code"], keep="first")
    simplified[["code", "description"]].to_csv(simplified_output, index=False)
    logger.info(f"✓ Saved simplified mapping to: {simplified_output}")
    logger.info(f"  ({len(simplified):,} unique codes)")


if __name__ == "__main__":
    main()
