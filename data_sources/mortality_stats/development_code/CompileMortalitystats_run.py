"""Compile selected mortality sheets (2001--2019) into one CSV.

Reads sheets named '2001'..'2019' from the Excel workbook located next
to this script, finds the header row containing the expected tokens
(`ICD-10, YR, SEX, AGE, NDTHS`), extracts the table below that header
for each year, concatenates them and writes a single CSV.
"""

import os
import re
import traceback
from typing import List

import pandas as pd


DATA_DIR = os.path.dirname(__file__)
XLS_PATH = os.path.join(DATA_DIR, "21stcenturymortality2017.xls")
OUT_CSV = os.path.join(DATA_DIR, "compiled_mortality_2001_2019.csv")

# Sheets to import
SHEETS = [str(y) for y in range(2001, 2020)]

# Header tokens to identify data tables within sheets
HEADER_TOKENS = ["ICD-10", "YR", "SEX", "AGE", "NDTHS"]


def normalize_token(s: str) -> str:
    s = str(s or "").upper()
    return re.sub(r"[^A-Z0-9]", "", s)


def find_header_row(df: pd.DataFrame, tokens: List[str], max_rows: int = 40):
    norm_tokens = [normalize_token(t) for t in tokens]
    rows_to_check = min(max_rows, len(df))
    for idx in range(rows_to_check):
        row = df.iloc[idx].tolist()
        norm_row = [normalize_token(x) for x in row]
        if all(tok in norm_row for tok in norm_tokens):
            return idx
    return None


def read_year_sheet(xls_path: str, sheet_name: str) -> pd.DataFrame:
    raw = pd.read_excel(xls_path, sheet_name=sheet_name, header=None)

    header_row = find_header_row(raw, HEADER_TOKENS)
    if header_row is None:
        # fallback: combine the first two rows and search again
        if raw.shape[0] >= 2:
            combined = raw.iloc[0].fillna("").astype(str) + " " + raw.iloc[1].fillna("").astype(str)
            combined_norm = [normalize_token(x) for x in combined.tolist()]
            if all(normalize_token(t) in combined_norm for t in HEADER_TOKENS):
                header_row = 1

    if header_row is None:
        # No header found — skip
        return pd.DataFrame()

    header = raw.iloc[header_row].fillna("").astype(str).str.strip().tolist()
    data = raw.iloc[header_row + 1 :].copy()
    data.columns = header
    data.dropna(axis=0, how="all", inplace=True)
    data.dropna(axis=1, how="all", inplace=True)
    if data.shape[0] == 0:
        return pd.DataFrame()
    data["sheet"] = sheet_name
    return data


def main():
    if not os.path.exists(XLS_PATH):
        print(f"Excel file not found: {XLS_PATH}")
        return

    parts = []
    for s in SHEETS:
        try:
            print(f"Reading sheet: {s}")
            df = read_year_sheet(XLS_PATH, s)
            if not df.empty:
                parts.append(df)
            else:
                print(f"  (no table found in sheet {s})")
        except Exception as exc:
            print(f"Failed to read sheet {s}: {exc}")
            traceback.print_exc()

    if not parts:
        print("No data tables were found for the requested sheets.")
        return

    compiled = pd.concat(parts, ignore_index=True, sort=False)
    compiled.to_csv(OUT_CSV, index=False)
    print(f"Saved combined CSV: {OUT_CSV}")
    print(compiled.head().to_string())


if __name__ == "__main__":
    main()
