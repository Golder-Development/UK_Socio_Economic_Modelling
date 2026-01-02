#!/usr/bin/env python3
"""
Investigate unknown/unclassified patterns for ages 35+ across problem periods.
"""

import pandas as pd
import os

os.chdir(r'h:\VScode\UK_Socio_Economic_Modelling\data_sources\mortality_stats')

# Load L1 dataset
print("Loading L1 dataset...")
df = pd.read_csv('uk_mortality_by_cause_1901_onwards_L1.csv', low_memory=False)

print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")

# Check unique categories
print("\n" + "="*70)
print("UNIQUE HARMONIZED CATEGORIES:")
print("="*70)
cats = sorted(df['harmonized_category_name'].dropna().unique())
for i, cat in enumerate(cats, 1):
    print(f"{i:2}. {cat}")

# Parse age
df['age_numeric'] = pd.to_numeric(df['age'].str.replace('T', '').str.replace('+', ''), errors='coerce')

# Filter to ages 35+
df_35plus = df[df['age_numeric'] >= 35].copy()

print(f"\nTotal records age 35+: {len(df_35plus):,}")
print(f"Total deaths age 35+: {df_35plus['deaths'].sum():,.0f}")

# Define problem periods with ICD versions
problem_periods = [
    (1931, 1938, 'ICD-3'),
    (1940, 1948, 'ICD-4'),
    (1969, 1986, 'ICD-7/8'),
    (1999, 2000, 'ICD-10')
]

print("\n" + "="*70)
print("UNKNOWN CLASSIFICATION PATTERNS (Age 35+)")
print("="*70)

for start_yr, end_yr, icd_ver in problem_periods:
    period_data = df_35plus[(df_35plus['year'] >= start_yr) & (df_35plus['year'] <= end_yr)]
    
    if len(period_data) > 0:
        unknown_mask = period_data['harmonized_category_name'].isna() | \
                       period_data['harmonized_category_name'].str.contains('Unknown|Unclassified|Residual', na=False, case=False)
        
        unknown_data = period_data[unknown_mask]
        unknown_count = len(unknown_data)
        unknown_deaths = unknown_data['deaths'].sum()
        total_deaths = period_data['deaths'].sum()
        pct = (unknown_deaths / total_deaths * 100) if total_deaths > 0 else 0
        
        print(f"\n{icd_ver} ({start_yr}-{end_yr}):")
        print(f"  Total records: {len(period_data):,}")
        print(f"  Unknown records: {unknown_count:,}")
        print(f"  Unknown deaths: {unknown_deaths:,.0f}")
        print(f"  Total deaths (35+): {total_deaths:,.0f}")
        print(f"  % Unknown: {pct:.2f}%")
        
        if unknown_count > 0:
            print("  Category breakdown:")
            cat_breakdown = unknown_data['harmonized_category_name'].value_counts()
            for cat, count in cat_breakdown.head(10).items():
                cat_deaths = unknown_data[unknown_data['harmonized_category_name'] == cat]['deaths'].sum()
                print(f"    - {str(cat)[:50]}: {count:,} records, {cat_deaths:,.0f} deaths")
            
            # Show sample source codes
            print("  Sample source codes:")
            sample_codes = unknown_data['cause'].unique()[:5]
            for code in sample_codes:
                if pd.notna(code):
                    print(f"    - {code}")

print("\n" + "="*70)
print("COMPARISON: Ages < 35 in same periods")
print("="*70)

df_under35 = df[df['age_numeric'] < 35].copy()

for start_yr, end_yr, icd_ver in problem_periods:
    period_data = df_under35[(df_under35['year'] >= start_yr) & (df_under35['year'] <= end_yr)]
    
    if len(period_data) > 0:
        unknown_mask = period_data['harmonized_category_name'].isna() | \
                       period_data['harmonized_category_name'].str.contains('Unknown|Unclassified|Residual', na=False, case=False)
        
        unknown_data = period_data[unknown_mask]
        unknown_deaths = unknown_data['deaths'].sum()
        total_deaths = period_data['deaths'].sum()
        pct = (unknown_deaths / total_deaths * 100) if total_deaths > 0 else 0
        
        print(f"\n{icd_ver} ({start_yr}-{end_yr}) - Ages < 35:")
        print(f"  Unknown deaths: {unknown_deaths:,.0f} / {total_deaths:,.0f}")
        print(f"  % Unknown: {pct:.2f}%")

print("\n" + "="*70)
print("Now checking classification outputs folder...")
print("="*70)

socio_ec_path = r'h:\VScode\UK_Socio_Economic_Modelling\data_sources\mortality_stats\socio_economic_classification\outputs'
if os.path.exists(socio_ec_path):
    files = os.listdir(socio_ec_path)
    print(f"Files in {socio_ec_path}:")
    for f in sorted(files):
        print(f"  - {f}")
else:
    print(f"Directory not found: {socio_ec_path}")
