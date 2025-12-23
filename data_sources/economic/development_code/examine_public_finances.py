import pandas as pd
from pathlib import Path

csv_path = Path('data_sources/economic/development_code/downloaded_sourcefiles/PublicFinances1800-2023.csv')

# Read first 10 rows to see structure
df_head = pd.read_csv(csv_path, nrows=10, header=None)
print("First 10 rows:")
print(df_head)

print("\n" + "="*80 + "\n")

# Try reading with different header row
df = pd.read_csv(csv_path, skiprows=4)
print(f"Shape: {df.shape}")
print(f"Columns ({len(df.columns)} total):")
for i, col in enumerate(df.columns):
    print(f"  {i}: {col}")
print(f"\nFirst 5 data rows:")
print(df.head())
print(f"\nLast 5 data rows:")
print(df.tail())

# Check the year column
year_col = df.columns[-2]
print(f"\nYear column: '{year_col}'")
print(f"Year values (first 10): {df[year_col].head(10).tolist()}")
print(f"Year values (last 10): {df[year_col].tail(10).tolist()}")
