import pandas as pd

df = pd.read_csv('uk_mortality_by_cause_1901_2025.csv')
desc_df = pd.read_csv('icd_code_descriptions.csv')

print('Unique causes by year range:')
year_ranges = [
    (1901, 1910, 'ICD-1'),
    (1911, 1920, 'ICD-2'),
    (1921, 1930, 'ICD-3'),
    (1931, 1939, 'ICD-4'),
    (1940, 1949, 'ICD-5'),
]

for start, end, icd in year_ranges:
    year_df = df[(df['year'] >= start) & (df['year'] <= end)]
    causes = year_df['cause'].unique()
    print(f'\n{start}-{end} ({icd}): {len(causes)} unique causes')
    print(f'  Data sample: {list(causes[:10])}')
    
    # Check what codes are in the description file for this ICD
    icd_codes = desc_df[desc_df['icd_version'] == f'{icd} ({start}-{end})']['code'].unique()
    print(f'  Description codes available: {len(icd_codes)}')
    print(f'  Description sample: {list(icd_codes[:10])}')
