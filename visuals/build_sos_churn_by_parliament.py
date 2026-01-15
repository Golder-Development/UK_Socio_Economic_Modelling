"""
Build a one-row-per-Parliament summary table of Secretary of State churn,
using cabinet_ministers.csv (unfiltered) as input.

Outputs:
- data/parliamentary_churn_summary.csv
- outputs/sos_churn_bar.png

Assumptions:
- "Secretary of State" is identified by substring match in the 'post' field.
- Parliament start/end dates are fetched from Parliament's "parliament periods" endpoint.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple
import json

import pandas as pd
import matplotlib.pyplot as plt
import requests


# Find the most recent cabinet ministers extract
EXTRACT_BASE_DIR = Path("data_sources/parliament/most recent extract")
if EXTRACT_BASE_DIR.exists():
    # Use symlinked most recent extract folder if it exists
    INPUT_CSV = EXTRACT_BASE_DIR / "cabinet_ministers.csv"
else:
    # Fallback to timestamped extract (adjust timestamp as needed)
    INPUT_CSV = Path("data_sources/parliament/extract_20260115_125959/cabinet_ministers.csv")

OUTPUT_DIR = Path("data_sources/parliament/most recent output")
PARLIAMENTS_CACHE = OUTPUT_DIR / "parliaments_periods.json"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PARLIAMENT_PERIODS_URL = "https://electionresults.parliament.uk/parliament-periods"

MEDIA_MARKERS: List[Tuple[str, str]] = [
    ("1978-01-01", "Radio"),
    ("1989-01-01", "TV (Commons)"),
    ("2000-01-01", "Rolling news"),
    ("2010-01-01", "Clip/social"),
]


def load_cabinet_ministers(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")

    # If end_date missing (currently serving), treat as "today" for calculations
    df["end_date"] = df["end_date"].fillna(pd.Timestamp.today().normalize())

    # Useful derived column for distinct person label
    df["person_name"] = (df["given_name"].fillna("") + " " + df["family_name"].fillna("")).str.strip()

    return df


def filter_secretaries_of_state(df: pd.DataFrame) -> pd.DataFrame:
    # Strictly "Secretaries of State first"
    mask = df["post"].astype(str).str.contains("Secretary of State", case=False, na=False)
    result = df.loc[mask].copy()
    print(f"Cabinet ministers total: {len(df)}")
    print(f"Secretaries of State filtered: {len(result)}")
    return result


def fetch_parliament_periods() -> pd.DataFrame:
    """
    Fetch and parse Parliament periods (numbered parliaments with start/end dates).
    Caches locally to avoid repeated API calls.

    The endpoint returns HTML with recent parliaments only. We supplement with 
    historical parliament data from 1945-2010.
    """
    # Check if cached data exists
    if PARLIAMENTS_CACHE.exists():
        print(f"Loading cached parliament periods from: {PARLIAMENTS_CACHE}")
        with open(PARLIAMENTS_CACHE, "r") as f:
            data = json.load(f)
        parls = pd.DataFrame(data)
        # Re-convert date columns
        parls["parliament_start_date"] = pd.to_datetime(parls["parliament_start_date"])
        parls["parliament_end_date"] = pd.to_datetime(parls["parliament_end_date"])
        return parls

    # Fetch from API if not cached (only gets recent parliaments)
    print("Fetching parliament periods from API...")
    resp = requests.get(PARLIAMENT_PERIODS_URL, timeout=30)
    resp.raise_for_status()

    tables = pd.read_html(resp.text)
    if not tables:
        raise RuntimeError("No tables found on parliament periods page.")

    # The first table on that page is the periods list.
    parls = tables[0].copy()

    # Expected columns include something like: parliament_period, summoned_on, dissolved_on
    # Normalise names:
    parls.columns = [str(c).strip().lower().replace(" ", "_") for c in parls.columns]

    # Identify likely columns
    if "parliament_period" in parls.columns:
        period_col = "parliament_period"
    elif "period" in parls.columns:
        period_col = "period"
    else:
        period_col = None

    if "summoned_on" in parls.columns:
        start_col = "summoned_on"
    elif "start_date" in parls.columns:
        start_col = "start_date"
    else:
        start_col = None

    if "dissolved_on" in parls.columns:
        end_col = "dissolved_on"
    elif "end_date" in parls.columns:
        end_col = "end_date"
    else:
        end_col = None

    if not (start_col and end_col):
        raise RuntimeError(f"Could not find date columns in parliament periods table. Columns: {parls.columns.tolist()}")

    parls["parliament_start_date"] = pd.to_datetime(parls[start_col])
    # Some entries have '-' for current Parliament end date
    parls["parliament_end_date"] = pd.to_datetime(parls[end_col], errors="coerce")
    parls["parliament_end_date"] = parls["parliament_end_date"].fillna(pd.Timestamp.today().normalize())

    # Extract an integer parliament number if possible
    # period_col might be "59th Parliament" or similar
    if period_col:
        parls["parliament_number"] = (
            parls[period_col].astype(str).str.extract(r"(\d+)", expand=False).astype(float).astype("Int64")
        )
    else:
        parls["parliament_number"] = pd.Series([pd.NA] * len(parls), dtype="Int64")

    keep = ["parliament_number", "parliament_start_date", "parliament_end_date"]
    parls = parls[keep].sort_values("parliament_start_date").reset_index(drop=True)

    # Add historical parliaments (1945-2010) from known UK election dates
    # Parliament numbers: 31-54 (1945-2010)
    historical_data = [
        (31, "1945-07-05", "1950-02-23"),
        (32, "1950-02-23", "1951-10-25"),
        (33, "1951-10-25", "1955-05-26"),
        (34, "1955-05-26", "1959-09-08"),
        (35, "1959-09-08", "1964-03-25"),
        (36, "1964-03-25", "1966-03-31"),
        (37, "1966-03-31", "1970-06-18"),
        (38, "1970-06-18", "1974-02-28"),
        (39, "1974-02-28", "1974-10-10"),
        (40, "1974-10-10", "1979-05-03"),
        (41, "1979-05-03", "1983-06-09"),
        (42, "1983-06-09", "1987-06-11"),
        (43, "1987-06-11", "1992-04-09"),
        (44, "1992-04-09", "1997-04-17"),
        (45, "1997-04-17", "2001-06-07"),
        (46, "2001-06-07", "2005-05-05"),
        (47, "2005-05-05", "2010-05-06"),
        (48, "2010-05-06", "2010-05-18"),  # Brief parliament before May 2010 parliament 55
    ]
    
    hist_df = pd.DataFrame(historical_data, columns=["parliament_number", "parliament_start_date", "parliament_end_date"])
    hist_df["parliament_start_date"] = pd.to_datetime(hist_df["parliament_start_date"])
    hist_df["parliament_end_date"] = pd.to_datetime(hist_df["parliament_end_date"])
    hist_df["parliament_number"] = hist_df["parliament_number"].astype("Int64")
    
    # Combine historical and recent data
    parls = pd.concat([hist_df, parls], ignore_index=True)
    parls = parls.sort_values("parliament_start_date").reset_index(drop=True)

    parls["parliament_duration_days"] = (
        parls["parliament_end_date"] - parls["parliament_start_date"]
    ).dt.days + 1

    # Cache to JSON
    print(f"Caching parliament periods to: {PARLIAMENTS_CACHE}")
    parls_json = parls.copy()
    parls_json["parliament_start_date"] = parls_json["parliament_start_date"].astype(str)
    parls_json["parliament_end_date"] = parls_json["parliament_end_date"].astype(str)
    parls_json.to_json(PARLIAMENTS_CACHE, orient="records", indent=2)

    return parls


def split_spells_across_parliaments(spells: pd.DataFrame, parls: pd.DataFrame) -> pd.DataFrame:
    """
    For each SoS spell, create per-Parliament segments based on overlap.
    """
    out_rows = []
    print(f"\nSoS spells to match: {len(spells)}")
    print(f"Parliament periods: {len(parls)}")
    print(f"Parliament date range: {parls['parliament_start_date'].min()} to {parls['parliament_end_date'].max()}")

    for _, r in spells.iterrows():
        rs = r["start_date"]
        re = r["end_date"]
        if pd.isna(rs) or pd.isna(re) or re < rs:
            continue

        overlaps = parls[
            (parls["parliament_end_date"] >= rs) & (parls["parliament_start_date"] <= re)
        ]

        for _, p in overlaps.iterrows():
            seg_start = max(rs, p["parliament_start_date"])
            seg_end = min(re, p["parliament_end_date"])
            if seg_end < seg_start:
                continue

            row = r.to_dict()
            row["parliament_number"] = int(p["parliament_number"]) if pd.notna(p["parliament_number"]) else None
            row["parliament_start_date"] = p["parliament_start_date"]
            row["parliament_end_date"] = p["parliament_end_date"]
            row["segment_start_date"] = seg_start
            row["segment_end_date"] = seg_end
            row["segment_days"] = int((seg_end - seg_start).days) + 1
            out_rows.append(row)

    result = pd.DataFrame(out_rows)
    print(f"Parliament-matched segments: {len(result)}")
    return result


def build_summary(seg: pd.DataFrame, parls: pd.DataFrame) -> pd.DataFrame:
    """
    One row per Parliament, with both raw counts and normalised measures.
    """
    base = parls.copy()

    # Distinct people who served as SoS during that Parliament
    people = (
        seg.groupby("parliament_number")["person_id"]
        .nunique()
        .rename("num_secretaries_of_state")
        .reset_index()
    )

    # Departments count (approx: use 'post' text as a proxy for department name)
    # If your data has a department field in future, swap it in here.
    departments = (
        seg.assign(department_guess=seg["post"].astype(str))
        .groupby("parliament_number")["department_guess"]
        .nunique()
        .rename("num_departments")
        .reset_index()
    )

    # Tenure distribution inside each Parliament (per person/post segments summed)
    tenure = (
        seg.groupby(["parliament_number", "person_id", "post"])["segment_days"]
        .sum()
        .reset_index()
    )

    tenure_stats = (
        tenure.groupby("parliament_number")["segment_days"]
        .agg(
            median_tenure_days="median",
            min_tenure_days="min",
            max_tenure_days="max",
        )
        .reset_index()
    )

    summary = base.merge(people, on="parliament_number", how="left")
    summary = summary.merge(departments, on="parliament_number", how="left")
    summary = summary.merge(tenure_stats, on="parliament_number", how="left")

    summary["num_secretaries_of_state"] = summary["num_secretaries_of_state"].fillna(0).astype(int)
    summary["num_departments"] = summary["num_departments"].fillna(0).astype(int)

    # Normalised churn: distinct SoS per year of Parliament duration
    summary["appointments_per_year"] = summary["num_secretaries_of_state"] / (
        summary["parliament_duration_days"] / 365.25
    )

    def media_era(dt: pd.Timestamp) -> str:
        y = dt.year
        if y < 1978:
            return "pre_radio"
        if y < 1989:
            return "radio"
        if y < 2000:
            return "tv"
        if y < 2010:
            return "rolling_news"
        return "social_clip"

    summary["media_era_flag"] = summary["parliament_start_date"].apply(media_era)

    return summary.sort_values("parliament_start_date").reset_index(drop=True)


def plot_bar(summary: pd.DataFrame) -> Path:
    x = summary["parliament_start_date"]
    y = summary["appointments_per_year"]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(x, y)

    ax.set_title("Secretary of State churn by Parliament (distinct appointees per year)")
    ax.set_xlabel("Parliament start date")
    ax.set_ylabel("Distinct Secretaries of State per year (normalised)")

    for d_str, label in MEDIA_MARKERS:
        dt = pd.to_datetime(d_str)
        ax.axvline(dt, linestyle="--")
        ax.text(dt, ax.get_ylim()[1] * 0.95, label, rotation=90, va="top")

    fig.autofmt_xdate()
    out = OUTPUT_DIR / "sos_churn_bar.jpg"
    fig.tight_layout()
    fig.savefig(out, dpi=200, format='jpg', bbox_inches='tight')
    plt.close(fig)
    return out


def main() -> None:
    print(f"Loading cabinet ministers from: {INPUT_CSV}")
    df = load_cabinet_ministers(INPUT_CSV)
    print(f"Loaded {len(df)} total records")
    print(f"Cabinet ministers date range: {df['start_date'].min()} to {df['end_date'].max()}\n")
    
    sos = filter_secretaries_of_state(df)
    
    parls = fetch_parliament_periods()
    
    seg = split_spells_across_parliaments(sos, parls)
    
    summary = build_summary(seg, parls)
    print(f"\nSummary rows: {len(summary)}")
    print(f"Summary parliament numbers: {summary['parliament_number'].tolist()}\n")

    out_csv = OUTPUT_DIR / "parliamentary_churn_summary.csv"
    summary.to_csv(out_csv, index=False)

    out_jpg = plot_bar(summary)

    print(f"\n✓ Wrote: {out_csv}")
    print(f"✓ Wrote: {out_jpg}")
    print(f"\nRows (parliaments): {len(summary)}")
    print("Summary data:")
    print(summary[['parliament_number', 'parliament_start_date', 'num_secretaries_of_state', 'appointments_per_year']].to_string(index=False))


if __name__ == "__main__":
    main()
