import pandas as pd
import numpy as np

print("="*80)
print("COMPARING PUSF.CSV vs PublicFinances1800-2023.CSV")
print("="*80)

# Load PUSF data
pusf_df = pd.read_csv('pusf.csv', header=None, nrows=2, low_memory=False)
pusf_measures = pusf_df.iloc[0, 1:].tolist()
pusf_cdids = pusf_df.iloc[1, 1:].tolist()

print(f"\n1. PUSF.CSV")
print(f"   Total measures: {len(pusf_measures)}")
print(f"   Date range (expected): 1938-2024")
print(f"\n   Sample measures:")
for i, (measure, cdid) in enumerate(list(zip(pusf_measures, pusf_cdids))[:5]):
    print(f"   - {measure} ({cdid})")

# Load Public Finances data
pf_df = pd.read_csv('PublicFinances1800-2023.csv', header=None, nrows=2, low_memory=False)
pf_measures = pf_df.iloc[0, 1:].tolist()
pf_cdids = pf_df.iloc[1, 1:].tolist()

print(f"\n2. PublicFinances1800-2023.CSV")
print(f"   Total measures: {len(pf_measures)}")
print(f"   Date range (expected): 1800-2023")
print(f"\n   Sample measures:")
for i, (measure, cdid) in enumerate(list(zip(pf_measures, pf_cdids))[:5]):
    print(f"   - {measure} ({cdid})")

# Convert to sets for comparison
pusf_set = set(str(m).strip().lower() for m in pusf_measures if pd.notna(m))
pf_set = set(str(m).strip().lower() for m in pf_measures if pd.notna(m))

# Find measures
common = pusf_set & pf_set
pusf_only = pusf_set - pf_set
pf_only = pf_set - pusf_set

print(f"\n3. COMPARISON RESULTS")
print(f"   Common measures: {len(common)}")
print(f"   PUSF only: {len(pusf_only)}")
print(f"   PublicFinances only: {len(pf_only)}")

print(f"\n4. UNIQUE MEASURES IN PublicFinances1800-2023.CSV (NOT in PUSF)")
print(f"   Count: {len(pf_only)}")
for i, measure in enumerate(sorted(list(pf_only))[:20]):
    print(f"   {i+1}. {measure}")
if len(pf_only) > 20:
    print(f"   ... and {len(pf_only) - 20} more")

# Export unique measures to file for detailed review
unique_pf_measures = []
for i, pf_measure in enumerate(pf_measures):
    if pd.notna(pf_measure) and str(pf_measure).strip().lower() not in pusf_set:
        cdid = pf_cdids[i] if i < len(pf_cdids) else ""
        unique_pf_measures.append((str(pf_measure), str(cdid)))

print(f"\n5. DETAILED UNIQUE MEASURES (exported to file)")
with open('unique_measures_comparison.txt', 'w', encoding='utf-8') as f:
    f.write("UNIQUE MEASURES IN PublicFinances1800-2023.CSV (NOT in PUSF)\n")
    f.write("="*80 + "\n\n")
    for i, (measure, cdid) in enumerate(sorted(unique_pf_measures), 1):
        f.write(f"{i}. {measure}\n   CDID: {cdid}\n\n")

print(f"   Exported {len(unique_pf_measures)} unique measures to 'unique_measures_comparison.txt'")
