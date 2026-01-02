import pandas as pd

df = pd.read_csv('uk_mortality_by_cause_1901_onwards_L1.csv')
print("=== MERGED DATASET QUALITY CHECK ===")
print(f"\nTotal records: {len(df):,}")

matched = df['harmonized_category_name'].notna().sum()
unmatched = df['harmonized_category_name'].isna().sum()
match_pct = (matched / len(df) * 100) if len(df) > 0 else 0

print(f"Successfully matched: {matched:,} ({match_pct:.1f}%)")
print(f"Unmatched: {unmatched:,} ({100-match_pct:.1f}%)")

print("\nMatched records sample:")
matched_df = df[df['harmonized_category_name'].notna()].head(10)
print(matched_df[['cause_description', 'year', 'harmonized_category_name', 'harmonization_confidence']].to_string())

print("\n\nUnmatched records sample:")
unmatched_df = df[df['harmonized_category_name'].isna()].head(10)
print(unmatched_df[['cause_description', 'year', 'icd_version']].to_string())

print("\n\nCategory distribution (matched records):")
print(df[df['harmonized_category_name'].notna()]['harmonized_category_name'].value_counts())
