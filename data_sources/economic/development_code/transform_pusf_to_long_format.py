"""
Transform PUSF CSV from wide to long (tidy) format.

File structure:
- Row 0: Title (measure names)
- Row 1: CDID (measure codes)
- Row 2: PreUnit (currency indicators)
- Row 3: Unit (measurement units)
- Row 4: Release Date
- Row 5: Next release
- Row 6: Important Notes
- Rows 7+: Actual data where column 0 = year, columns 1+ = values

Output format:
- date_period (year)
- measure (the measure description)
- measure_code (original column header)
- cdid (the CDID code)
- value (the data value, including nulls)
- unit (measurement unit)
- pre_unit (currency indicator)
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Define file paths
input_file = Path(__file__).parent / "downloaded_sourcefiles" / "pusf.csv"
output_file = Path(__file__).parent / "pusf_long_format.csv"

print(f"Reading from: {input_file}")

# Read the CSV file with no header to preserve structure
df = pd.read_csv(input_file, header=None, low_memory=False)

# Display original structure info
print(f"\nOriginal shape: {df.shape}")
print(f"Row 0 (first 3 items): {list(df.iloc[0, :3])}")
print(f"Row 1 (first 3 items): {list(df.iloc[1, :3])}")

# Extract metadata from the first rows
# Row 0: "Title" label in col 0, then measure descriptions
# Row 1: "CDID" label in col 0, then measure codes
# Row 2: "PreUnit" label in col 0, then currency prefixes
# Row 3: "Unit" label in col 0, then units
# Rows 7+: Data with year in column 0
measure_names = df.iloc[0, 1:].values  # Skip the "Title" label in column 0
cdids = df.iloc[1, 1:].values  # Skip the "CDID" label
pre_units = df.iloc[2, 1:].values  # Skip the "PreUnit" label
units = df.iloc[3, 1:].values  # Skip the "Unit" label

# Get data starting from row 7 onwards
data_df = df.iloc[7:, :].copy()

# Column 0 contains the year/date period
date_column = data_df.iloc[:, 0]
date_values = pd.to_numeric(date_column, errors='coerce')

print(f"\nData shape after removing metadata: {data_df.shape}")
print(f"Sample years: {date_values[~date_values.isna()].head().tolist()}")
print(f"Date range: {date_values.min():.0f} to {date_values.max():.0f}")

# Initialize list to store long-format rows
long_format_rows = []

# Data columns start from column 1 (column 0 is dates)
num_measures = len(data_df.columns) - 1

# Iterate through each data column (skip column 0 which is dates)
for col_idx in range(1, len(data_df.columns)):
    measure_idx = col_idx - 1  # Index for metadata arrays

    measure_title = measure_names[measure_idx]
    cdid = cdids[measure_idx]
    pre_unit = pre_units[measure_idx]
    unit = units[measure_idx]

    # Skip if measure name is empty or NaN
    if pd.isna(measure_title) or str(measure_title).strip() == '' or str(measure_title).strip().lower() == 'nan':
        continue

    # Get all values for this measure across all years
    col_values = data_df.iloc[:, col_idx]

    # Create long-format rows
    for year_idx, year in enumerate(date_values):
        if pd.isna(year):
            continue

        value = col_values.iloc[year_idx]

        # Convert value to numeric, keeping NaN for missing values
        try:
            if pd.isna(value) or str(value).strip() == '' or str(value).strip().lower() == 'nan':
                numeric_value = np.nan
            else:
                numeric_value = float(value)
        except (ValueError, TypeError):
            numeric_value = np.nan

        # Append row
        long_format_rows.append({
            'date_period': int(year),
            'measure': str(measure_title),
            'cdid': str(cdid) if not pd.isna(cdid) else '',
            'value': numeric_value,
            'unit': str(unit) if not pd.isna(unit) else '',
            'pre_unit': str(pre_unit) if not pd.isna(pre_unit) else ''
        })

# Create long-format DataFrame
long_df = pd.DataFrame(long_format_rows)

# Sort by date_period, then measure
long_df = long_df.sort_values(['date_period', 'measure']).reset_index(drop=True)

# Display summary information
print(f"\nLong format shape: {long_df.shape}")
print("\nFirst 10 rows:")
print(long_df.head(10))
print("\nData types:")
print(long_df.dtypes)
print(f"\nUnique measures: {long_df['measure'].nunique()}")
print("\nSample measures:")
for i, measure in enumerate(long_df['measure'].unique()[:5]):
    print(f"  - {measure}")
print("\nNull value statistics:")
print(f"  Total rows: {len(long_df)}")
print(f"  Rows with null values: {long_df['value'].isna().sum()}")
print(f"  Percentage null: {(long_df['value'].isna().sum() / len(long_df) * 100):.2f}%")

# Save to CSV
long_df.to_csv(output_file, index=False)
print(f"\n✓ Transformed data saved to: {output_file}")
print(f"  Shape: {long_df.shape}")
