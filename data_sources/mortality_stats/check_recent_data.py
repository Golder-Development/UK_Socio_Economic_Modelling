"""Check the structure of 2001-2025 data files"""
import pandas as pd

# Check compiled mortality files
print('=== compiled_mortality_2001_2019.csv ===')
df = pd.read_csv('downloaded_sourcefiles/compiled_mortality_2001_2019.csv', nrows=5)
print(f'Columns: {list(df.columns)}')
print(df.head().to_string())
full_df = pd.read_csv('downloaded_sourcefiles/compiled_mortality_2001_2019.csv')
print(f'Shape: {full_df.shape}')
print(f'Year range: {full_df["YR"].min()}-{full_df["YR"].max()}')

print('\n\n=== uk_mortality_weekly_raw.csv ===')
df2 = pd.read_csv('extract_20251220_172134/uk_mortality_weekly_raw.csv', nrows=5)
print(f'Columns: {list(df2.columns)}')
print(df2.head().to_string())
