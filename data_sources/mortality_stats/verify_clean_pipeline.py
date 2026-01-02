import pandas as pd

# Load the clean L1-classified file
df = pd.read_csv('uk_mortality_by_cause_1901_onwards_L1.csv')

# Check ICD-2 specifically
df_icd2 = df[df['icd_version'] == 'ICD2']
print(f"ICD-2 Records: {len(df_icd2):,}")

codes = df_icd2['cause'].unique()
numeric = [int(c) for c in codes if str(c).isdigit()]
alpha = [c for c in codes if not str(c).isdigit()]

print(f"\nNumeric codes:")
print(f"  Min: {min(numeric)}, Max: {max(numeric)}")
print(f"  Count: {len(numeric)}")

print(f"\nAlphanumeric codes: {len(alpha)}")
print(f"  Sample: {alpha[:10]}")

# Check for codes > 190
high = [c for c in numeric if c > 190]
print(f"\nCodes > 190: {len(high)}")
if high:
    print(f"  Found: {high[:10]}")

# Check unmatched
unmatched = df_icd2[df_icd2['L1_category'].isna()]
print(f"\nUnmatched ICD-2 records: {len(unmatched):,}")

# Overall stats
print(f"\n{'='*60}")
print(f"OVERALL PIPELINE RESULTS")
print(f"{'='*60}")
print(f"Total records: {len(df):,}")
print(f"L1 classifications: {df['L1_category'].notna().sum():,}")
print(f"Match rate: {df['L1_category'].notna().sum() / len(df) * 100:.1f}%")

print(f"\nICD versions:")
for version in sorted(df['icd_version'].unique()):
    df_v = df[df['icd_version'] == version]
    matched = df_v['L1_category'].notna().sum()
    pct = matched / len(df_v) * 100
    print(f"  {version}: {len(df_v):,} records, {matched:,} matched ({pct:.1f}%)")
