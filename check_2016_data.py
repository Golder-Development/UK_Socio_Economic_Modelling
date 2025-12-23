import pandas as pd

df = pd.read_csv('data_sources/population/development_code/downloaded_sourcefiles/combined_population_data.csv')
print('2016 data:')
df_2016 = df[df['YR'] == 2016][['YR', 'AGE', 'SEX', 'POP']]
print(f"Shape: {df_2016.shape}")
print(f"Age values: {df_2016['AGE'].unique()}")
print(df_2016)
