import pandas as pd
from pathlib import Path

ONS_DOWNLOADS = Path("ons_downloads/extracted")

# Examine ICD1 file
print("=" * 80)
print("EXAMINING ICD1.XLS")
print("=" * 80)

xls = pd.ExcelFile(ONS_DOWNLOADS / "icd1.xls")
print(f"Sheet names: {xls.sheet_names}")

for sheet_name in xls.sheet_names[:3]:  # First 3 sheets
    print(f"\n--- Sheet: {sheet_name} ---")
    df = pd.read_excel(xls, sheet_name=sheet_name, nrows=15)
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nFirst rows:")
    print(df.head(10))
    print()
