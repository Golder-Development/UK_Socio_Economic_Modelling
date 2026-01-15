"""
Analyze individual cabinet members' tenure patterns to identify:
1. Members with exceptionally long single tenures
2. Members with multiple short spells (sacrificial pawns)
3. Career patterns and re-appointments

Outputs:
- generated_charts/individual_cabinet_analysis.html (interactive report)
- generated_charts/cabinet_members_tenure_profile.csv (detailed individual stats)
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple
import json

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys

# Import classification logic
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
CHARTS_OUTPUT_DIR = Path("generated_charts")
CHARTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PARLIAMENTS_CACHE = OUTPUT_DIR / "parliaments_periods.json"


def load_cabinet_ministers(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    df["end_date"] = df["end_date"].fillna(pd.Timestamp.today().normalize())
    df["person_name"] = (df["given_name"].fillna("") + " " + df["family_name"].fillna("")).str.strip()
    
    # Filter out most recent parliament (not yet complete) - dynamically exclude latest year
    # Find the maximum start_date year and exclude that year
    max_year = df["start_date"].dt.year.max()
    df = df[df["start_date"].dt.year < max_year].copy()
    
    return df


def filter_senior_cabinet(df: pd.DataFrame) -> pd.DataFrame:
    """Filter for senior Cabinet posts (Commons only), excluding Prime Ministers."""
    house_series = df["member_house"].astype(str).str.lower()
    in_commons = house_series == "commons"
    
    classifications = df["post"].apply(lambda p: classify_post(p, {}))
    is_senior = classifications.apply(lambda c: c.is_senior)
    
    # Exclude Prime Ministers as they are outliers
    post_series = df["post"].astype(str).str.lower()
    not_pm = ~post_series.str.contains("prime minister", na=False)
    
    mask = is_senior & in_commons & not_pm
    result = df.loc[mask].copy()
    print(f"Cabinet ministers total: {len(df)}")
    print(f"Senior Cabinet posts (Commons) filtered: {len(result)}")
    return result


def load_parliament_periods() -> pd.DataFrame:
    """Load cached parliament periods."""
    if PARLIAMENTS_CACHE.exists():
        with open(PARLIAMENTS_CACHE, "r") as f:
            data = json.load(f)
        parls = pd.DataFrame(data)
        parls["parliament_start_date"] = pd.to_datetime(parls["parliament_start_date"])
        parls["parliament_end_date"] = pd.to_datetime(parls["parliament_end_date"])
        return parls
    else:
        raise FileNotFoundError(f"Parliament cache not found at {PARLIAMENTS_CACHE}")


def analyze_individual_tenure(df: pd.DataFrame, min_year: int = 1970) -> pd.DataFrame:
    """
    Analyze tenure patterns for each individual cabinet member.
    
    Returns one row per unique person with metrics:
    - Total tenure (days)
    - Average tenure per spell (days)
    - Number of spells
    - Longest single spell
    - Shortest spell
    - Spell variance (indicates sacrifice player pattern)
    - Years active
    - Different posts held
    - Party affiliation
    """
    # Filter by date
    df = df[df["start_date"] >= pd.Timestamp(f"{min_year}-01-01")].copy()
    
    individuals = []
    
    for person_id, group in df.groupby("person_id"):
        person_name = group["person_name"].iloc[0]
        party = group["party"].mode()[0] if len(group["party"].mode()) > 0 else "Unknown"
        
        # Calculate tenure for each spell
        group["tenure_days"] = (group["end_date"] - group["start_date"]).dt.days + 1
        
        # Basic stats
        total_tenure = group["tenure_days"].sum()
        num_spells = len(group)
        longest_spell = group["tenure_days"].max()
        shortest_spell = group["tenure_days"].min()
        mean_tenure = group["tenure_days"].mean()
        median_tenure = group["tenure_days"].median()
        std_tenure = group["tenure_days"].std()
        
        # Spell consistency: coefficient of variation (std/mean)
        # High CV = inconsistent spell lengths (sacrificial pawn pattern)
        # Low CV = consistent spell lengths (steady senior figure)
        cv_tenure = std_tenure / mean_tenure if mean_tenure > 0 else 0
        cv_tenure = 0 if pd.isna(cv_tenure) else cv_tenure
        
        # Career span
        first_spell_start = group["start_date"].min()
        last_spell_end = group["end_date"].max()
        career_span_days = (last_spell_end - first_spell_start).days + 1
        years_active = career_span_days / 365.25
        
        # Unique posts held
        posts = group["post"].unique()
        num_posts = len(posts)
        
        # Early career, mid-career, late career
        today = pd.Timestamp.today()
        is_current = (group["end_date"] >= today).any()
        
        individuals.append({
            "person_id": person_id,
            "person_name": person_name,
            "party": party,
            "total_tenure_days": total_tenure,
            "total_tenure_years": total_tenure / 365.25,
            "avg_tenure_days": mean_tenure,
            "avg_tenure_years": mean_tenure / 365.25,
            "num_spells": num_spells,
            "longest_spell_days": longest_spell,
            "longest_spell_years": longest_spell / 365.25,
            "shortest_spell_days": shortest_spell,
            "shortest_spell_years": shortest_spell / 365.25,
            "mean_tenure_days": mean_tenure,
            "median_tenure_days": median_tenure,
            "std_tenure_days": std_tenure,
            "cv_tenure": cv_tenure,  # Coefficient of variation - high = varied spell lengths
            "first_appointment": first_spell_start,
            "last_appointment": last_spell_end,
            "career_span_years": years_active,
            "num_posts": num_posts,
            "posts": ", ".join(posts[:3]) + ("..." if len(posts) > 3 else ""),
            "is_current": is_current,
        })
    
    result = pd.DataFrame(individuals)
    return result.sort_values("total_tenure_days", ascending=False).reset_index(drop=True)


def identify_patterns(individuals: pd.DataFrame) -> dict:
    """
    Identify cabinet members fitting specific patterns:
    1. Long-tenure stalwarts (high total tenure, few spells)
    2. Sacrificial pawns (multiple short spells, high CV)
    3. One-hit wonders (single long spell, never returned)
    """
    patterns = {
        "long_tenure_stalwarts": [],
        "sacrificial_pawns": [],
        "one_hit_wonders": [],
        "rotating_posts": [],
    }
    
    # Long-tenure stalwarts: top 10% by tenure, low CV (consistency)
    tenure_75th = individuals["total_tenure_days"].quantile(0.75)
    cv_25th = individuals["cv_tenure"].quantile(0.25)
    stalwarts = individuals[
        (individuals["total_tenure_days"] >= tenure_75th) & 
        (individuals["cv_tenure"] <= cv_25th) &
        (individuals["num_spells"] <= 3)
    ].sort_values("total_tenure_days", ascending=False)
    patterns["long_tenure_stalwarts"] = stalwarts.to_dict("records")[:10]
    
    # Sacrificial pawns: multiple spells (3+) with high variance and moderate total tenure
    multiple_spells = individuals[individuals["num_spells"] >= 3]
    cv_75th = multiple_spells["cv_tenure"].quantile(0.75)
    pawns = individuals[
        (individuals["num_spells"] >= 4) &
        (individuals["cv_tenure"] >= cv_75th) &
        (individuals["total_tenure_days"] > 100)
    ].sort_values("cv_tenure", ascending=False)
    patterns["sacrificial_pawns"] = pawns.to_dict("records")[:10]
    
    # One-hit wonders: exactly one spell with significant duration (1+ year)
    one_hit = individuals[
        (individuals["num_spells"] == 1) &
        (individuals["longest_spell_days"] > 365)
    ].sort_values("longest_spell_days", ascending=False)
    patterns["one_hit_wonders"] = one_hit.to_dict("records")[:10]
    
    # Single short tenures: exactly one spell with short duration (less than 1 year)
    # These are ministers who had a single brief appointment and never returned
    single_short = individuals[
        (individuals["num_spells"] == 1) &
        (individuals["longest_spell_days"] <= 365) &
        (individuals["longest_spell_days"] >= 30)  # At least 30 days
    ].sort_values("longest_spell_days", ascending=False)
    patterns["single_short_tenures"] = single_short.to_dict("records")[:15]
    
    # Rotating posts: held 4+ different posts
    rotating = individuals[
        individuals["num_posts"] >= 4
    ].sort_values("num_posts", ascending=False)
    patterns["rotating_posts"] = rotating.to_dict("records")[:10]
    
    return patterns


def create_scatter_plot(individuals: pd.DataFrame) -> go.Figure:
    """Create scatter plot: average tenure vs num_spells, colored by party."""
    fig = go.Figure()
    
    # Handle NaN values
    individuals_copy = individuals.copy()
    individuals_copy["cv_tenure"] = individuals_copy["cv_tenure"].fillna(0)
    individuals_copy["party"] = individuals_copy["party"].fillna("Unknown")
    
    # Define party colors (UK politics standard)
    party_colors = {
        "Labour": "#E4003B",
        "Conservative": "#0087DC",
        "Liberal Democrat": "#FAA61A",
        "Independent": "#999999",
        "Unknown": "#CCCCCC"
    }
    
    # Identify categories by position
    is_stalwart = (individuals_copy["cv_tenure"] <= individuals_copy["cv_tenure"].quantile(0.25)) & \
                  (individuals_copy["num_spells"] <= 3) & \
                  (individuals_copy["avg_tenure_days"] >= individuals_copy["avg_tenure_days"].quantile(0.75))
    
    is_pawn = (individuals_copy["num_spells"] >= 4) & \
              (individuals_copy["cv_tenure"] >= individuals_copy["cv_tenure"].quantile(0.75))
    
    is_one_hit = (individuals_copy["num_spells"] == 1) & \
                 (individuals_copy["longest_spell_days"] > 365)
    
    individuals_copy["category"] = np.where(is_stalwart, "Stalwart",
            np.where(is_pawn, "Sacrificial Pawn",
            np.where(is_one_hit, "One-Hit Wonder", "Other")))
    
    # Add traces for each party
    for party in sorted(individuals_copy["party"].unique()):
        mask = individuals_copy["party"] == party
        subset = individuals_copy[mask]
        
        color = party_colors.get(party, "#999999")
        
        # Ensure no NaN in size calculation
        sizes = np.where(np.isnan(subset["cv_tenure"]), 5, subset["cv_tenure"] * 30 + 5)
        sizes = np.maximum(sizes, 5)  # Ensure minimum size of 5
        
        # Create hover text with category information
        hover_text = []
        for _, row in subset.iterrows():
            hover_text.append(f"<b>{row['person_name']}</b><br>" +
                            f"Party: {row['party']}<br>" +
                            f"Category: {row['category']}")
        
        fig.add_trace(go.Scatter(
            x=subset["num_spells"],
            y=subset["avg_tenure_days"],
            mode="markers+text",
            name=party,
            text=subset["person_name"],
            textposition="top center",
            textfont=dict(size=8),
            marker=dict(
                size=sizes,
                color=color,
                opacity=0.7,
                line=dict(width=1, color="darkgray")
            ),
            hovertext=hover_text,
            hoverinfo="text",
            customdata=subset["cv_tenure"]
        ))
    
    fig.update_layout(
        title="Cabinet Member Career Patterns by Party<br><sub>Position identifies pattern: Bottom-left=Stalwarts | Right=Sacrificial Pawns | Bubble size=Spell variance</sub>",
        xaxis=dict(title="Number of Separate Spells"),
        yaxis=dict(title="Average Tenure Per Spell (days)"),
        hovermode="closest",
        height=700,
        width=1200,
        font=dict(size=11)
    )
    
    return fig


def create_top_members_chart(individuals: pd.DataFrame) -> go.Figure:
    """Create charts for top long-tenure and top sacrificial pawn members by average tenure."""
    # Top 10 by average tenure
    top_long = individuals.nlargest(10, "avg_tenure_days")
    
    # Define party colors
    party_colors = {
        "Labour": "#E4003B",
        "Conservative": "#0087DC",
        "Liberal Democrat": "#FAA61A",
        "Independent": "#999999",
        "Unknown": "#CCCCCC"
    }
    
    colors = [party_colors.get(party, "#999999") for party in top_long["party"]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=top_long["person_name"],
        y=top_long["avg_tenure_days"],
        name="Average Tenure",
        marker_color=colors,
        text=[f"{x/365.25:.1f} yrs<br>({int(y)} spells)" for x, y in zip(top_long["avg_tenure_days"], top_long["num_spells"])],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Average tenure: %{y:.0f} days<extra></extra>"
    ))
    
    fig.update_layout(
        title="Top 10 Cabinet Members by Average Tenure Per Spell",
        xaxis_title="Cabinet Member",
        yaxis_title="Average Tenure (days)",
        xaxis=dict(tickangle=45),
        height=500,
        showlegend=False
    )
    
    return fig


def create_spell_distribution_chart(df: pd.DataFrame, individuals: pd.DataFrame) -> go.Figure:
    """Create detailed view of spells for key individuals."""
    # Get top long-tenure members and top sacrificial pawns
    top_long = individuals.nlargest(5, "total_tenure_days")["person_id"].tolist()
    top_pawns = individuals.nlargest(5, "cv_tenure")[
        individuals.nlargest(5, "cv_tenure")["num_spells"] >= 4
    ]["person_id"].tolist()
    
    key_people = top_long + top_pawns[:3]
    
    fig = go.Figure()
    
    for person_id in key_people:
        person_spells = df[df["person_id"] == person_id].copy()
        person_name = person_spells["person_name"].iloc[0]
        
        person_spells = person_spells.sort_values("start_date")
        person_spells["tenure_days"] = (person_spells["end_date"] - person_spells["start_date"]).dt.days + 1
        person_spells["spell_num"] = range(1, len(person_spells) + 1)
        
        fig.add_trace(go.Bar(
            x=[f"Spell {x}" for x in person_spells["spell_num"]],
            y=person_spells["tenure_days"],
            name=person_name,
            text=[f"{x/365.25:.1f} yrs" for x in person_spells["tenure_days"]],
            textposition="outside",
            hovertemplate="<b>" + person_name + "</b><br>%{x}<br>%{y:.0f} days<extra></extra>"
        ))
    
    fig.update_layout(
        title="Spell Duration Patterns - Key Cabinet Members",
        xaxis_title="Spell Sequence",
        yaxis_title="Spell Duration (days)",
        barmode="group",
        height=500,
        hovermode="x unified"
    )
    
    return fig


def generate_html_report(individuals: pd.DataFrame, patterns: dict, 
                        scatter_fig: go.Figure, tenure_fig: go.Figure,
                        spells_fig: go.Figure) -> Path:
    """Generate comprehensive HTML report."""
    
    scatter_html = scatter_fig.to_html(include_plotlyjs='cdn', div_id='scatter-chart')
    tenure_html = tenure_fig.to_html(include_plotlyjs=False, div_id='tenure-chart')
    spells_html = spells_fig.to_html(include_plotlyjs=False, div_id='spells-chart')
    
    # Build pattern HTML sections
    def make_table(records: List[dict]) -> str:
        if not records:
            return "<p><em>No members in this category.</em></p>"
        
        cols = ["person_name", "party", "avg_tenure_years", "num_spells", "cv_tenure", "posts"]
        html = "<table style='border-collapse: collapse; width: 100%;'>"
        html += "<tr style='background-color: #f0f0f0; border-bottom: 2px solid #333;'>"
        headers = ["Name", "Party", "Avg Tenure (yrs)", "Num Spells", "Consistency (CV)", "Posts"]
        for h in headers:
            html += f"<th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>{h}</th>"
        html += "</tr>"
        
        # Define party colors
        party_color_map = {
            "Labour": "#E4003B",
            "Conservative": "#0087DC",
            "Liberal Democrat": "#FAA61A",
            "Independent": "#999999",
            "Unknown": "#CCCCCC"
        }
        
        for rec in records[:10]:
            party_color = party_color_map.get(rec.get('party', 'Unknown'), '#CCCCCC')
            html += "<tr style='border-bottom: 1px solid #ddd;'>"
            html += f"<td style='border: 1px solid #ddd; padding: 8px;'><strong>{rec['person_name']}</strong></td>"
            html += f"<td style='border: 1px solid #ddd; padding: 8px; color: {party_color}; font-weight: bold;'>{rec.get('party', 'Unknown')}</td>"
            html += f"<td style='border: 1px solid #ddd; padding: 8px;'>{rec['avg_tenure_years']:.1f}</td>"
            html += f"<td style='border: 1px solid #ddd; padding: 8px;'>{rec['num_spells']}</td>"
            html += f"<td style='border: 1px solid #ddd; padding: 8px;'>{rec['cv_tenure']:.2f}</td>"
            html += f"<td style='border: 1px solid #ddd; padding: 8px; font-size: 0.85em;'>{rec['posts']}</td>"
            html += "</tr>"
        
        html += "</table>"
        return html
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Individual Cabinet Member Tenure Analysis</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #fafafa;
                color: #333;
            }}
            .header {{
                background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
                color: white;
                padding: 30px;
                border-radius: 8px;
                margin-bottom: 30px;
            }}
            .header h1 {{
                margin: 0 0 10px 0;
                font-size: 2.5em;
            }}
            .header p {{
                margin: 0;
                font-size: 1.1em;
                opacity: 0.9;
            }}
            .section {{
                background: white;
                padding: 25px;
                margin: 20px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .section h2 {{
                color: #1a237e;
                border-bottom: 3px solid #283593;
                padding-bottom: 10px;
                margin-top: 0;
            }}
            .section h3 {{
                color: #283593;
                margin-top: 20px;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }}
            .stat-box {{
                background: #f5f5f5;
                padding: 15px;
                border-left: 4px solid #283593;
                border-radius: 4px;
            }}
            .stat-box h4 {{
                margin: 0 0 5px 0;
                color: #666;
                font-size: 0.9em;
                text-transform: uppercase;
            }}
            .stat-box .value {{
                font-size: 1.8em;
                font-weight: bold;
                color: #1a237e;
            }}
            .chart-container {{
                margin: 20px 0;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 10px;
                text-align: left;
            }}
            th {{
                background-color: #f0f0f0;
                font-weight: bold;
                border-bottom: 2px solid #333;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            .category-label {{
                display: inline-block;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 0.85em;
                font-weight: bold;
                margin-right: 5px;
            }}
            .stalwart {{
                background-color: #c8e6c9;
                color: #1b5e20;
            }}
            .pawn {{
                background-color: #ffcdd2;
                color: #b71c1c;
            }}
            .one-hit {{
                background-color: #bbdefb;
                color: #0d47a1;
            }}
            .insight {{
                background-color: #fff9c4;
                border-left: 4px solid #f57f17;
                padding: 15px;
                margin: 15px 0;
                border-radius: 4px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Individual Cabinet Member Tenure Analysis</h1>
            <p>Identifying patterns of long tenures, sacrificial pawns, and career trajectories</p>
            <p style="font-size: 0.95em; opacity: 0.8;">Senior Cabinet Members (Commons) from {MIN_YEAR} onwards</p>
        </div>
        
        <div class="section">
            <h2>Overview Statistics</h2>
            <div class="stats-grid">
                <div class="stat-box">
                    <h4>Total Individuals</h4>
                    <div class="value">{len(individuals)}</div>
                </div>
                <div class="stat-box">
                    <h4>Total Spells</h4>
                    <div class="value">{individuals['num_spells'].sum():.0f}</div>
                </div>
                <div class="stat-box">
                    <h4>Avg Tenure per Spell (years)</h4>
                    <div class="value">{individuals['avg_tenure_years'].mean():.1f}</div>
                </div>
                <div class="stat-box">
                    <h4>Longest Avg Spell (years)</h4>
                    <div class="value">{individuals['avg_tenure_years'].max():.1f}</div>
                </div>
                <div class="stat-box">
                    <h4>Avg Spells per Person</h4>
                    <div class="value">{individuals['num_spells'].mean():.1f}</div>
                </div>
                <div class="stat-box">
                    <h4>Max Spells</h4>
                    <div class="value">{individuals['num_spells'].max():.0f}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Interactive Visualizations</h2>
            <h3>Career Pattern Scatter Plot</h3>
            <p>Each bubble represents one cabinet member, colored by political party. Horizontal position (x-axis) shows number of separate spells; vertical position (y-axis) shows average tenure per spell. Bubble size indicates spell length consistency (larger = more varied spell lengths). Position patterns: <strong>bottom-left = stalwarts</strong> (few spells, long average tenure), <strong>right side = sacrificial pawns</strong> (many spells, varied lengths).</p>
            <div class="chart-container">
                {scatter_html}
            </div>
            <div class="insight">
                <strong>Party Color Legend:</strong><br>
                <span style="color: #0087DC; font-weight: bold;">Conservative (Blue)</span> | 
                <span style="color: #E4003B; font-weight: bold;">Labour (Red)</span> | 
                <span style="color: #FAA61A; font-weight: bold;">Liberal Democrat (Orange)</span> | 
                <span style="color: #999999; font-weight: bold;">Independent/Unknown (Gray)</span>
            </div>
            
            <h3>Top Tenure Holders</h3>
            <div class="chart-container">
                {tenure_html}
            </div>
            
            <h3>Spell Duration Patterns</h3>
            <p>Detailed breakdown of appointment spells for key individuals, showing how tenure is distributed across separate appointments.</p>
            <div class="chart-container">
                {spells_html}
            </div>
        </div>
        
        <div class="section">
            <h2><span class="category-label stalwart">Stalwarts</span> - Long-Tenure Steady Performers</h2>
            <p>Cabinet members with significant total tenure, low variability in spell length, and typically few separate appointments. These are the steady hands who maintained consistent roles across years or parliaments.</p>
            {make_table(patterns['long_tenure_stalwarts'])}
        </div>
        
        <div class="section">
            <h2><span class="category-label pawn">Sacrificial Pawns</span> - Multiple Short Spells</h2>
            <p>Members with 4+ separate spells and high variance in spell duration. These individuals were frequently appointed and removed, often suggesting they held difficult or politically sensitive positions.</p>
            {make_table(patterns['sacrificial_pawns'])}
        </div>
        
        <div class="section">
            <h2><span class="category-label one-hit">One-Hit Wonders</span> - Single Long Spells</h2>
            <p>Cabinet members who held a significant role for an extended period but only served once. They either specialized in their role or left frontbench politics after their tenure.</p>
            {make_table(patterns['one_hit_wonders'])}
        </div>
        
        <div class="section">
            <h2><span class="category-label pawn">Single Short Tenures</span> - Brief One-Time Appointments</h2>
            <p>Cabinet members appointed to a single role for a brief period (less than one year), who were never recalled to Cabinet. These may represent specialized crisis managers, appointment mistakes, or ill-fated experimental placements.</p>
            <div style="background-color: #fffacd; border-left: 4px solid #ff6347; padding: 15px; margin: 15px 0; border-radius: 4px;">
                <strong>What This Means:</strong> These ministers held Cabinet rank for a short spell and never returned. The brief tenure could indicate: (a) they were brought in for a specific task then released, (b) the role proved too difficult or political, (c) they proved unsuitable for the position, or (d) the department/role was restructured.
            </div>
            {make_table(patterns['single_short_tenures'])}
        </div>
        
        <div class="section">
            <h2>Portfolio Rotators</h2>
            <p>Cabinet members who held 4 or more different posts throughout their careers, suggesting generalists or political survivors.</p>
            {make_table(patterns['rotating_posts'])}
        </div>
        
        <div class="section">
            <h2>Key Insights</h2>
            <ul>
                <li><strong>Tenure variation:</strong> Average cabinet member tenure is {individuals['total_tenure_years'].mean():.1f} years, but ranges from {individuals['total_tenure_years'].min():.1f} to {individuals['total_tenure_years'].max():.1f} years.</li>
                <li><strong>Appointment patterns:</strong> Most members ({(individuals['num_spells'] == 1).sum()} out of {len(individuals)}) serve in a single continuous or non-overlapping period. Those with {(individuals['num_spells'] >= 4).sum()} or more spells represent the sacrificial pawn pattern.</li>
                <li><strong>Spell consistency:</strong> Members with CV < 0.5 show consistent spell lengths (stalwarts), while those with CV > 1.5 show highly varied patterns (pawns).</li>
                <li><strong>Post rotation:</strong> {(individuals['num_posts'] >= 4).sum()} members held 4+ different posts, indicating career mobility within Cabinet.</li>
            </ul>
        </div>
        
    </body>
    </html>
    """
    
    out = CHARTS_OUTPUT_DIR / "individual_cabinet_analysis.html"
    with open(out, "w") as f:
        f.write(html_content)
    
    return out


def main() -> None:
    print(f"Loading cabinet ministers from: {INPUT_CSV}")
    df = load_cabinet_ministers(INPUT_CSV)
    print(f"Loaded {len(df)} total records\n")
    
    # Filter for senior cabinet
    cabinet = filter_senior_cabinet(df)
    
    # Analyze individual tenure patterns
    print("Analyzing individual tenure patterns...")
    individuals = analyze_individual_tenure(cabinet, MIN_YEAR)
    print(f"Analyzed {len(individuals)} unique individuals\n")
    
    # Identify patterns
    print("Identifying career patterns...")
    patterns = identify_patterns(individuals)
    print(f"  - Stalwarts: {len(patterns['long_tenure_stalwarts'])}")
    print(f"  - Sacrificial pawns: {len(patterns['sacrificial_pawns'])}")
    print(f"  - One-hit wonders: {len(patterns['one_hit_wonders'])}")
    print(f"  - Single short tenures: {len(patterns['single_short_tenures'])}")
    print(f"  - Portfolio rotators: {len(patterns['rotating_posts'])}\n")
    
    # Create visualizations
    print("Creating visualizations...")
    scatter_fig = create_scatter_plot(individuals)
    tenure_fig = create_top_members_chart(individuals)
    spells_fig = create_spell_distribution_chart(cabinet, individuals)
    
    # Generate report
    print("Generating HTML report...")
    report_path = generate_html_report(individuals, patterns, scatter_fig, tenure_fig, spells_fig)
    
    # Save detailed CSV
    print("Saving detailed CSV...")
    csv_path = CHARTS_OUTPUT_DIR / "cabinet_members_tenure_profile.csv"
    individuals.to_csv(csv_path, index=False)
    
    print(f"\n✓ Generated: {report_path}")
    print(f"✓ Generated: {csv_path}")
    print("\n" + "="*70)
    print("TOP STALWARTS (Long-tenure steady performers):")
    print("="*70)
    for i, p in enumerate(patterns['long_tenure_stalwarts'][:5], 1):
        print(f"{i}. {p['person_name']}: {p['total_tenure_years']:.1f} years over {p['num_spells']} spell(s), "
              f"CV={p['cv_tenure']:.2f}")
    
    print("\n" + "="*70)
    print("TOP SACRIFICIAL PAWNS (Multiple short spells):")
    print("="*70)
    for i, p in enumerate(patterns['sacrificial_pawns'][:5], 1):
        print(f"{i}. {p['person_name']}: {p['num_spells']} spells over {p['total_tenure_years']:.1f} years, "
              f"CV={p['cv_tenure']:.2f} (high variance = inconsistent tenure)")


if __name__ == "__main__":
    main()
