"""
Demonstrate the harmonized category system with example analyses.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path(__file__).parent

print("=" * 80)
print("HARMONIZED MORTALITY DATA DEMONSTRATION")
print("=" * 80)

# Load the harmonized data
df = pd.read_csv(DATA_DIR / "uk_mortality_by_cause_1901_2025_harmonized.csv")

print(f"\nLoaded {len(df):,} rows")
print(f"\nColumns: {df.columns.tolist()}")

# Show sample data
print("\n" + "=" * 80)
print("SAMPLE DATA WITH HARMONIZED CATEGORIES")
print("=" * 80)
sample = df[df["year"] == 1901][
    [
        "year",
        "cause",
        "cause_description",
        "harmonized_category_name",
        "sex",
        "age",
        "deaths",
    ]
].head(10)
print(sample.to_string(index=False))

# Example 1: Trend analysis over time for major categories
print("\n" + "=" * 80)
print("EXAMPLE 1: Deaths by Major Category Over Time")
print("=" * 80)

# Group by year and harmonized category
yearly_by_category = (
    df.groupby(["year", "harmonized_category_name"])["deaths"].sum().reset_index()
)

# Get top categories by total deaths
top_categories = (
    df.groupby("harmonized_category_name")["deaths"].sum().nlargest(5).index.tolist()
)

print(f"\nTop 5 categories by total deaths (1901-2000):")
for i, cat in enumerate(top_categories, 1):
    total = df[df["harmonized_category_name"] == cat]["deaths"].sum()
    print(f"  {i}. {cat}: {total:,.0f} deaths")

# Show year-by-year for top category
print(f"\nYearly deaths for '{top_categories[0]}' (first 10 years):")
top_cat_data = yearly_by_category[
    yearly_by_category["harmonized_category_name"] == top_categories[0]
]
print(top_cat_data.head(10).to_string(index=False))

# Example 2: Compare specific diseases that map to same harmonized category
print("\n" + "=" * 80)
print("EXAMPLE 2: Specific Diseases Within Infectious Diseases Category")
print("=" * 80)

infectious = df[df["harmonized_category_name"] == "Infectious and Parasitic Diseases"]
by_specific_cause = infectious.groupby("cause_description")["deaths"].sum().nlargest(10)

print("\nTop 10 specific infectious diseases by total deaths:")
for i, (disease, deaths) in enumerate(by_specific_cause.items(), 1):
    print(f"  {i:2d}. {disease:50s}: {deaths:>10,.0f} deaths")

# Example 3: Age distribution by harmonized category
print("\n" + "=" * 80)
print("EXAMPLE 3: Age Distribution for Different Categories (1901)")
print("=" * 80)

df_1901 = df[df["year"] == 1901]
age_dist = (
    df_1901.groupby(["harmonized_category_name", "age"])["deaths"].sum().reset_index()
)

for cat in top_categories[:3]:
    cat_age = age_dist[age_dist["harmonized_category_name"] == cat].nlargest(
        5, "deaths"
    )
    print(f"\n{cat}:")
    for _, row in cat_age.iterrows():
        print(f"  Age {row['age']:10s}: {row['deaths']:>8,.0f} deaths")

# Example 4: Demonstrating cross-period consistency
print("\n" + "=" * 80)
print("EXAMPLE 4: Cross-Period Consistency")
print("=" * 80)
print("\nDifferent ICD codes mapping to same harmonized category:")

# Load the harmonized mapping to show examples
mapping_df = pd.read_csv(DATA_DIR / "icd_harmonized_categories.csv")

# Show how different codes from different periods map to "Infectious and Parasitic Diseases"
infectious_codes = mapping_df[
    mapping_df["harmonized_category_name"] == "Infectious and Parasitic Diseases"
]

print("\nExamples of codes mapping to 'Infectious and Parasitic Diseases':")
for icd_version in ["ICD-1 (1901-1910)", "ICD-5 (1940-1949)", "ICD-9c (1994-2000)"]:
    version_codes = infectious_codes[
        infectious_codes["icd_version"] == icd_version
    ].head(3)
    print(f"\n{icd_version}:")
    for _, row in version_codes.iterrows():
        print(f"  Code {row['code']:10s}: {row['original_description']}")

# Summary statistics
print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)

print(f"\nTotal deaths in dataset: {df['deaths'].sum():,.0f}")
print(f"Year range: {df['year'].min():.0f} - {df['year'].max():.0f}")
print(f"Unique harmonized categories: {df['harmonized_category_name'].nunique()}")
print(
    f"Rows with harmonized categories: {df['harmonized_category_name'].notna().sum():,} / {len(df):,}"
)

print("\n" + "=" * 80)
print("READY FOR ANALYSIS!")
print("=" * 80)
print("\nYou can now:")
print("1. Perform time series analysis across the full 1901-2000 period")
print("2. Compare trends between different disease categories")
print("3. Analyze age/sex patterns within consistent categories")
print("4. Create visualizations without worrying about ICD version changes")
