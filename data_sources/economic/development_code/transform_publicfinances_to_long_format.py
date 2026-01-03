"""
Transform PublicFinances1800-2023.csv from wide to long format

Structure:
- Row 0: Navigation header ("Back to contents", "Non-CG Receipts", etc.)
- Row 1: Category groupings
- Row 2: Subcategory labels with "PreUnit"
- Row 3: Measure titles
- Row 4: ONS codes (CDID)
- Row 5: Units and source metadata
- Row 6+: Data starts (fiscal years like 1800-01, 1801-02, etc.)

Output: publicfinances_long_format.csv with structure:
  date_period | measure | cdid | value | unit | source_dataset
"""

import pandas as pd
import numpy as np
from pathlib import Path


def transform_publicfinances_to_long_format():
    # Define paths
    input_file = Path(__file__).parent / 'downloaded_sourcefiles' / 'PublicFinances1800-2023.csv'
    output_file = Path(__file__).parent / 'publicfinances_long_format.csv'

    print(f"Reading: {input_file}")

    # Read with no header to preserve structure
    df = pd.read_csv(input_file, header=None, dtype=str)

    print(f"Raw data shape: {df.shape}")
    print("First few rows of header structure:")
    print(df.iloc[0:6, 0:10])  # Show first 6 rows, 10 columns

    # Extract header information
    # Row 3 contains measure titles (column names for data)
    measure_titles = df.iloc[3, 1:].tolist()  # Skip first column (row labels)

    # Row 4 contains ONS codes
    ons_codes = df.iloc[4, 1:].tolist()

    # Row 5 contains units/metadata info
    row_5 = df.iloc[5, 1:].tolist()

    # Data starts from row 6
    data_df = df.iloc[6:, :].copy()
    data_df.columns = df.iloc[0, :].tolist()  # Use row 0 as column names

    # The first column contains fiscal year periods (e.g., '1800-01', '1801-02', etc.)
    date_col_name = data_df.columns[0]
    date_periods = data_df[date_col_name].values

    # Get the actual data columns (starting from column 1)
    data_cols = data_df.iloc[:, 1:]
    data_cols.columns = measure_titles

    # Convert date periods to years (extract first 4 digits)
    # '1800-01' -> 1800, '1938-39' -> 1938
    years = [int(str(period).split('-')[0]) if pd.notna(period) else np.nan for period in date_periods]

    # Initialize list to collect rows
    long_format_rows = []

    # Iterate through each measure (column)
    for col_idx, measure_title in enumerate(measure_titles):
        # Get values for this measure
        values = data_cols.iloc[:, col_idx].values
        cdid = ons_codes[col_idx] if col_idx < len(ons_codes) else ''

        # Extract unit info from row 5
        unit_info = row_5[col_idx] if col_idx < len(row_5) else ''

        # Create rows for long format
        for year_idx, year in enumerate(years):
            value = values[year_idx]

            # Convert value to float, handling '-' as NaN
            if pd.isna(value) or value == '-' or value == '':
                numeric_value = np.nan
            else:
                try:
                    numeric_value = float(value)
                except Exception:
                    numeric_value = np.nan

            long_format_rows.append({
                'date_period': year,
                'measure': measure_title,
                'cdid': cdid,
                'value': numeric_value,
                'unit': unit_info,
                'source_dataset': 'PublicFinances1800-2023'
            })

    # Create long format dataframe
    long_df = pd.DataFrame(long_format_rows)

    # Remove rows with NaN measures (could occur from malformed headers)
    long_df = long_df[long_df['measure'].notna()]

    # Sort by date_period and measure for consistency
    long_df = long_df.sort_values(['date_period', 'measure']).reset_index(drop=True)

    # Save to CSV
    long_df.to_csv(output_file, index=False)

    print("\n✓ Successfully transformed to long format")
    print(f"Output: {output_file}")
    print(f"Shape: {long_df.shape}")
    print("\nData summary:")
    print(f"  Date range: {long_df['date_period'].min()} - {long_df['date_period'].max()}")
    print(f"  Unique measures: {long_df['measure'].nunique()}")
    print(f"  Total rows: {len(long_df)}")
    print(f"  Non-null values: {long_df['value'].notna().sum()}")
    print(f"  Null values: {long_df['value'].isna().sum()}")
    print(f"  Data completeness: {long_df['value'].notna().sum() / len(long_df) * 100:.1f}%")

    print("\nFirst 10 rows:")
    print(long_df.head(10))

    print("\nMeasure list:")
    measures = long_df['measure'].unique()
    for i, measure in enumerate(measures[:10], 1):
        print(f"  {i}. {measure}")
    print(f"  ... and {len(measures) - 10} more measures")

    return long_df


if __name__ == "__main__":
    long_df = transform_publicfinances_to_long_format()
