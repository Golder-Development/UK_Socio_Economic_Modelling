import pandas as pd

df = pd.read_csv('H:/VScode/UK_Socio_Economic_Modelling/data_sources/mortality_stats/development_code/archive_csv/uk_mortality_comprehensive_1901_2019.csv')
print('Full year range:', df['year'].min(), '-', df['year'].max())
print('Total rows:', len(df))
print('Columns:', df.columns.tolist())
print('\nUnique causes by decade:')
for year in [1901, 1911, 1921, 1931, 1941, 1951, 1961, 1971, 1981, 1991, 2001, 2011]:
    subset = df[df['year']==year]
    if len(subset) > 0:
        print(f'{year}: {subset["cause"].nunique()} unique causes')
