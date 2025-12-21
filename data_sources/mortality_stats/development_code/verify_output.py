"""Verify the comprehensive mortality datasets"""

import pandas as pd

print("=== uk_mortality_comprehensive_1901_2019.csv ===")
df = pd.read_csv("uk_mortality_comprehensive_1901_2019.csv")
print(f"Total records: {len(df):,}")
print(f"Columns: {list(df.columns)}")
print(f'Year range: {df["year"].min():.0f} - {df["year"].max():.0f}')
print(f'Unique causes: {df["cause"].nunique()}')
print(f'Sexes: {df["sex"].unique()}')
print(f'Unique ages: {df["age"].nunique()}')
print(f"\nSample data:")
print(df.head(10).to_string())

print("\n\n=== uk_mortality_yearly_totals_1901_2019.csv ===")
yearly = pd.read_csv("uk_mortality_yearly_totals_1901_2019.csv")
print(f"Total records: {len(yearly):,}")
print(f'Year range: {yearly["year"].min():.0f} - {yearly["year"].max():.0f}')
print(f"\nSample years:")
sample_years = [1901, 1950, 1979, 2000, 2017]
print(yearly[yearly["year"].isin(sample_years)].to_string())
