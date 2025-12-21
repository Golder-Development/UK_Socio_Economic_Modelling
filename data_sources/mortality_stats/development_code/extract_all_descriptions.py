import xlrd
from pathlib import Path
import pandas as pd

ONS_DOWNLOADS = Path("ons_downloads/extracted")

# Check all ICD files for description sheets
icd_files = [
    "icd1.xls",
    "icd2.xls",
    "icd3.xls",
    "icd4.xls",
    "icd5.xls",
    "icd6.xls",
    "icd7.xlsx",
    "icd8.xls",
    "icd9_a.xlsx",
    "icd9_b.xls",
    "icd9_c.xls",
]

all_descriptions = {}

for filename in icd_files:
    filepath = ONS_DOWNLOADS / filename
    if not filepath.exists():
        print(f"File not found: {filename}")
        continue

    print(f"\n{'='*80}")
    print(f"Examining {filename}")
    print("=" * 80)

    try:
        if filename.endswith(".xlsx"):
            # Use pandas for xlsx files
            xls = pd.ExcelFile(filepath)
            sheet_names = xls.sheet_names
            print(f"Sheet names: {sheet_names}")

            # Look for description sheet
            desc_sheet = None
            for name in sheet_names:
                if "descr" in name.lower():
                    desc_sheet = name
                    break

            if desc_sheet:
                df = pd.read_excel(filepath, sheet_name=desc_sheet)
                print(f"\nDescription sheet: {desc_sheet}")
                print(f"Columns: {df.columns.tolist()}")
                print(f"Rows: {len(df)}")
                print("\nFirst 5 entries:")
                print(df.head())

                # Store the mapping
                if "CODE" in df.columns and "DESCRIPTION" in df.columns:
                    mapping = dict(zip(df["CODE"], df["DESCRIPTION"]))
                    all_descriptions[filename] = mapping
                    print(f"\nStored {len(mapping)} code descriptions from {filename}")
        else:
            # Use xlrd for xls files
            wb = xlrd.open_workbook(filepath)
            sheet_names = wb.sheet_names()
            print(f"Sheet names: {sheet_names}")

            # Look for description sheet
            desc_sheet = None
            for name in sheet_names:
                if "descr" in name.lower():
                    desc_sheet = name
                    break

            if desc_sheet:
                ws = wb.sheet_by_name(desc_sheet)
                print(f"\nDescription sheet: {desc_sheet}")
                print(f"Rows: {ws.nrows}, Columns: {ws.ncols}")

                # Get headers
                if ws.nrows > 0:
                    headers = [ws.cell_value(0, col) for col in range(ws.ncols)]
                    print(f"Headers: {headers}")

                    # Print first 5 entries
                    print("\nFirst 5 entries:")
                    for row_idx in range(1, min(6, ws.nrows)):
                        row_values = [
                            ws.cell_value(row_idx, col) for col in range(ws.ncols)
                        ]
                        print(f"  {row_values}")

                    # Extract mapping if columns are CODE and DESCRIPTION
                    if "CODE" in headers and "DESCRIPTION" in headers:
                        code_col = headers.index("CODE")
                        desc_col = headers.index("DESCRIPTION")
                        mapping = {}
                        for row_idx in range(1, ws.nrows):
                            code = ws.cell_value(row_idx, code_col)
                            desc = ws.cell_value(row_idx, desc_col)
                            if code and desc:
                                mapping[code] = desc
                        all_descriptions[filename] = mapping
                        print(
                            f"\nStored {len(mapping)} code descriptions from {filename}"
                        )

    except Exception as e:
        print(f"Error processing {filename}: {e}")
        import traceback

        traceback.print_exc()

print(f"\n{'='*80}")
print(f"SUMMARY")
print("=" * 80)
print(f"Total files with descriptions: {len(all_descriptions)}")
for filename, mapping in all_descriptions.items():
    print(f"  {filename}: {len(mapping)} codes")
