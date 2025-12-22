import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger("diagnose")

DATA_DIR = Path(__file__).parent
ONS_DOWNLOADS = DATA_DIR / "ons_downloads" / "extracted"

EXCLUDED_SHEETS = {"metadata", "description", "correction notice", "contents", "readme"}


def detect_header_row(df_like):
    """Detect header row index in a DataFrame read with header=None."""
    try:
        max_rows = min(25, len(df_like))
        year_keywords = ["year", "yr", "year of death"]
        for i in range(max_rows):
            row_vals = [str(v).lower() for v in df_like.iloc[i].tolist()]
            if any(any(kw in val for kw in year_keywords) for val in row_vals):
                return i
        return None
    except Exception:
        return None


def clean_and_filter_years(df, year_range=None):
    """Normalize year column and filter plausible rows."""
    df = df.copy()
    df.columns = df.columns.map(lambda x: str(x).strip())
    lower_cols = pd.Index([str(c).lower() for c in df.columns])

    year_col = None
    for candidate in ["year", "yr", "year of death"]:
        if candidate in lower_cols.tolist():
            year_col = df.columns[lower_cols.tolist().index(candidate)]
            break

    if year_col is None and len(df.columns) > 0:
        first_col = df.columns[0]
        years = pd.to_numeric(df[first_col], errors='coerce')
        plausible = years.between(1800, 2100)
        if plausible.sum() > 5:
            year_col = first_col

    if year_col is None:
        return pd.DataFrame()

    df['year'] = pd.to_numeric(df[year_col], errors='coerce')
    df = df[df['year'].between(1800, 2100)]

    if year_range and isinstance(year_range, tuple) and len(year_range) == 2:
        df = df[df['year'].between(year_range[0], year_range[1])]

    df = df.dropna(subset=['year'])
    return df


def diagnose_file(filepath: Path, year_range=None):
    if not filepath.exists():
        log.warning(f"Missing file: {filepath}")
        return []

    log.info(f"\n=== {filepath.name} ===")
    try:
        xls = pd.ExcelFile(filepath)
    except Exception as e:
        log.error(f"Failed to open {filepath.name}: {e}")
        return []

    sheet_results = []
    data_sheets = [s for s in xls.sheet_names if str(s).lower().strip() not in EXCLUDED_SHEETS]

    for sheet in data_sheets:
        try:
            # Raw read (reuse ExcelFile to avoid repeated parsing)
            raw = xls.parse(sheet_name=sheet)
            raw_rows = len(raw)

            # Strategy 1: default header + year detection
            parsed1 = clean_and_filter_years(raw, year_range)
            rows1 = len(parsed1)

            # Strategy 2: headerless read + detect header row
            raw2 = xls.parse(sheet_name=sheet, header=None)
            hdr = detect_header_row(raw2)
            if hdr is not None:
                # construct a DataFrame with detected header row without re-reading
                header_vals = [str(v).strip() for v in raw2.iloc[hdr].tolist()]
                df2 = raw2.iloc[hdr + 1:].copy()
                df2.columns = header_vals
                parsed2 = clean_and_filter_years(df2, year_range)
                rows2 = len(parsed2)
            else:
                rows2 = 0

            # Strategy 3: headerless heuristic on first column
            parsed3 = clean_and_filter_years(raw2, year_range)
            rows3 = len(parsed3)

            best_rows = max(rows1, rows2, rows3)
            sheet_results.append((sheet, raw_rows, rows1, rows2, rows3, best_rows))
            log.info(f"Sheet: {sheet:20} raw={raw_rows:6} strat1={rows1:6} strat2={rows2:6} strat3={rows3:6} best={best_rows:6}")
        except Exception as e:
            log.warning(f"Error reading sheet {sheet}: {e}")

    total_best = sum(r[-1] for r in sheet_results)
    log.info(f"Total best-rows across sheets: {total_best}")
    return sheet_results


def main():
    files_to_check = [
        ("icd2.xls", (1911, 1920)),
        ("icd3.xls", (1921, 1930)),
        ("icd4.xls", (1931, 1939)),
        ("icd5.xls", (1940, 1949)),
        ("icd6.xls", (1950, 1957)),
        ("icd7.xlsx", (1958, 1967)),
        ("icd8.xls", (1968, 1978)),
        ("icd9_a.xlsx", (1979, 1984)),
        ("icd9_b.xls", (1985, 1993)),
        ("icd9_c.xls", (1994, 2000)),
    ]

    for fname, yr in files_to_check:
        diagnose_file(ONS_DOWNLOADS / fname, yr)

    log.info("\nDone.")


if __name__ == "__main__":
    main()
