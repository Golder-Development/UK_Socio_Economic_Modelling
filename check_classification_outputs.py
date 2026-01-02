#!/usr/bin/env python3
"""
Check what happened to the unmatched codes: are they in classification outputs?
"""

import pandas as pd
import os

os.chdir(r'h:\VScode\UK_Socio_Economic_Modelling\data_sources\mortality_stats\socio_economic_classification\outputs')

# Load classification results for problem ICD versions
problem_versions = {
    'ICD-3': 'icd3results.csv',
    'ICD-4': 'icd4results.csv', 
    'ICD-7': 'icd7results.csv',
    'ICD-8': 'icd8results.csv',
    'ICD-10': 'icd10results.csv',
}

print("="*70)
print("CLASSIFICATION OUTPUT ANALYSIS")
print("="*70)

# Codes we saw with high unknown rates
problem_codes = {
    'ICD-3': ['100(1)', '100(2)', '101', '102', '104(1)'],
    'ICD-4': ['100a', '100b', '104', '105', '107(1)'],
    'ICD-7': ['1411', '1412', '1413', '1431', '1451'],
    'ICD-8': ['1411', '1412', '1413', '1431', '1451'],
    'ICD-10': ['1125', '1128', '113', '114', '115'],
}

for icd_ver, filename in problem_versions.items():
    if os.path.exists(filename):
        print(f"\n{icd_ver}: {filename}")
        df = pd.read_csv(filename)
        
        print(f"  Shape: {df.shape}")
        print(f"  Columns: {df.columns.tolist()}")
        
        if 'category_code' in df.columns or 'L1_category' in df.columns:
            # Check for Unknown/unmatched
            cat_col = 'category_code' if 'category_code' in df.columns else 'L1_category'
            unknown = df[df[cat_col].isna() | df[cat_col].str.contains('Unknown|Unmatched|Unclassified', na=True, case=False)]
            print(f"  Unknown/Unmatched records: {len(unknown):,}")
            
            # Look for our problem codes
            if 'code' in df.columns:
                codes = problem_codes.get(icd_ver, [])
                print(f"  Looking for problem codes: {codes}")
                
                for code in codes[:3]:
                    matches = df[df['code'].astype(str) == code]
                    if len(matches) > 0:
                        print(f"    {code}: FOUND - {len(matches)} record(s)")
                        if 'category_code' in matches.columns:
                            print(f"           Classified as: {matches['category_code'].iloc[0]}")
                        if 'L1_category' in matches.columns:
                            print(f"           Classified as: {matches['L1_category'].iloc[0]}")
                    else:
                        print(f"    {code}: NOT FOUND in classification results")
        else:
            print(f"  Available columns: {df.columns.tolist()}")
            print("  First few rows:")
            print(df.head(3))
    else:
        print(f"\n{icd_ver}: {filename} - NOT FOUND")

print("\n" + "="*70)
print("Check if there are any input files with unmatched codes")
print("="*70)

inputs_dir = r'h:\VScode\UK_Socio_Economic_Modelling\data_sources\mortality_stats\socio_economic_classification\inputs'
if os.path.exists(inputs_dir):
    print(f"Files in inputs directory:")
    for f in sorted(os.listdir(inputs_dir)):
        path = os.path.join(inputs_dir, f)
        size = os.path.getsize(path)
        print(f"  - {f} ({size:,} bytes)")
else:
    print(f"Inputs directory not found: {inputs_dir}")
