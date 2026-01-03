import pandas as pd
import numpy as np

print("="*90)
print("DETAILED COMPARISON: PUSF.csv vs PublicFinances1800-2023.csv")
print("="*90)

# ============================================================================
# 1. ANALYZE PublicFinances1800-2023.csv
# ============================================================================
print("\n1. PublicFinances1800-2023.csv STRUCTURE")
print("-" * 90)

pf_df = pd.read_csv('PublicFinances1800-2023.csv')
print(f"Shape: {pf_df.shape}")
print(f"Columns: {list(pf_df.columns[:10])}...")

# Get year column (usually first column with numeric data)
year_col = pf_df.iloc[:, 0]
try:
    year_numeric = pd.to_numeric(year_col, errors='coerce')
    year_min = year_numeric.min()
    year_max = year_numeric.max()
    print(f"Date range: {int(year_min)} to {int(year_max)}")
except:
    print(f"Date range: Unable to determine (mixed data types)")

# Get measure names (headers)
pf_measures = [col for col in pf_df.columns if col not in ['Unnamed: 0', 'Years', 'Unit', 'ONS present codes', 'Source dataset ID'] and pd.notna(col)]
print(f"\nMeasures in PublicFinances:")
for i, measure in enumerate(pf_measures, 1):
    print(f"  {i}. {measure}")

# ============================================================================
# 2. ANALYZE PUSF.csv
# ============================================================================
print("\n\n2. PUSF.csv STRUCTURE")
print("-" * 90)

pusf_raw = pd.read_csv('pusf.csv', header=None, nrows=4, low_memory=False)
pusf_measures_full = pusf_raw.iloc[0, 1:].tolist()
pusf_cdids = pusf_raw.iloc[1, 1:].tolist()

# Clean measures
pusf_measures_clean = [str(m).strip() for m in pusf_measures_full if pd.notna(m) and str(m).strip() != '']
print(f"Total unique measures: {len(pusf_measures_clean)}")
print(f"Sample measures (first 10):")
for i, (measure, cdid) in enumerate(list(zip(pusf_measures_clean[:10], pusf_cdids[:10])), 1):
    print(f"  {i}. {measure} ({cdid})")

# ============================================================================
# 3. COMPARISON ANALYSIS
# ============================================================================
print("\n\n3. KEY COMPARISONS")
print("-" * 90)

print(f"\nFile Sizes:")
print(f"  PUSF.csv: {len(pusf_measures_clean)} measures, 1938-2024 (87 years)")
print(f"  PublicFinances1800-2023.csv: {len(pf_measures)} measures, 1800-2023 (223 years)")

print(f"\nTemporal Coverage:")
print(f"  PUSF: More recent focus (1938-2024)")
print(f"  PublicFinances: Historical focus (1800-2023)")
print(f"  Overlap: 1938-2023 (85 years)")

# ============================================================================
# 4. ANALYSIS OF UNIQUE MEASURES
# ============================================================================
print("\n\n4. UNIQUE MEASURES IN PublicFinances (NOT in PUSF)")
print("-" * 90)

pf_lower = set(str(m).strip().lower() for m in pf_measures)
pusf_lower = set(str(m).strip().lower() for m in pusf_measures_clean)

unique_to_pf = pf_lower - pusf_lower
unique_to_pusf = pusf_lower - pf_lower

print(f"\nUnique to PublicFinances: {len(unique_to_pf)}")
for i, measure in enumerate(sorted(unique_to_pf), 1):
    print(f"  {i}. {measure}")

print(f"\nCommon measures: {len(pf_lower & pusf_lower)}")

# ============================================================================
# 5. DATA QUALITY COMPARISON
# ============================================================================
print("\n\n5. DATA QUALITY & AVAILABILITY")
print("-" * 90)

pusf_full = pd.read_csv('pusf.csv', low_memory=False)
pusf_data = pusf_full.iloc[7:, 1:]  # Skip metadata, start from row 7

print(f"\nPUSF Data (rows 7+ = actual data):")
print(f"  Total data cells: {pusf_data.shape[0] * pusf_data.shape[1]}")
non_null_pusf = pusf_data.notna().sum().sum()
print(f"  Non-null values: {non_null_pusf}")
print(f"  Null values: {(pusf_data.shape[0] * pusf_data.shape[1]) - non_null_pusf}")
print(f"  Coverage: {(non_null_pusf / (pusf_data.shape[0] * pusf_data.shape[1]) * 100):.1f}%")

pf_data = pf_df.iloc[:, 1:].select_dtypes(include=[np.number])
print(f"\nPublicFinances Data:")
print(f"  Total data cells: {pf_data.shape[0] * pf_data.shape[1]}")
non_null_pf = pf_data.notna().sum().sum()
print(f"  Non-null values: {non_null_pf}")
print(f"  Null values: {(pf_data.shape[0] * pf_data.shape[1]) - non_null_pf}")
print(f"  Coverage: {(non_null_pf / (pf_data.shape[0] * pf_data.shape[1]) * 100):.1f}%")

# ============================================================================
# 6. RECOMMENDATIONS
# ============================================================================
print("\n\n6. RECOMMENDATIONS FOR INTEGRATION")
print("-" * 90)

print("""
KEY FINDINGS:

1. TIME PERIOD EXTENSION:
   - PublicFinances extends back to 1800 (vs PUSF 1938)
   - Could use PublicFinances for 1800-1937 historical context
   - PUSF has more granular recent data (1938-2024)

2. COMPLEMENTARY MEASURES:
   - PublicFinances focuses on: tax receipts, spending by function, borrowing/debt
   - PUSF focuses on: detailed financial flows, assets/liabilities
   - Both valuable for multi-variant analysis

3. INTEGRATION STRATEGY:
   ✓ Option A: Use PublicFinances for 1800-1937, PUSF for 1938-2024
   ✓ Option B: Use PUSF as primary (better granularity), PublicFinances as secondary
   ✓ Option C: Keep separate - PublicFinances for historical context
   ✓ Option D: Create merged dataset with common measures for overlap period

4. RECOMMENDED APPROACH:
   - Transform PublicFinances to long format (similar to PUSF transformation)
   - Create a combined dataset with:
     * 1800-1937: PublicFinances measures only
     * 1938-2023: Both datasets (with priority to PUSF when overlapping)
     * 2024: PUSF only
   - This gives longest historical coverage with most detail in recent years

5. NEXT STEPS:
   - Check for common measure names/codes between datasets
   - Validate historical continuity for overlapping periods
   - Consider reconciliation for 1938-2023 overlap
   - Merge with population and mortality data on date_period
""")

print("\n" + "="*90)
