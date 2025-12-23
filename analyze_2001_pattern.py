import pandas as pd
from pathlib import Path
import numpy as np

# Load the combined data
csv_path = Path('data_sources/population/development_code/downloaded_sourcefiles/combined_population_data.csv')
df = pd.read_csv(csv_path)

# Get data around 2000-2001 to see the pattern
print("="*80)
print("Pattern Analysis: 2000 vs 2001 structure")
print("="*80)

df_2000 = df[df['YR'] == 2000].copy()
df_2001 = df[df['YR'] == 2001].copy()

print(f"\n2000 data: {len(df_2000)} records")
print(f"2000 unique ages: {sorted(df_2000['AGE'].dropna().unique())}")
print(f"2000 records per sex: {df_2000.groupby('SEX').size()}")

print(f"\n2001 data: {len(df_2001)} records")
print(f"2001 unique ages: {sorted(df_2001['AGE'].dropna().unique())}")
print(f"2001 records per sex: {df_2001.groupby('SEX').size()}")

# Check what the 19 population values look like for males 2001
print("\n2001 Male population values (sorted):")
male_2001_pops = df_2001[df_2001['SEX'] == 1]['POP'].values
male_2001_pops_sorted = sorted(male_2001_pops)
print(male_2001_pops_sorted)

# Check corresponding ages from 2000 for males
print("\n2000 Male data (check order):")
male_2000 = df_2000[df_2000['SEX'] == 1].sort_values('POP')
print(male_2000[['AGE', 'POP']])

# Try to match 2001 values with 2000 to infer ages
print("\n" + "="*80)
print("Attempting to match 2001 values with 2000 age ranges by interpolation")
print("="*80)

# Calculate 2000 male by age
male_2000_by_age = df_2000[df_2000['SEX'] == 1].set_index('AGE')['POP'].sort_index()
print("\n2000 Male population by age group:")
print(male_2000_by_age)

# Check if 2001 single-year ages correspond to components of 2000 age groups
print("\nSorted 2001 male populations with corresponding rank:")
for i, pop in enumerate(sorted(male_2001_pops)):
    rank = sorted(male_2001_pops).index(pop)
    print(f"  Rank {rank}: {pop:,}")

print("\nNote: 19 single-year ages for 2001 suggests either:")
print("  1. Individual ages 0-18 and 85+")
print("  2. Individual ages 0-19 (excluding grouped ages)")
print("  3. Some other grouping scheme")

# Check other source files
xls_path = Path('data_sources/population/development_code/downloaded_sourcefiles/populations20012016.xls')
if xls_path.exists():
    print(f"\n{'='*80}")
    print(f"Found supplementary file: {xls_path.name}")
    print("Attempting to read...")
    try:
        xls_data = pd.read_excel(xls_path, sheet_name=None)
        for sheet_name in list(xls_data.keys())[:3]:
            print(f"\nSheet: {sheet_name}")
            print(xls_data[sheet_name].head())
    except Exception as e:
        print(f"Error reading: {e}")
else:
    print(f"\nSupplementary file not found: {xls_path}")
