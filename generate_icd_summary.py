"""
Generate ICD code summary from L1-classified mortality data.
Simple aggregation: one row per ICD code with summary statistics.
"""

import pandas as pd
import zipfile
from pathlib import Path

# Load L1-classified data
data_file_zip = Path('data_sources/mortality_stats/uk_mortality_by_cause_1901_onwards_L1.zip')
data_file_csv = Path('data_sources/mortality_stats/uk_mortality_by_cause_1901_onwards_L1.csv')

if data_file_zip.exists():
    with zipfile.ZipFile(data_file_zip, 'r') as zf:
        csv_name = [n for n in zf.namelist() if n.endswith('.csv')][0]
        with zf.open(csv_name) as f:
            df = pd.read_csv(f)
elif data_file_csv.exists():
    df = pd.read_csv(data_file_csv)
else:
    raise FileNotFoundError("L1 classified data not found. Run regenerate_all_data_v2.py first.")

print(f"Loading: {len(df):,} records")
print(f"Years: {df['year'].min()}-{df['year'].max()}")

# Group by ICD version and code
grouped = df.groupby(['icd_version', 'cause']).agg({
    'cause_description': 'first',
    'harmonized_category_code': 'first',
    'harmonized_category_name': 'first',
    'year': ['min', 'max', 'nunique'],
    'deaths': 'sum'
}).reset_index()

grouped.columns = ['icd_version', 'icd_code', 'cause_description', 'l1_category_code', 'l1_category_name', 
                   'first_year', 'last_year', 'years_active', 'total_deaths']

# Calculate avg deaths per year
grouped['avg_deaths_per_year'] = grouped['total_deaths'] / grouped['years_active']

# Get max population for each period and calculate per 100k
pop_file = Path('data_sources/population/uk_population_harmonized_age_groups.csv')
pop_df = pd.read_csv(pop_file)

def get_max_population(first_year, last_year):
    period_pop = pop_df[(pop_df['year'] >= first_year) & (pop_df['year'] <= last_year)]['population'].max()
    return period_pop if pd.notna(period_pop) else pop_df['population'].max()

grouped['max_population'] = grouped.apply(
    lambda r: get_max_population(r['first_year'], r['last_year']), axis=1
)

grouped['deaths_per_100k'] = (grouped['avg_deaths_per_year'] / grouped['max_population']) * 100000

# Sort by ICD version and code
grouped = grouped.sort_values(['icd_version', 'icd_code'])

# Save
output_file = Path('generated_charts/icd_code_summary.csv')
grouped.to_csv(output_file, index=False)

print(f"\n✓ Saved: {output_file.name}")
print(f"  Rows: {len(grouped):,}")
print(f"  Columns: {len(grouped.columns)}")
print(f"  ICD versions: {grouped['icd_version'].nunique()}")
print(f"\nFirst 10 rows:")
print(grouped.head(10).to_string(index=False))
