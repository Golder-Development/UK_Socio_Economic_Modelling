import pandas as pd

df = pd.read_csv("uk_mortality_by_cause_1901_2025_with_descriptions.csv")

print("=== Sample descriptions from different years ===")
for year in [1901, 1920, 1950, 1970, 1990, 2000]:
    year_df = df[df["year"] == year][["cause", "cause_description"]].drop_duplicates()
    if len(year_df) > 0:
        print(f"\n{year} (showing first 5 of {len(year_df)} unique causes):")
        print(year_df.head(5).to_string(index=False))

        # Check match rate
        matched = year_df["cause_description"].notna().sum()
        total = len(year_df)
        print(f"  Match rate: {matched}/{total} ({matched/total*100:.1f}%)")
