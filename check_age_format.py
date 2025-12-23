import pandas as pd
import zipfile
from pathlib import Path

zip_path = Path('data_sources/mortality_stats/uk_mortality_by_cause_1901_onwards.zip')
with zipfile.ZipFile(zip_path) as zf:
    df = pd.read_csv(zf.open('uk_mortality_by_cause_1901_onwards.csv'))

print('Age column unique values (first 30):')
print(df['age'].unique()[:30])
print(f'\nAge dtype: {df["age"].dtype}')
print(f'\nSample ages from first 20 rows:')
print(df['age'].head(20).tolist())
print(f'\nValue counts (top 10):')
print(df['age'].value_counts().head(10))
