"""
Build a whisker/box plot showing the spread of Secretary of State tenure periods
across parliaments, with outliers displayed.

Outputs:
- data/sos_tenure_boxplot.jpg

Uses the same cabinet_ministers data and filtering as build_sos_churn_by_parliament.py
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple
import json

import pandas as pd
import matplotlib.pyplot as plt
import requests

# Import classification logic
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data_sources" / "parliament"))
from cabinet_post_classifier import classify_post

# --- Configuration ----------------------------------------------------------
MIN_YEAR = 1970  # Only analyze data from this year onwards


# Find the most recent cabinet ministers extract
EXTRACT_BASE_DIR = Path("data_sources/parliament/most recent extract")
if EXTRACT_BASE_DIR.exists():
    INPUT_CSV = EXTRACT_BASE_DIR / "cabinet_ministers.csv"
else:
    INPUT_CSV = Path("data_sources/parliament/extract_20260115_125959/cabinet_ministers.csv")

OUTPUT_DIR = Path("data_sources/parliament/most recent output")
PARLIAMENTS_CACHE = OUTPUT_DIR / "parliaments_periods.json"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PARLIAMENT_PERIODS_URL = "https://electionresults.parliament.uk/parliament-periods"


def load_cabinet_ministers(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    df["end_date"] = df["end_date"].fillna(pd.Timestamp.today().normalize())
    df["person_name"] = (df["given_name"].fillna("") + " " + df["family_name"].fillna("")).str.strip()
    return df


def filter_secretaries_of_state(df: pd.DataFrame) -> pd.DataFrame:
    # Use classification logic to identify senior Cabinet posts
    # (primarily Secretaries of State, but also PM, Chancellor, etc.)
    house_series = df["member_house"].astype(str).str.lower()
    in_commons = house_series == "commons"
    
    # Apply classification to each post
    classifications = df["post"].apply(lambda p: classify_post(p, {}))
    is_senior = classifications.apply(lambda c: c.is_senior)
    
    mask = is_senior & in_commons
    result = df.loc[mask].copy()
    print(f"Cabinet ministers total: {len(df)}")
    print(f"Senior Cabinet posts (Commons) filtered: {len(result)}")
    return result


def fetch_parliament_periods() -> pd.DataFrame:
    """Fetch and cache parliament periods."""
    if PARLIAMENTS_CACHE.exists():
        print(f"Loading cached parliament periods from: {PARLIAMENTS_CACHE}")
        with open(PARLIAMENTS_CACHE, "r") as f:
            data = json.load(f)
        parls = pd.DataFrame(data)
        parls["parliament_start_date"] = pd.to_datetime(parls["parliament_start_date"])
        parls["parliament_end_date"] = pd.to_datetime(parls["parliament_end_date"])
        return parls

    print("Fetching parliament periods from API...")
    resp = requests.get(PARLIAMENT_PERIODS_URL, timeout=30)
    resp.raise_for_status()

    tables = pd.read_html(resp.text)
    if not tables:
        raise RuntimeError("No tables found on parliament periods page.")

    parls = tables[0].copy()
    parls.columns = [str(c).strip().lower().replace(" ", "_") for c in parls.columns]

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
    parls["parliament_end_date"] = pd.to_datetime(parls[end_col], errors="coerce")
    parls["parliament_end_date"] = parls["parliament_end_date"].fillna(pd.Timestamp.today().normalize())

    if period_col:
        parls["parliament_number"] = (
            parls[period_col].astype(str).str.extract(r"(\d+)", expand=False).astype(float).astype("Int64")
        )
    else:
        parls["parliament_number"] = pd.Series([pd.NA] * len(parls), dtype="Int64")

    keep = ["parliament_number", "parliament_start_date", "parliament_end_date"]
    parls = parls[keep].sort_values("parliament_start_date").reset_index(drop=True)

    # Add historical parliaments (1945-2010)
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
        (48, "2010-05-06", "2010-05-18"),
    ]

    hist_df = pd.DataFrame(historical_data, columns=["parliament_number", "parliament_start_date", "parliament_end_date"])
    hist_df["parliament_start_date"] = pd.to_datetime(hist_df["parliament_start_date"])
    hist_df["parliament_end_date"] = pd.to_datetime(hist_df["parliament_end_date"])
    hist_df["parliament_number"] = hist_df["parliament_number"].astype("Int64")

    parls = pd.concat([hist_df, parls], ignore_index=True)
    parls = parls.sort_values("parliament_start_date").reset_index(drop=True)

    return parls


def split_spells_across_parliaments(spells: pd.DataFrame, parls: pd.DataFrame) -> pd.DataFrame:
    """For each SoS spell, create per-Parliament segments based on overlap."""
    out_rows = []
    print(f"\nSoS spells to match: {len(spells)}")
    print(f"Parliament periods: {len(parls)}")

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


def plot_tenure_boxplot(seg: pd.DataFrame, parls: pd.DataFrame) -> Path:
    """Create a box plot showing tenure distribution per parliament."""
    # Filter out Parliament 48 (extreme outlier)
    seg_filtered = seg[seg["parliament_number"] != 48].copy()
    parls_filtered = parls[parls["parliament_number"] != 48].copy()
    
    # Prepare data for plotting
    plot_data = []
    x_labels = []
    
    for _, p in parls_filtered.iterrows():
        parl_num = int(p["parliament_number"])
        parl_year = p["parliament_start_date"].year
        
        # Get all tenure segments for this parliament
        tenures = seg_filtered[seg_filtered["parliament_number"] == parl_num]["segment_days"].values
        
        if len(tenures) > 0:
            plot_data.append(tenures)
            x_labels.append(f"{parl_year}\n(P{parl_num})")
        else:
            # Still include parliament even if no data, for continuity
            plot_data.append([])
            x_labels.append(f"{parl_year}\n(P{parl_num})")
    
    # Create the box plot
    fig, ax = plt.subplots(figsize=(20, 8))
    
    bp = ax.boxplot(
        plot_data,
        labels=x_labels,
        patch_artist=True,
        showfliers=True,  # Show outliers
        widths=0.6
    )
    
    # Customize box plot appearance
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
        patch.set_alpha(0.7)
    
    for whisker in bp['whiskers']:
        whisker.set(linewidth=1.5, color='navy')
    
    for cap in bp['caps']:
        cap.set(linewidth=1.5, color='navy')
    
    for median in bp['medians']:
        median.set(linewidth=2.5, color='red')
    
    for flier in bp['fliers']:
        flier.set(marker='o', markerfacecolor='red', markersize=5, alpha=0.6)
    
    ax.set_title("Secretary of State Tenure Distribution by Parliament", fontsize=16, fontweight='bold')
    ax.set_xlabel("Parliament (Year)", fontsize=12)
    ax.set_ylabel("Tenure Duration (days)", fontsize=12)
    ax.grid(True, axis='y', alpha=0.3, linestyle='--')
    
    # Rotate x-axis labels for readability
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    fig.tight_layout()
    out = OUTPUT_DIR / "sos_tenure_boxplot.jpg"
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
    parls = parls[parls["parliament_start_date"] >= pd.Timestamp(f"{MIN_YEAR}-01-01")].reset_index(drop=True)
    print(f"Filtering to parliaments from {MIN_YEAR} onwards: {len(parls)} parliaments")

    seg = split_spells_across_parliaments(sos, parls)

    out_jpg = plot_tenure_boxplot(seg, parls)

    print(f"\nWrote: {out_jpg}")
    print(f"\nTenure statistics:")
    print(f"  Mean tenure: {seg['segment_days'].mean():.1f} days")
    print(f"  Median tenure: {seg['segment_days'].median():.1f} days")
    print(f"  Min tenure: {seg['segment_days'].min()} days")
    print(f"  Max tenure: {seg['segment_days'].max()} days")


if __name__ == "__main__":
    main()
