import xlrd
from pathlib import Path

ONS_DOWNLOADS = Path("ons_downloads/extracted")

# Examine ICD1 file
print("=" * 80)
print("EXAMINING ICD1.XLS")
print("=" * 80)

wb = xlrd.open_workbook(ONS_DOWNLOADS / "icd1.xls")
print(f"Sheet names: {wb.sheet_names()}")

for sheet_name in wb.sheet_names()[:2]:  # First 2 sheets
    print(f"\n--- Sheet: {sheet_name} ---")
    ws = wb.sheet_by_name(sheet_name)
    
    # Print first row (headers)
    if ws.nrows > 0:
        headers = [ws.cell_value(0, col) for col in range(ws.ncols)]
        print(f"Headers ({len(headers)} columns): {headers}")
        
        # Print a few data rows
        print(f"\nFirst 5 data rows (Total rows: {ws.nrows}):")
        for row_idx in range(1, min(6, ws.nrows)):
            row_values = [ws.cell_value(row_idx, col) for col in range(ws.ncols)]
            print(f"Row {row_idx}: {row_values}")
    
    print()
