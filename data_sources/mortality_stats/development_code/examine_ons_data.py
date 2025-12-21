"""Quick script to examine the structure of historical ONS mortality data."""

import pandas as pd
import os
from pathlib import Path

xls_file = Path(__file__).parent / "ons_downloads" / "extracted" / "icd1.xls"

if xls_file.exists():
    # Check sheets
    xls = pd.ExcelFile(xls_file)
    print("Sheet names (first 10):")
    for sheet in xls.sheet_names[:10]:
        print(f"  {sheet}")

    print(f"\nTotal sheets: {len(xls.sheet_names)}")

    # Sample first sheet
    df = pd.read_excel(xls_file, sheet_name=xls.sheet_names[0], nrows=15)
    print(f"\nFirst sheet columns: {list(df.columns)}")
    print(f"\nFirst few rows:")
    print(df.head(10).to_string())
else:
    print(f"File not found: {xls_file}")
