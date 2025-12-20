import pandas as pd
import xlrd

# Import data from popln_tcm77-215653.xls
data_path = 'DataSources/popln_tcm77-215653.xls'
xls = pd.ExcelFile(data_path)
df = pd.read_excel(xls, 1)  # Adjust sheet name as necessary

# remove blank columns
df = df.dropna(axis=1, how='all')

# show the first few rows to understand the structure
print(df.head())

# Import populations20012016.xls to df2
data_path_2 = 'DataSources/populations20012016.xls'
xls2 = pd.ExcelFile(data_path_2)
df2 = pd.read_excel(xls2, 1)  # Adjust sheet name as necessary

# remove blank columns again
df2 = df2.dropna(axis=1, how='all')
# show the first few rows to understand the structure
print(df2.head())

# drop sort column from DF2
df2 = df2.drop(columns=['Sort'])
# rename columns in df2 to match df year=yr, agegroup=age, sex=sex, pops=pop
df2 = df2.rename(columns={'Year': 'YR', 'AgeGroup': 'AGE', 'Sex': 'SEX', 'Pops': 'POP'})
# Append df and df2
df_combined = pd.concat([df, df2], ignore_index=True)
# Save combined dataframe to a new CSV file
df_combined.to_csv('DataSources/combined_population_data.csv', index=False)
print("Combined data saved to DataSources/combined_population_data.csv")
