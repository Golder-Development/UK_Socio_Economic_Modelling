import pandas as pd
from pathlib import Path

# Load source data
csv_path = Path('data_sources/population/development_code/downloaded_sourcefiles/combined_population_data.csv')
df = pd.read_csv(csv_path)

# Focus on 2001-2016 with NaN ages
df_2001_2016 = df[(df['YR'] >= 2001) & (df['YR'] <= 2016)].copy()
print(f"Total records 2001-2016: {len(df_2001_2016)}")
print(f"Records with NaN age: {df_2001_2016['AGE'].isna().sum()}")
print(f"Records with non-NaN age: {df_2001_2016['AGE'].notna().sum()}")

print("\n" + "="*80)
print("Examining 2001 data structure:")
df_2001 = df[df['YR'] == 2001]
print(f"Total 2001 records: {len(df_2001)}")
print(f"Unique SEX values: {sorted(df_2001['SEX'].unique())}")
print(f"Unique AGE values: {sorted(df_2001['AGE'].dropna().unique())}")
print(f"NaN age count: {df_2001['AGE'].isna().sum()}")

print("\nFirst 50 rows of 2001 data:")
print(df_2001[['YR', 'SEX', 'AGE', 'POP']].head(50).to_string())

print("\n" + "="*80)
print("Last 50 rows of 2001 data:")
print(df_2001[['YR', 'SEX', 'AGE', 'POP']].tail(50).to_string())

print("\n" + "="*80)
print("Examining population totals by sex and year:")
totals_2001_2016 = df_2001_2016.groupby(['YR', 'SEX']).agg({
    'POP': ['sum', 'count']
}).reset_index()
totals_2001_2016.columns = ['YR', 'SEX', 'Total_Pop', 'Num_Records']
print(totals_2001_2016.to_string())

print("\n" + "="*80)
print("Checking if NaN and non-NaN ages are for same years:")
df_with_nan = df[(df['YR'] >= 2001) & (df['YR'] <= 2016) & (df['AGE'].isna())]
df_without_nan = df[(df['YR'] >= 2001) & (df['YR'] <= 2016) & (df['AGE'].notna())]
print(f"Years with NaN ages: {sorted(df_with_nan['YR'].unique())}")
print(f"Years without NaN ages: {sorted(df_without_nan['YR'].unique())}")
