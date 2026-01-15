import pandas as pd
from pathlib import Path

# Get the most recent extract
extract_dir = sorted(Path('data_sources/parliament').glob('extract_*'), key=lambda p: p.stat().st_mtime)[-1]
csv_file = extract_dir / 'cabinet_ministers.csv'

df = pd.read_csv(csv_file)

# Convert dates
df['start_date'] = pd.to_datetime(df['start_date'])
df['end_date'] = pd.to_datetime(df['end_date'])

print('=== Cabinet Ministers Dataset Summary ===\n')
print(f'Total records: {len(df)}')
print(f'Date range: {df["start_date"].min().date()} to {df["end_date"].max().date()}')
print(f'\nUnique ministers: {df["mnis_id"].nunique()}')
print(f'Unique posts: {df["post"].nunique()}')
print(f'Unique prime ministers: {df["prime_minister"].nunique()}')
print(f'\nTop 10 Parties:')
print(df['party'].value_counts().head(10))
print(f'\nPrime Minister distribution:')
print(df['prime_minister'].value_counts())
print(f'\nMember House distribution:')
print(df['member_house'].value_counts())
print(f'\nColumns: {list(df.columns)}')
print(f'\nFile saved to: {csv_file}')
