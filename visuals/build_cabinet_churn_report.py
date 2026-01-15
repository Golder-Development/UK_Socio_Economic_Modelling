"""
Generate an interactive HTML report combining:
1. Secretary of State churn by Parliament (bar chart)
2. Tenure distribution by Parliament (box plot)

Outputs:
- data_sources/parliament/most recent output/cabinet_churn_report.html
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple
import json

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys

# Import classification logic
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data_sources" / "parliament"))
from cabinet_post_classifier import classify_post

# --- Configuration ----------------------------------------------------------
MIN_YEAR = 1966  # Only analyze data from this year onwards

# Find the most recent cabinet ministers extract
EXTRACT_BASE_DIR = Path("data_sources/parliament/most recent extract")
if EXTRACT_BASE_DIR.exists():
    INPUT_CSV = EXTRACT_BASE_DIR / "cabinet_ministers.csv"
else:
    INPUT_CSV = Path("data_sources/parliament/extract_20260115_125959/cabinet_ministers.csv")

OUTPUT_DIR = Path("data_sources/parliament/most recent output")
PARLIAMENTS_CACHE = OUTPUT_DIR / "parliaments_periods.json"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Output for generated charts
CHARTS_OUTPUT_DIR = Path("generated_charts")
CHARTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PARLIAMENT_PERIODS_URL = "https://electionresults.parliament.uk/parliament-periods"

MEDIA_MARKERS: List[Tuple[str, str]] = [
    ("1978-01-01", "Radio"),
    ("1989-01-01", "TV (Commons)"),
    ("2000-06-07", "Rolling news"),
    ("2010-05-18", "Clip/social"),
]


def load_cabinet_ministers(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    df["end_date"] = df["end_date"].fillna(pd.Timestamp.today().normalize())
    df["person_name"] = (df["given_name"].fillna("") + " " + df["family_name"].fillna("")).str.strip()
    return df


def filter_secretaries_of_state(df: pd.DataFrame) -> pd.DataFrame:
    # Use classification logic to identify senior Cabinet posts
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

    # Historical parliaments (fallback if cache doesn't exist)
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
        (55, "2010-05-18", "2015-05-18"),
        (56, "2015-05-18", "2017-06-13"),
        (57, "2017-06-13", "2019-12-17"),
        (58, "2019-12-17", "2024-07-09"),
        (59, "2024-07-09", pd.Timestamp.today().strftime("%Y-%m-%d")),
    ]
    
    df = pd.DataFrame(historical_data, columns=["parliament_number", "parliament_start_date", "parliament_end_date"])
    df["parliament_start_date"] = pd.to_datetime(df["parliament_start_date"])
    df["parliament_end_date"] = pd.to_datetime(df["parliament_end_date"])
    df["parliament_number"] = df["parliament_number"].astype("Int64")
    
    return df


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


def build_summary(seg: pd.DataFrame, parls: pd.DataFrame) -> pd.DataFrame:
    """One row per Parliament, with both raw counts and normalised measures."""
    base = parls.copy()
    base["parliament_duration_days"] = (base["parliament_end_date"] - base["parliament_start_date"]).dt.days + 1

    # Distinct people who served during that Parliament
    people = (
        seg.groupby("parliament_number")["person_id"]
        .nunique()
        .rename("num_secretaries_of_state")
        .reset_index()
    )

    # Tenure distribution inside each Parliament
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
    summary = summary.merge(tenure_stats, on="parliament_number", how="left")

    summary["num_secretaries_of_state"] = summary["num_secretaries_of_state"].fillna(0).astype(int)

    # Normalised churn: distinct SoS per year of Parliament duration
    summary["appointments_per_year"] = summary["num_secretaries_of_state"] / (
        summary["parliament_duration_days"] / 365.25
    )

    return summary.sort_values("parliament_start_date").reset_index(drop=True)


def create_churn_chart(summary: pd.DataFrame) -> go.Figure:
    """Create interactive bar chart of churn by parliament."""
    # Filter out Parliament 48 (extreme outlier)
    plot_data = summary[summary["parliament_number"] != 48].copy()
    
    x_labels = [f"Parliament {int(row['parliament_number'])} ({row['parliament_start_date'].year})" 
                for _, row in plot_data.iterrows()]
    y = plot_data["appointments_per_year"]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=x_labels,
        y=y,
        marker=dict(color='steelblue', line=dict(color='navy', width=1)),
        text=[f"{val:.1f}" for val in y],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Churn Rate: %{y:.2f} appointees/year<extra></extra>'
    ))
    
    # Add media era markers
    for d_str, label in MEDIA_MARKERS:
        dt = pd.to_datetime(d_str)
        matching = plot_data[
            (plot_data["parliament_start_date"] <= dt) & 
            (plot_data["parliament_end_date"] >= dt)
        ]
        if not matching.empty:
            parl_year = matching.iloc[0]["parliament_start_date"].year
            parl_num = int(matching.iloc[0]["parliament_number"])
            marker_label = f"Parliament {parl_num} ({parl_year})"
            if marker_label in x_labels:
                idx = x_labels.index(marker_label)
                max_y = max(y) * 1.1
                fig.add_annotation(
                    x=idx,
                    y=max_y * 0.95,
                    text=label,
                    showarrow=False,
                    font=dict(size=10, style='italic'),
                    bgcolor='wheat',
                    opacity=0.8,
                    borderpad=4
                )
    
    fig.update_layout(
        title=dict(
            text=f"Senior Cabinet Churn by Parliament ({MIN_YEAR} onwards)<br><sub>Distinct appointees per year (normalised)</sub>",
            font=dict(size=18)
        ),
        xaxis=dict(title="Parliament Number (Year)", tickangle=45),
        yaxis=dict(title="Appointees per year"),
        height=500,
        hovermode='x unified',
        showlegend=False
    )
    
    return fig


def create_tenure_boxplot(seg: pd.DataFrame, parls: pd.DataFrame) -> go.Figure:
    """Create interactive box plot of tenure distribution."""
    # Filter out Parliament 48
    seg_filtered = seg[seg["parliament_number"] != 48].copy()
    parls_filtered = parls[parls["parliament_number"] != 48].copy()
    
    fig = go.Figure()
    
    x_labels = []
    for _, p in parls_filtered.iterrows():
        parl_num = int(p["parliament_number"])
        parl_year = p["parliament_start_date"].year
        
        tenures = seg_filtered[seg_filtered["parliament_number"] == parl_num]["segment_days"].values
        
        label = f"Parliament {parl_num} ({parl_year})"
        x_labels.append(label)
        
        if len(tenures) > 0:
            fig.add_trace(go.Box(
                y=tenures,
                name=label,
                marker=dict(color='lightblue', outliercolor='red'),
                boxmean=True,
                hovertemplate='<b>%{fullData.name}</b><br>Tenure: %{y} days<extra></extra>'
            ))
    
    # Add media era markers
    for d_str, label in MEDIA_MARKERS:
        dt = pd.to_datetime(d_str)
        matching = parls_filtered[
            (parls_filtered["parliament_start_date"] <= dt) & 
            (parls_filtered["parliament_end_date"] >= dt)
        ]
        if not matching.empty:
            parl_year = matching.iloc[0]["parliament_start_date"].year
            parl_num = int(matching.iloc[0]["parliament_number"])
            marker_label = f"Parliament {parl_num} ({parl_year})"
            if marker_label in x_labels:
                idx = x_labels.index(marker_label)
                fig.add_annotation(
                    x=idx,
                    y=1.0,
                    yref='paper',
                    text=label,
                    showarrow=False,
                    font=dict(size=10, style='italic'),
                    bgcolor='wheat',
                    opacity=0.8,
                    borderpad=4,
                    yanchor='top'
                )
    
    fig.update_layout(
        title=dict(
            text=f"Senior Cabinet Tenure Distribution by Parliament ({MIN_YEAR} onwards)<br><sub>Tenure duration in days</sub>",
            font=dict(size=18)
        ),
        xaxis=dict(title="Parliament Number (Year)", tickangle=45),
        yaxis=dict(title="Tenure Duration (days)"),
        height=600,
        showlegend=False,
        hovermode='x unified'
    )
    
    return fig


def generate_html_report(summary: pd.DataFrame, seg: pd.DataFrame, parls: pd.DataFrame) -> Path:
    """Generate combined HTML report with both charts."""
    
    # Create both charts
    churn_fig = create_churn_chart(summary)
    tenure_fig = create_tenure_boxplot(seg, parls)
    
    # Generate statistics summary
    stats_html = f"""
    <div style="background-color: #f0f0f0; padding: 20px; margin: 20px 0; border-radius: 8px;">
        <h2>Summary Statistics ({MIN_YEAR} onwards)</h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
            <div>
                <h3>Coverage</h3>
                <p><strong>Parliaments analyzed:</strong> {len(parls[parls["parliament_number"] != 48])}</p>
                <p><strong>Senior posts tracked:</strong> {len(seg)}</p>
                <p><strong>Unique individuals:</strong> {seg['person_id'].nunique()}</p>
            </div>
            <div>
                <h3>Tenure Statistics</h3>
                <p><strong>Mean tenure:</strong> {seg['segment_days'].mean():.0f} days ({seg['segment_days'].mean()/30:.1f} months)</p>
                <p><strong>Median tenure:</strong> {seg['segment_days'].median():.0f} days ({seg['segment_days'].median()/30:.1f} months)</p>
                <p><strong>Range:</strong> {seg['segment_days'].min()} - {seg['segment_days'].max()} days</p>
            </div>
            <div>
                <h3>Churn Rates</h3>
                <p><strong>Mean churn:</strong> {summary[summary['parliament_number'] != 48]['appointments_per_year'].mean():.1f} per year</p>
                <p><strong>Median churn:</strong> {summary[summary['parliament_number'] != 48]['appointments_per_year'].median():.1f} per year</p>
                <p><strong>Peak churn:</strong> Parliament {int(summary[summary['parliament_number'] != 48].nlargest(1, 'appointments_per_year').iloc[0]['parliament_number'])} ({summary[summary['parliament_number'] != 48]['appointments_per_year'].max():.1f} per year)</p>
            </div>
        </div>
    </div>
    """
    
    # Get HTML for both charts
    churn_html = churn_fig.to_html(include_plotlyjs='cdn', div_id='churn-chart')
    tenure_html = tenure_fig.to_html(include_plotlyjs=False, div_id='tenure-chart')
    
    # Combine into full HTML
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>UK Cabinet Churn & Tenure Report</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
                background-color: #ffffff;
            }}
            h1 {{
                color: #333;
                border-bottom: 3px solid #0087DC;
                padding-bottom: 10px;
            }}
            .metadata {{
                color: #666;
                font-size: 14px;
                margin-bottom: 30px;
            }}
            .chart-container {{
                margin: 30px 0;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                background-color: #fafafa;
            }}
        </style>
    </head>
    <body>
        <h1>UK Senior Cabinet Churn & Tenure Analysis</h1>
        <div class="metadata">
            <p><strong>Generated:</strong> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Data source:</strong> UK Parliament API via cabinet_ministers.csv</p>
            <p><strong>Analysis period:</strong> {MIN_YEAR} onwards</p>
            <p><strong>Methodology:</strong> Senior Cabinet posts identified via classification rules (Secretaries of State, PM, Chancellor, etc.) in the House of Commons</p>
        </div>
        
        {stats_html}
        
        <div class="chart-container">
            <h2>1. Cabinet Churn Rate by Parliament</h2>
            <p>Shows the rate of turnover in senior Cabinet positions, normalized per year. Higher values indicate more frequent changes in senior posts.</p>
            {churn_html}
        </div>
        
        <div class="chart-container">
            <h2>2. Tenure Duration Distribution by Parliament</h2>
            <p>Box plots showing the distribution of how long individuals held senior Cabinet posts within each Parliament. The box shows the interquartile range (25th-75th percentile), the line shows the median, and red dots are outliers.</p>
            {tenure_html}
        </div>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px;">
            <p><strong>Notes:</strong></p>
            <ul>
                <li>Parliament 48 (2010-05-06 to 2010-05-18, 12 days) excluded as an outlier from visualizations</li>
                <li>Media era markers indicate approximate technological shifts affecting political communication</li>
                <li>Tenure calculations are per-parliament segments; individuals may serve across multiple parliaments</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    # Save to file
    output_path = CHARTS_OUTPUT_DIR / "cabinet_churn_report.html"
    output_path.write_text(full_html, encoding='utf-8')
    
    return output_path


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

    summary = build_summary(seg, parls)
    print(f"\nSummary rows: {len(summary)}")

    output_path = generate_html_report(summary, seg, parls)

    print(f"\nWrote: {output_path}")
    print(f"\nOpen the report in your browser to view the interactive charts.")


if __name__ == "__main__":
    main()
