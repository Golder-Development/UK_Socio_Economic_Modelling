"""Examine the actual structure of one ICD file to understand layout"""
import pandas as pd
from pathlib import Path

data_dir = Path(__file__).parent
xls_file = data_dir / "ons_downloads" / "extracted" / "icd1.xls"

xls = pd.ExcelFile(xls_file)
print(f"File: {xls_file.name}")
print(f"Sheet names: {xls.sheet_names}\n")

for sheet_name in xls.sheet_names[:1]:  # Just look at first sheet
    print(f"\n{'='*70}")
    print(f"Sheet: {sheet_name}")
    print(f"{'='*70}")
    
    df = pd.read_excel(xls_file, sheet_name=sheet_name, nrows=30)
    print(f"\nShape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"\nFirst 20 rows:")
    print(df.head(20).to_string())
