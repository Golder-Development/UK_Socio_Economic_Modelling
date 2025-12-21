"""
Download ONS bulk historical mortality datasets.
These files typically cover 50+ years and include cause of death data.
"""

import requests
import pandas as pd
import logging
from pathlib import Path
from io import BytesIO
import zipfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent
DOWNLOADS_DIR = OUTPUT_DIR / "ons_downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)


# Known ONS bulk mortality datasets with historical coverage
# Updated URLs as of Dec 2025
ONS_DATASETS = {
    "deaths_registered_2023": {
        "name": "Deaths registered in England and Wales 2023",
        "url": "https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/birthsdeathsandmarriages/deaths/datasets/deathsregisteredinenglandandwalesseriesdrreferencetables/2023/publishedtables2023.xlsx",
        "description": "Annual death registrations 2023",
    },
    "death_registrations_summary": {
        "name": "Death registrations summary tables",
        "url": "https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/birthsdeathsandmarriages/deaths/datasets/deathregistrationssummarytablesenglandandwalesreferencetables/2023/publishedweek522023.xlsx",
        "description": "Summary of deaths by cause, age, and sex",
    },
    # Alternative: Try to access the 21st century mortality directly from ONS
    "mortality_21st_century": {
        "name": "21st Century Mortality",
        "url": "https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/birthsdeathsandmarriages/deaths/datasets/the21stcenturymortalityfilesdeathsdataset/current/21stcenturymortality2023.xls",
        "description": "21st century mortality files with cause of death",
    },
}


def download_file(url, filename):
    """Download a file from URL.

    Parameters
    ----------
    url : str
        URL to download from
    filename : Path
        Local path to save to

    Returns
    -------
    Path or None
        Path to downloaded file, or None if failed
    """
    try:
        logger.info(f"Downloading: {url}")
        response = requests.get(url, timeout=60)

        if response.status_code == 200:
            filename.write_bytes(response.content)
            logger.info(f"✓ Saved to: {filename}")
            return filename
        else:
            logger.error(f"✗ HTTP {response.status_code}: {url}")
            return None
    except Exception as e:
        logger.error(f"✗ Error downloading {url}: {e}")
        return None


def extract_zip(zip_path, extract_to):
    """Extract a ZIP file.

    Parameters
    ----------
    zip_path : Path
        Path to ZIP file
    extract_to : Path
        Directory to extract to

    Returns
    -------
    list of Path
        List of extracted file paths
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)
            extracted = [extract_to / name for name in zip_ref.namelist()]
            logger.info(f"✓ Extracted {len(extracted)} files")
            return extracted
    except Exception as e:
        logger.error(f"✗ Error extracting {zip_path}: {e}")
        return []


def parse_excel_file(excel_path):
    """Parse an Excel file and display its structure.

    Parameters
    ----------
    excel_path : Path
        Path to Excel file

    Returns
    -------
    dict
        Dictionary mapping sheet names to DataFrames
    """
    try:
        logger.info(f"\nParsing: {excel_path.name}")
        excel_file = pd.ExcelFile(excel_path)

        logger.info(f"  Sheets: {len(excel_file.sheet_names)}")

        sheets_data = {}
        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                sheets_data[sheet_name] = df
                logger.info(
                    f"    • {sheet_name}: {df.shape[0]} rows × {df.shape[1]} cols"
                )

                # Show first few column names to understand structure
                if len(df.columns) > 0:
                    cols_preview = list(df.columns[:5])
                    logger.info(f"      Columns: {cols_preview}")
            except Exception as e:
                logger.warning(f"    ✗ Could not read sheet '{sheet_name}': {e}")

        return sheets_data
    except Exception as e:
        logger.error(f"✗ Error parsing {excel_path}: {e}")
        return {}


def extract_yearly_totals(sheets_data):
    """Try to extract yearly death totals from parsed sheets.

    Parameters
    ----------
    sheets_data : dict
        Dictionary of sheet_name -> DataFrame

    Returns
    -------
    pd.DataFrame or None
        DataFrame with year and total_deaths columns
    """
    for sheet_name, df in sheets_data.items():
        # Look for sheets that might contain yearly totals
        if any(
            keyword in sheet_name.lower()
            for keyword in ["total", "summary", "annual", "year"]
        ):
            logger.info(f"\nAnalyzing sheet: {sheet_name}")
            logger.info(f"First few rows:")
            print(df.head(10).to_string())

            # Try to identify year and deaths columns
            year_col = None
            deaths_col = None

            for col in df.columns:
                col_lower = str(col).lower()
                if "year" in col_lower:
                    year_col = col
                if any(word in col_lower for word in ["death", "total", "number"]):
                    deaths_col = col

            if year_col and deaths_col:
                logger.info(f"Found year column: {year_col}")
                logger.info(f"Found deaths column: {deaths_col}")

                result = df[[year_col, deaths_col]].copy()
                result.columns = ["year", "total_deaths"]

                # Clean and convert
                result["year"] = pd.to_numeric(result["year"], errors="coerce")
                result["total_deaths"] = pd.to_numeric(
                    result["total_deaths"], errors="coerce"
                )
                result = result.dropna()

                return result

    return None


def main():
    """Main entry point."""
    logger.info("=" * 70)
    logger.info("ONS Historical Mortality Data Downloader")
    logger.info("=" * 70)

    all_yearly_data = []

    for dataset_id, dataset_info in ONS_DATASETS.items():
        logger.info(f"\n{'=' * 70}")
        logger.info(f"Dataset: {dataset_info['name']}")
        logger.info(f"Description: {dataset_info['description']}")
        logger.info(f"{'=' * 70}")

        # Determine file extension from URL
        url = dataset_info["url"]
        if url.endswith(".xlsx"):
            extension = ".xlsx"
        elif url.endswith(".xls"):
            extension = ".xls"
        elif url.endswith(".zip"):
            extension = ".zip"
        elif url.endswith(".csv"):
            extension = ".csv"
        else:
            extension = ".xlsx"  # default guess

        output_file = DOWNLOADS_DIR / f"{dataset_id}{extension}"

        # Download
        downloaded = download_file(url, output_file)

        if downloaded:
            # Parse if Excel
            if extension in [".xlsx", ".xls"]:
                sheets = parse_excel_file(downloaded)

                # Try to extract yearly totals
                yearly_data = extract_yearly_totals(sheets)
                if yearly_data is not None:
                    logger.info(f"\n✓ Extracted {len(yearly_data)} years of data")
                    logger.info(
                        f"  Year range: {yearly_data['year'].min():.0f} - {yearly_data['year'].max():.0f}"
                    )
                    all_yearly_data.append(yearly_data)
            elif extension == ".zip":
                # Extract and process
                extracted = extract_zip(downloaded, DOWNLOADS_DIR / dataset_id)
                logger.info(f"Extracted files: {[f.name for f in extracted]}")

    # Combine all yearly data
    if all_yearly_data:
        logger.info(f"\n{'=' * 70}")
        logger.info("Combining all datasets...")
        logger.info(f"{'=' * 70}")

        combined = pd.concat(all_yearly_data, ignore_index=True)
        combined = combined.sort_values("year")
        combined = combined.groupby("year", as_index=False)[
            "total_deaths"
        ].max()  # Take max to avoid duplicates

        output_file = OUTPUT_DIR / "uk_mortality_historical_totals.csv"
        combined.to_csv(output_file, index=False)

        logger.info(f"\n✓ Final dataset saved: {output_file}")
        logger.info(f"✓ Years covered: {len(combined)}")
        logger.info(
            f"✓ Range: {combined['year'].min():.0f} - {combined['year'].max():.0f}"
        )
        logger.info(f"\nData preview:")
        print(combined.to_string(index=False))
    else:
        logger.warning("\nNo yearly data extracted. Files may need manual inspection.")
        logger.info(f"\nDownloaded files are in: {DOWNLOADS_DIR}")
        logger.info(
            "Please review them manually to identify the correct sheets/columns."
        )


if __name__ == "__main__":
    main()
