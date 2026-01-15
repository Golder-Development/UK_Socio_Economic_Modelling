import pandas as pd
from pathlib import Path

extract_dir = sorted(Path('data_sources/parliament').glob('extract_*'), key=lambda p: p.stat().st_mtime)[-1]
csv_file = extract_dir / 'cabinet_ministers.csv'

df = pd.read_csv(csv_file)
df['tenure_length_days'] = pd.to_numeric(df['tenure_length_days'], errors='coerce')
df['parliament_length_days'] = pd.to_numeric(df['parliament_length_days'], errors='coerce')
df['parliament_start_date'] = pd.to_datetime(df['parliament_start_date'], errors='coerce')

print('=== Enhanced Cabinet Ministers Dataset Summary ===\n')
print(f'File: {csv_file.name}')
print(f'Total records: {len(df)}')
print(f'\nNew fields added:')
print(f'  tenure_length_days:')
print(f'    - Average: {df["tenure_length_days"].mean():.0f} days (~{df["tenure_length_days"].mean()/30:.1f} months)')
print(f'    - Maximum: {df["tenure_length_days"].max():.0f} days (~{df["tenure_length_days"].max()/365:.1f} years)')
print(f'    - Minimum: {df["tenure_length_days"].min():.0f} days')
print(f'\n  parliament_start_date:')
print(f'    - Earliest: {df["parliament_start_date"].min().date()}')
print(f'    - Latest: {df["parliament_start_date"].max().date()}')
print(f'\n  parliament_length_days:')
print(f'    - Average: {df["parliament_length_days"].mean():.0f} days (~{df["parliament_length_days"].mean()/365:.2f} years)')
print(f'    - Maximum: {df["parliament_length_days"].max():.0f} days (~{df["parliament_length_days"].max()/365:.2f} years)')
print(f'    - Minimum: {df["parliament_length_days"].min():.0f} days')
print(f'\nAll columns: {list(df.columns)}')
