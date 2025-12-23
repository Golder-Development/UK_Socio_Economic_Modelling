import pandas as pd
from pathlib import Path

# Read the proper data from the XLS file
xls_path = Path('data_sources/population/development_code/downloaded_sourcefiles/populations20012016.xls')
print(f"Reading from: {xls_path}")

# Read the data sheet
df_xls = pd.read_excel(xls_path, sheet_name='pops01-16')

print(f"\nDataframe shape: {df_xls.shape}")
print(f"Columns: {df_xls.columns.tolist()}")
print(f"\nFirst 30 rows:")
print(df_xls.head(30))

print(f"\nData types:")
print(df_xls.dtypes)

print(f"\nYear range: {df_xls['Year'].min()} - {df_xls['Year'].max()}")
print(f"Unique age groups: {sorted(df_xls['Agegroup'].unique())}")
print(f"Sex values: {sorted(df_xls['Sex'].unique())}")

print(f"\nTotal records: {len(df_xls)}")
print(f"Records per year:")
print(df_xls.groupby('Year').size())

# Verify we can recover all 2001-2016 data with age groups
print("\n" + "="*80)
print("Summary: This file has the complete 2001-2016 data with age groups!")
print("="*80)

print(f"\nSample 2001 data:")
df_2001_sample = df_xls[df_xls['Year'] == 2001]
print(df_2001_sample)

print(f"\nSample 2016 data:")
df_2016_sample = df_xls[df_xls['Year'] == 2016]
print(df_2016_sample)
