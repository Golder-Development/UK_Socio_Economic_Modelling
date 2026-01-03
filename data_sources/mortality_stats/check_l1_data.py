import zipfile
import pandas as pd

with zipfile.ZipFile('uk_mortality_by_cause_1901_onwards_l1.zip', 'r') as z:
    print('Files in archive:')
    for name in z.namelist():
        print(f'  {name}')
    
    csv_file = [n for n in z.namelist() if n.endswith('.csv')][0]
    
    with z.open(csv_file) as f:
        df = pd.read_csv(f, low_memory=False)
        print(f'\nFile: {csv_file}')
        print(f'Shape: {df.shape}')
        print(f'Columns: {df.columns.tolist()}')
        print(f'\nYear range: {df["year"].min()} - {df["year"].max()}')
        print(f'\nFirst 20 rows:')
        print(df.head(20))
        print(f'\nUnique L1 categories:')
        print(df[['harmonized_category_code', 'harmonized_category_name']].drop_duplicates().sort_values('harmonized_category_code'))
        
        print(f'\nSample aggregation by year and category:')
        agg = df.groupby(['year', 'harmonized_category_name'])['deaths'].sum().reset_index()
        print(agg.head(30))
