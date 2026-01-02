import pandas as pd

df = pd.read_csv('uk_mortality_by_cause_1901_2025.zip')
print('Year ranges:')
print(f'Min year: {df["year"].min()}, Max year: {df["year"].max()}')
print()

icd_periods = {
    'ICD-1': (1900, 1909),
    'ICD-2': (1910, 1920),
    'ICD-3': (1921, 1938),
    'ICD-4': (1939, 1948),
    'ICD-5': (1949, 1957),
    'ICD-6': (1958, 1967),
    'ICD-7': (1968, 1978),
    'ICD-8': (1979, 1986),
    'ICD-9': (1987, 1998),
    'ICD-10': (1999, 2100),
}

for version, (start, end) in icd_periods.items():
    count = df[(df['year'] >= start) & (df['year'] <= end)].shape[0]
    if count > 0:
        print(f'{version} ({start}-{end}): {count:,} records')
