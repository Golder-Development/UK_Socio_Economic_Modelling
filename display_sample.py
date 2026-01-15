import pandas as pd

df = pd.read_csv('data_sources/parliament/extract_20260115_124736/cabinet_ministers.csv')
df['start_date'] = pd.to_datetime(df['start_date'])
df['end_date'] = pd.to_datetime(df['end_date'])

print('Sample records:')
print()
cols = ['given_name', 'family_name', 'post', 'start_date', 'end_date', 'party', 'prime_minister']
sample = df[cols].head(15)

# Print header
print(f"{'Name':<25} {'Post':<50} {'Start Date':<12} {'PM':<20} {'Party':<15}")
print('='*145)

# Print rows
for idx, row in sample.iterrows():
    name = f"{row['given_name']} {row['family_name']}"
    post = row['post'][:47] + '...' if len(str(row['post'])) > 50 else str(row['post'])
    start = str(row['start_date'].date())
    pm = str(row['prime_minister'])
    party = str(row['party']) if pd.notna(row['party']) else 'N/A'
    print(f"{name:<25} {post:<50} {start:<12} {pm:<20} {party:<15}")
