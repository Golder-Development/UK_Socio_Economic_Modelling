"""
Compute UK mortality totals per year from compiled mortality CSVs.
Reads available source files in this folder, aggregates deaths by year,
then writes uk_mortality_totals_by_year.csv.

Sources expected (already present in this repo):
- compiled_mortality_2001_2019.csv
- compiled_mortality_21c_2017.csv

The code is defensive: it looks for year column candidates (e.g., 'YR', 'Year')
and for death-count column candidates (e.g., 'NDTHS', any column containing 'death').
Rows with non-numeric year or death counts are ignored.
For overlapping years across sources, the maximum total per year is selected to avoid double-counting.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MORTALITY_DIR = Path(__file__).parent
OUTPUT_FILE = MORTALITY_DIR / "uk_mortality_totals_by_year.csv"


def _list_source_csvs() -> List[Path]:
    candidates = [
        MORTALITY_DIR / "compiled_mortality_2001_2019.csv",
        MORTALITY_DIR / "compiled_mortality_21c_2017.csv",
    ]
    return [p for p in candidates if p.exists()]


def _find_year_col(df: pd.DataFrame) -> Optional[str]:
    cols_lower = {c.lower(): c for c in df.columns}
    for key in ("yr", "year"):
        if key in cols_lower:
            return cols_lower[key]
    # Fallback: any column whose name contains 'year'
    for c in df.columns:
        if "year" in c.lower():
            return c
    return None


def _find_deaths_col(df: pd.DataFrame) -> Optional[str]:
    # Prefer known column 'NDTHS'
    if "NDTHS" in df.columns:
        return "NDTHS"
    # Otherwise search for a column containing 'death'
    for c in df.columns:
        if "death" in c.lower():
            return c
    return None


def _coerce_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _aggregate_file(path: Path) -> pd.DataFrame:
    logger.info(f"Aggregating file: {path.name}")
    # Read with low_memory=False due to wide mixed types; avoid dtype inference issues
    df = pd.read_csv(path, low_memory=False)

    year_col = _find_year_col(df)
    deaths_col = _find_deaths_col(df)

    if not year_col or not deaths_col:
        logger.warning(
            f"Skipping {path.name}: year_col={year_col}, deaths_col={deaths_col} not found"
        )
        return pd.DataFrame(columns=["year", "total_deaths"])  # empty

    years = _coerce_numeric(df[year_col])
    deaths = _coerce_numeric(df[deaths_col])

    valid = (~years.isna()) & (~deaths.isna())
    df_valid = pd.DataFrame(
        {"year": years[valid].astype(int), "deaths": deaths[valid].astype(int)}
    )

    grouped = df_valid.groupby("year", as_index=False)["deaths"].sum()
    grouped.rename(columns={"deaths": "total_deaths"}, inplace=True)
    logger.info(
        f"  Years covered: {grouped['year'].min()}–{grouped['year'].max()} ({len(grouped)} years)"
    )
    return grouped


def compute_totals() -> pd.DataFrame:
    files = _list_source_csvs()
    if not files:
        raise FileNotFoundError("No source mortality CSVs found.")

    per_file = [_aggregate_file(p) for p in files]

    # Outer merge all results on year, then take row-wise max across sources
    if not per_file:
        return pd.DataFrame(columns=["year", "total_deaths"])  # empty

    merged = per_file[0].copy()
    for idx, df in enumerate(per_file[1:], start=2):
        merged = merged.merge(df, on="year", how="outer", suffixes=("", f"_{idx}"))

    # Collect all total_deaths columns
    death_cols = [c for c in merged.columns if c.startswith("total_deaths")]
    merged["total_deaths"] = merged[death_cols].max(axis=1, skipna=True)
    result = merged[["year", "total_deaths"]].sort_values("year").reset_index(drop=True)
    return result


def save_totals(df: pd.DataFrame, output_path: Path = OUTPUT_FILE) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path


def main() -> Tuple[pd.DataFrame, Path]:
    totals = compute_totals()
    out_path = save_totals(totals)
    logger.info(f"Saved totals to: {out_path}")
    # Print preview
    logger.info("First rows:\n" + totals.head(10).to_string(index=False))
    return totals, out_path


if __name__ == "__main__":
    main()
