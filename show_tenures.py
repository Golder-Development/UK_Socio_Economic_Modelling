import pandas as pd
from pathlib import Path

extract_dir = sorted(Path('data_sources/parliament').glob('extract_*'), key=lambda p: p.stat().st_mtime)[-1]
csv_file = extract_dir / 'cabinet_ministers.csv'

df = pd.read_csv(csv_file)
df['tenure_length_days'] = pd.to_numeric(df['tenure_length_days'], errors='coerce')

print('='*100)
print('LONGEST SERVING MINISTERS (by tenure in a single post)\n')
print('='*100)

longest = df.nlargest(15, 'tenure_length_days')[['given_name', 'family_name', 'post', 'start_date', 'end_date', 'tenure_length_days', 'prime_minister']]

for idx, (i, row) in enumerate(longest.iterrows(), 1):
    name = f"{row['given_name']} {row['family_name']}"
    post = str(row['post'])[:50]
    days = f"{row['tenure_length_days']:.0f}"
    years = f"{row['tenure_length_days']/365:.1f}"
    pm = str(row['prime_minister'])
    print(f"{idx:2}. {name:25} | {post:50} | {days:6} days ({years:5} years) | PM: {pm}")

print('\n' + '='*100)
print('SHORTEST TENURES (ministers who held posts for very brief periods)\n')
print('='*100)

shortest = df.nsmallest(15, 'tenure_length_days')[['given_name', 'family_name', 'post', 'start_date', 'end_date', 'tenure_length_days', 'prime_minister']]

for idx, (i, row) in enumerate(shortest.iterrows(), 1):
    name = f"{row['given_name']} {row['family_name']}"
    post = str(row['post'])[:50]
    days = f"{row['tenure_length_days']:.0f}"
    pm = str(row['prime_minister'])
    print(f"{idx:2}. {name:25} | {post:50} | {days:6} days | PM: {pm}")
