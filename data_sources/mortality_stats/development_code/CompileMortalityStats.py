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
"""Compile mortality data from '21stcenturymortality2017.xls' into one DataFrame.

This script reads all sheets from the provided Excel file, attempts to
normalize wide tables (where the first column is an identifier like Age
and the remaining columns are years/categories) by melting them, and
concatenates everything into a single DataFrame which is saved as CSV
and pickle for easy reuse.

Usage:
    python CompileMortalitystats.py

Outputs (next to this script):
    - compiled_mortality_21c_2017.csv
    - compiled_mortality_21c_2017.pkl
"""
from __future__ import annotations

import os
import sys
import traceback
from typing import Dict

import pandas as pd


DATA_DIR = os.path.dirname(__file__)
XLS_PATH = os.path.join(DATA_DIR, "21stcenturymortality2017.xls")
OUT_CSV = os.path.join(DATA_DIR, "compiled_mortality_21c_2017.csv")
OUT_PKL = os.path.join(DATA_DIR, "compiled_mortality_21c_2017.pkl")

# Header tokens to identify data tables within sheets
HEADER_TOKENS = ["ICD-10", "YR", "SEX", "AGE", "NDTHS"]


def try_read_excel(path: str) -> Dict[str, pd.DataFrame]:
    """Read all sheets from an Excel file, trying common engines.

    Returns a dict mapping sheet_name -> DataFrame.
    """
    try:
        return pd.read_excel(path, sheet_name=None)
    except Exception as e:
        # Try with explicit older engine for .xls files
        try:
            return pd.read_excel(path, sheet_name=None, engine="xlrd")
        except Exception:
            # Final attempt: let pandas choose but raise original
            raise


def columns_look_like_years(cols) -> bool:
    """Heuristic: are many column names simple year numbers?"""
    if not cols:
        return False
    year_like = 0
    total = 0
    for c in cols:
        total += 1
        s = str(c).strip()
        if s.isdigit():
            try:
                y = int(s)
                if 1800 < y < 2100:
                    year_like += 1
            except Exception:
                pass
    return year_like >= max(1, total // 2)


def process_sheet(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    """Normalize a single sheet into a tidy DataFrame.

    Strategy:
    - Drop fully empty rows/columns.
    - If the sheet looks like a wide table (first column = id, rest = years),
      melt it into long form with columns: id_col, Year, Value.
    - Otherwise, keep the table and add a `sheet` column.
    """
    df = df.copy()
    # Drop fully empty rows/cols early
    df.dropna(axis=0, how="all", inplace=True)
    df.dropna(axis=1, how="all", inplace=True)

    if df.shape[0] == 0 or df.shape[1] == 0:
        return pd.DataFrame()

    # Reset index
    df = df.reset_index(drop=True)

    # Find the header row that contains the expected tokens
    header_row = None
    tokens_upper = [t.upper() for t in HEADER_TOKENS]
    for idx in range(min(20, df.shape[0])):
        row_vals = " ".join([str(x) for x in df.iloc[idx].values if pd.notna(x)]).upper()
        if all(tok in row_vals for tok in tokens_upper):
            header_row = idx
            break

    # If header not found, skip this sheet (not a data table of interest)
    if header_row is None:
        return pd.DataFrame()

    # Use the header row as column names and take rows below as data
    header = df.iloc[header_row].fillna("").astype(str).str.strip().tolist()
    data = df.iloc[header_row + 1 :].copy()
    data.columns = header

    # Drop rows that are fully empty after header assignment
    data.dropna(axis=0, how="all", inplace=True)
    data.dropna(axis=1, how="all", inplace=True)

    # Standard tidy: ensure columns exist and return
    data["sheet"] = sheet_name
    return data


def compile_excel_to_single_df(xls_path: str) -> pd.DataFrame:
    if not os.path.exists(xls_path):
        raise FileNotFoundError(f"Excel file not found: {xls_path}")

    print(f"Reading Excel file: {xls_path}")
    sheets = try_read_excel(xls_path)
    parts = []
    for name, df in sheets.items():
        try:
            processed = process_sheet(df, name)
            if not processed.empty:
                # Add original sheet name and source file
                processed["sheet_name"] = name
                processed["source_file"] = os.path.basename(xls_path)
                parts.append(processed)
        except Exception:
            print(f"Failed processing sheet: {name}")
            traceback.print_exc()

    if not parts:
        return pd.DataFrame()

    compiled = pd.concat(parts, ignore_index=True, sort=False)
    return compiled


def main():
    try:
        df = compile_excel_to_single_df(XLS_PATH)
        if df.empty:
            print("No data compiled (empty DataFrame).")
            return
        # Save outputs
        print(f"Saving compiled data to: {OUT_CSV} and {OUT_PKL}")
        df.to_csv(OUT_CSV, index=False)
        df.to_pickle(OUT_PKL)
        print("Done.")
        # Print sample
        print(df.head().to_string())
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
