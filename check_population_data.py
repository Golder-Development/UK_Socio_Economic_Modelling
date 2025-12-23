import pandas as pd

df = pd.read_csv('data_sources/population/combined_population_data.csv')
print(f'Shape: {df.shape}')
print(f'\nColumns: {df.columns.tolist()}')
print(f'\nFirst 5 rows:')
print(df.head())
print(f'\nYear range: {df["YR"].min()} - {df["YR"].max()}')
print(f'\nData types:')
print(df.dtypes)
print(f'\nSex values: {df["SEX"].unique()}')
print(f'\nAge values (first 20): {df["AGE"].unique()[:20]}')
print(f'\nAgegroup values: {df["Agegroup"].unique()}')

