import pandas as pd

df = pd.read_csv('data_sources/population/uk_population_harmonized_age_groups.csv')
print('Shape:', df.shape)
print('\nFirst 20 rows:')
print(df.head(20))
print('\nYears:', df['year'].min(), '-', df['year'].max())
print('Age groups:', sorted(df['age_group'].unique()))
print('Sex:', sorted(df['sex'].unique()))
print('\nTotal population 1901:', df[df['year'] == 1901]['population'].sum())
print('Total population 2000:', df[df['year'] == 2000]['population'].sum())
