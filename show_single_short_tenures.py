import pandas as pd

df = pd.read_csv('generated_charts/cabinet_members_tenure_profile.csv')

# Single short tenures: 1 spell, 30-365 days
single_short = df[(df['num_spells'] == 1) &
                  (df['longest_spell_days'] >= 30) &
                  (df['longest_spell_days'] <= 365)].sort_values('longest_spell_days',
                                                                 ascending=False).head(20)

print('='*100)
print('SINGLE SHORT TENURE MINISTERS (who were they?)')
print('='*100)
print()
for idx, row in single_short.iterrows():
    days = int(row['longest_spell_days'])
    years = row['longest_spell_years']
    party = row['party']
    name = row['person_name']
    posts = row['posts']

    print(f"{name:25} ({party:15}) - {days:3d} days ({years:5.2f} years)")
    print(f"  Posts: {posts}")
    print()

print(f"Total single short tenure ministers: {len(single_short)}")
