import pandas as pd
from pathlib import Path

# Get the most recent extract
extract_dir = sorted(Path('data_sources/parliament').glob('extract_*'), key=lambda p: p.stat().st_mtime)[-1]
csv_file = extract_dir / 'cabinet_ministers.csv'

df = pd.read_csv(csv_file)

# Convert dates
df['start_date'] = pd.to_datetime(df['start_date'])
df['end_date'] = pd.to_datetime(df['end_date'])
df['parliament_start_date'] = pd.to_datetime(df['parliament_start_date'])

print('=== Cabinet Ministers Dataset - Enhanced Version ===\n')
print(f'File: {csv_file}\n')
print(f'Total records: {len(df)}')
print(f'Date range: {df["start_date"].min().date()} to {df["end_date"].max().date()}')
print(f'\nAverage tenure length: {df["tenure_length_days"].mean():.0f} days')
print(f'Max tenure length: {df["tenure_length_days"].max():.0f} days')
print(f'Min tenure length: {df["tenure_length_days"].min():.0f} days')
print(f'\nAverage parliament length: {df["parliament_length_days"].mean():.0f} days')

print('\n' + '='*100)
print('\nSample records with new fields:\n')

# Show some interesting records
cols = ['given_name', 'family_name', 'post', 'start_date', 'tenure_length_days', 'parliament_start_date', 'parliament_length_days', 'prime_minister']
sample = df[cols].head(10)

for idx, row in sample.iterrows():
    name = f"{row['given_name']} {row['family_name']}"
    post = row['post'][:40] + '...' if len(str(row['post'])) > 40 else str(row['post'])
    start = str(row['start_date'].date())
    tenure = f"{row['tenure_length_days']:.0f}" if pd.notna(row['tenure_length_days']) else 'N/A'
    parl_start = str(row['parliament_start_date'].date())
    parl_len = f"{row['parliament_length_days']:.0f}" if pd.notna(row['parliament_length_days']) else 'N/A'
    pm = str(row['prime_minister'])
    print(f"{name:25} | {post:42} | Start: {start} | Tenure: {tenure:5} days")
    print(f"{'':25}   Parliament started: {parl_start} | Duration: {parl_len:5} days")
    print()

print('='*100)
print(f'\nColumns in dataset: {list(df.columns)}')
