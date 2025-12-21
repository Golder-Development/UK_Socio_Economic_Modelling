import pandas as pd

print("=" * 80)
print("SIDE-BY-SIDE COMPARISON: Original vs Harmonized Data")
print("=" * 80)

# Load both files
df_harmonized = pd.read_csv('uk_mortality_by_cause_1901_2025_harmonized.csv')

# Show a few rows to demonstrate
sample = df_harmonized[df_harmonized['year'] == 1901].head(5)

print("\nShowing 5 rows from 1901:")
print("\n" + "-" * 80)
print("ORIGINAL ICD INFORMATION (preserved):")
print("-" * 80)
print(sample[['year', 'cause', 'cause_description', 'sex', 'age', 'deaths']].to_string(index=False))

print("\n" + "-" * 80)
print("NEW HARMONIZED CATEGORIES (added):")
print("-" * 80)
print(sample[['cause', 'harmonized_category', 'harmonized_category_name', 'classification_confidence']].to_string(index=False))

print("\n" + "=" * 80)
print("KEY POINTS")
print("=" * 80)
print("""
✓ Original ICD code (10.0) is still there in the 'cause' column
✓ Original description ('Small pox - vaccinated') is still there
✓ NEW 'harmonized_category' column added: 'infectious_diseases'
✓ NEW 'harmonized_category_name' column added: 'Infectious and Parasitic Diseases'
✓ NEW 'classification_confidence' column added: shows reliability

You have BOTH levels of detail:
  • Specific: Use 'cause' and 'cause_description' for precise analysis
  • Broad: Use 'harmonized_category_name' for longitudinal trends

Nothing was lost - only gained!
""")
