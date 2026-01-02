#!/usr/bin/env python3
import pandas as pd
import os

os.chdir(r'h:\VScode\UK_Socio_Economic_Modelling\data_sources\mortality_stats')

# Load summary
summary = pd.read_csv('icd_unmatched_codes_summary.csv')

print('UNMATCHED CODES SUMMARY - FIRST 20 ROWS')
print('='*100)
print(summary.head(20).to_string(index=False))

# Show by version totals
print('\n\nTOTALS BY ICD VERSION:')
print('='*100)
by_version = summary.groupby('icd_version').agg({
    'total_deaths': 'sum',
    'cause_code': 'count'
}).rename(columns={'cause_code': 'unique_codes'})
by_version = by_version.sort_values('total_deaths', ascending=False)
print(by_version)

# Focus on problem versions
print('\n\nPROBLEM VERSIONS - TOP UNMATCHED CODES:')
print('='*100)
for version in ['ICD-3', 'ICD-4', 'ICD-7', 'ICD-8', 'ICD-10']:
    v_data = summary[summary['icd_version'] == version].nlargest(3, 'total_deaths')
    if len(v_data) > 0:
        print(f'\n{version} - Top 3 unmatched codes:')
        for idx, row in v_data.iterrows():
            print(f'  Code {row["cause_code"]}: {row["total_deaths"]:,.0f} deaths ({int(row["first_year"])}-{int(row["last_year"])})')

# Check ICD-10 detail file
print('\n\nICD-10 UNMATCHED DETAIL FILE (first 10 records):')
print('='*100)
detail = pd.read_csv('icd_unmatched_codes_detail_ICD10.csv')
print(f'Total records: {len(detail):,}')
print(f'Columns: {detail.columns.tolist()}')
print(detail.head(10).to_string())
