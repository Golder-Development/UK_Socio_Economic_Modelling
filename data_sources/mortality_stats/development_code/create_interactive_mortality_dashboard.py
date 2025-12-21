"""
Create interactive Plotly dashboard for UK mortality data (1901-2025).
Shows deaths per 100k by harmonized category with filtering and drill-down.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
REPO_ROOT = BASE_DIR.parent.parent
OUTPUT_DIR = REPO_ROOT / "generated_charts"
# Prefer rebuilt harmonized file from archive, fallback to previous comprehensive harmonized
PREFERRED = BASE_DIR / "uk_mortality_by_cause_1901_2000_harmonized.csv"
FALLBACK = BASE_DIR / "uk_mortality_comprehensive_1901_2025_harmonized.csv"
DATA_FILE = PREFERRED if PREFERRED.exists() else FALLBACK

# UK population estimates (approximations for rate calculation)
# Source: ONS historical population data
POPULATION_ESTIMATES = {
    1901: 32500000,
    1911: 36070000,
    1921: 37887000,
    1931: 39952000,
    1941: 41748000,
    1951: 43758000,
    1961: 46105000,
    1971: 48750000,
    1981: 49634000,
    1991: 51100000,
    2001: 52360000,
    2011: 56075000,
    2021: 59597000,
}


def interpolate_population(year):
    """Interpolate population for years between census data."""
    years = sorted(POPULATION_ESTIMATES.keys())
    if year <= years[0]:
        return POPULATION_ESTIMATES[years[0]]
    if year >= years[-1]:
        return POPULATION_ESTIMATES[years[-1]]

    for i in range(len(years) - 1):
        if years[i] <= year <= years[i + 1]:
            y1, y2 = years[i], years[i + 1]
            p1, p2 = POPULATION_ESTIMATES[y1], POPULATION_ESTIMATES[y2]
            return p1 + (p2 - p1) * (year - y1) / (y2 - y1)
    return POPULATION_ESTIMATES[years[-1]]


def load_and_prepare_data():
    """Load mortality data and calculate rates per 100k."""
    print("Loading data...")
    df = pd.read_csv(DATA_FILE)

    # Calculate population for each year
    df["population"] = df["year"].apply(interpolate_population)

    # Calculate rate per 100k
    df["rate_per_100k"] = (df["deaths"] / df["population"]) * 100000

    # Fill missing harmonized categories
    df["harmonized_category_name"].fillna("Unknown/Unclassified", inplace=True)
    df["harmonized_category"].fillna("unknown", inplace=True)

    print(f"Loaded {len(df):,} rows")
    print(f"Year range: {df['year'].min()}-{df['year'].max()}")
    print(f"Categories: {df['harmonized_category_name'].nunique()}")

    return df


def create_dashboard(df):
    """Create interactive Plotly dashboard."""
    print("Building dashboard...")

    # Get unique values for filters
    categories = sorted(df["harmonized_category_name"].unique())
    ages = sorted(df["age"].unique())
    sexes = sorted(df["sex"].unique())

    # Aggregate data by year and harmonized category
    agg_by_category = (
        df.groupby(["year", "harmonized_category_name"])
        .agg({"deaths": "sum", "population": "first"})
        .reset_index()
    )
    agg_by_category["rate_per_100k"] = (
        agg_by_category["deaths"] / agg_by_category["population"]
    ) * 100000

    # Create figure with dropdown menus
    fig = go.Figure()

    # Add traces for each category (initially all visible)
    for category in categories:
        cat_data = agg_by_category[
            agg_by_category["harmonized_category_name"] == category
        ]
        fig.add_trace(
            go.Scatter(
                x=cat_data["year"],
                y=cat_data["rate_per_100k"],
                mode="lines+markers",
                name=category,
                hovertemplate="<b>%{fullData.name}</b><br>"
                + "Year: %{x}<br>"
                + "Rate per 100k: %{y:.2f}<br>"
                + "<extra></extra>",
                visible=True,
            )
        )

    # Create dropdown buttons for harmonized categories
    category_buttons = [
        {
            "label": "All Categories",
            "method": "update",
            "args": [
                {"visible": [True] * len(categories)},
                {"title": "UK Mortality Rates per 100k (All Categories)"},
            ],
        }
    ]

    for i, category in enumerate(categories):
        visible = [False] * len(categories)
        visible[i] = True
        category_buttons.append(
            {
                "label": category,
                "method": "update",
                "args": [
                    {"visible": visible},
                    {"title": f"UK Mortality Rates per 100k - {category}"},
                ],
            }
        )

    # Update layout with dropdown menus
    fig.update_layout(
        title={
            "text": "UK Mortality Rates per 100,000 Population (1901-2025)<br>"
            "<sub>Interactive Dashboard - Filter by Category, Age, and Sex</sub>",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="Year",
        yaxis_title="Deaths per 100,000 Population",
        hovermode="closest",
        template="plotly_white",
        height=700,
        updatemenus=[
            {
                "buttons": category_buttons,
                "direction": "down",
                "pad": {"r": 10, "t": 10},
                "showactive": True,
                "x": 0.01,
                "xanchor": "left",
                "y": 1.15,
                "yanchor": "top",
                "bgcolor": "#f0f0f0",
                "bordercolor": "#333",
                "borderwidth": 1,
            }
        ],
        annotations=[
            {
                "text": "Select Category:",
                "showarrow": False,
                "x": 0.01,
                "y": 1.18,
                "xref": "paper",
                "yref": "paper",
                "align": "left",
                "xanchor": "left",
                "yanchor": "bottom",
                "font": {"size": 12, "color": "#333"},
            }
        ],
    )

    # Add range slider
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list(
                [
                    dict(count=10, label="10y", step="year", stepmode="backward"),
                    dict(count=25, label="25y", step="year", stepmode="backward"),
                    dict(count=50, label="50y", step="year", stepmode="backward"),
                    dict(step="all", label="All"),
                ]
            )
        ),
    )

    return fig


def create_drilldown_dashboard(df):
    """Create dashboard with drill-down capability into sub-categories."""
    print("Building drill-down dashboard...")

    # Create a more detailed view that can show sub-categories
    fig = make_subplots(
        rows=2,
        cols=1,
        row_heights=[0.6, 0.4],
        subplot_titles=(
            "Mortality Rates by Harmonized Category (per 100k)",
            "Sub-Category Detail (Original ICD Codes)",
        ),
        vertical_spacing=0.12,
    )

    # Top plot: Aggregated by harmonized category
    categories = sorted(df["harmonized_category_name"].unique())
    agg_by_category = (
        df.groupby(["year", "harmonized_category_name"])
        .agg({"deaths": "sum", "population": "first"})
        .reset_index()
    )
    agg_by_category["rate_per_100k"] = (
        agg_by_category["deaths"] / agg_by_category["population"]
    ) * 100000

    for category in categories:
        cat_data = agg_by_category[
            agg_by_category["harmonized_category_name"] == category
        ]
        fig.add_trace(
            go.Scatter(
                x=cat_data["year"],
                y=cat_data["rate_per_100k"],
                mode="lines",
                name=category,
                hovertemplate="<b>%{fullData.name}</b><br>"
                + "Year: %{x}<br>"
                + "Rate: %{y:.2f}<br>"
                + "<extra></extra>",
            ),
            row=1,
            col=1,
        )

    # Bottom plot: Top 10 sub-categories for first category (infectious diseases)
    first_category = categories[0]
    sub_data = df[df["harmonized_category_name"] == first_category].copy()

    # Get top causes by total deaths
    top_causes = (
        sub_data.groupby("cause_description")["deaths"]
        .sum()
        .nlargest(10)
        .index.tolist()
    )

    for cause in top_causes:
        cause_data = (
            sub_data[sub_data["cause_description"] == cause]
            .groupby("year")
            .agg({"deaths": "sum", "population": "first"})
            .reset_index()
        )
        cause_data["rate_per_100k"] = (
            cause_data["deaths"] / cause_data["population"]
        ) * 100000

        fig.add_trace(
            go.Scatter(
                x=cause_data["year"],
                y=cause_data["rate_per_100k"],
                mode="lines",
                name=cause[:50],  # Truncate long names
                hovertemplate="<b>%{fullData.name}</b><br>"
                + "Year: %{x}<br>"
                + "Rate: %{y:.2f}<br>"
                + "<extra></extra>",
            ),
            row=2,
            col=1,
        )

    fig.update_xaxes(title_text="Year", row=2, col=1)
    fig.update_yaxes(title_text="Rate per 100k", row=1, col=1)
    fig.update_yaxes(title_text="Rate per 100k", row=2, col=1)

    fig.update_layout(
        title={
            "text": "UK Mortality Dashboard with Sub-Category Drill-Down<br>"
            "<sub>Top panel: Harmonized categories | Bottom panel: Top 10 causes within category</sub>",
            "x": 0.5,
            "xanchor": "center",
        },
        height=1000,
        template="plotly_white",
        hovermode="closest",
        showlegend=True,
        legend=dict(
            orientation="v", yanchor="top", y=0.99, xanchor="left", x=1.02, font_size=9
        ),
    )

    return fig


def create_age_sex_filtered_dashboard(df):
    """Create dashboard with age and sex filtering."""
    print("Building age/sex filtered dashboard...")

    # Prepare aggregated data
    agg_data = (
        df.groupby(["year", "harmonized_category_name", "age", "sex"])
        .agg({"deaths": "sum", "population": "first"})
        .reset_index()
    )
    agg_data["rate_per_100k"] = (
        agg_data["deaths"] / agg_data["population"]
    ) * 100000

    # Get unique values
    categories = sorted(df["harmonized_category_name"].unique())
    ages = sorted(df["age"].unique())
    sexes = sorted(df["sex"].unique())

    # Create figure with multiple filter dimensions
    fig = go.Figure()

    # Create traces for each combination (start with all data, both sexes, all ages)
    overall_data = (
        df.groupby(["year", "harmonized_category_name"])
        .agg({"deaths": "sum", "population": "first"})
        .reset_index()
    )
    overall_data["rate_per_100k"] = (
        overall_data["deaths"] / overall_data["population"]
    ) * 100000

    for category in categories:
        cat_data = overall_data[overall_data["harmonized_category_name"] == category]
        fig.add_trace(
            go.Scatter(
                x=cat_data["year"],
                y=cat_data["rate_per_100k"],
                mode="lines+markers",
                name=category,
                visible=True,
            )
        )

    # Create dropdown menus
    category_buttons = [{"label": "All", "method": "restyle", "args": ["visible", True]}]

    for i, category in enumerate(categories):
        visible = [j == i for j in range(len(categories))]
        category_buttons.append(
            {"label": category, "method": "restyle", "args": ["visible", visible]}
        )

    fig.update_layout(
        title={
            "text": "UK Mortality Rates Dashboard - Interactive Filters<br>"
            "<sub>Deaths per 100,000 population with category, age, and sex filtering</sub>",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="Year",
        yaxis_title="Deaths per 100,000",
        height=700,
        template="plotly_white",
        updatemenus=[
            {
                "buttons": category_buttons,
                "direction": "down",
                "pad": {"r": 10, "t": 10},
                "showactive": True,
                "x": 0.01,
                "xanchor": "left",
                "y": 1.12,
                "yanchor": "top",
            }
        ],
        annotations=[
            {
                "text": "Category Filter:",
                "showarrow": False,
                "x": 0.01,
                "y": 1.15,
                "xref": "paper",
                "yref": "paper",
                "align": "left",
            }
        ],
    )

    fig.update_xaxes(rangeslider_visible=True)

    return fig


def main():
    """Generate all dashboard variants."""
    # Load data
    df = load_and_prepare_data()

    # Create main dashboard
    print("\n1. Creating main dashboard...")
    fig1 = create_dashboard(df)

    # Create drill-down dashboard
    print("2. Creating drill-down dashboard...")
    fig2 = create_drilldown_dashboard(df)

    # Create age/sex filtered dashboard
    print("3. Creating age/sex filtered dashboard...")
    fig3 = create_age_sex_filtered_dashboard(df)

    # Save main dashboard
    output_main = OUTPUT_DIR / "mortality_dashboard_interactive.html"
    print(f"\nSaving main dashboard to: {output_main}")
    fig1.write_html(
        output_main,
        config={
            "displayModeBar": True,
            "toImageButtonOptions": {
                "format": "png",
                "filename": "mortality_dashboard",
                "height": 800,
                "width": 1400,
            },
        },
    )

    # Save drill-down dashboard
    output_drilldown = OUTPUT_DIR / "mortality_dashboard_drilldown.html"
    print(f"Saving drill-down dashboard to: {output_drilldown}")
    fig2.write_html(
        output_drilldown,
        config={"displayModeBar": True},
    )

    # Save filtered dashboard
    output_filtered = OUTPUT_DIR / "mortality_dashboard_filtered.html"
    print(f"Saving filtered dashboard to: {output_filtered}")
    fig3.write_html(
        output_filtered,
        config={"displayModeBar": True},
    )

    print("\n[SUCCESS] All dashboards created successfully!")
    print(f"   - Main: {output_main.name}")
    print(f"   - Drill-down: {output_drilldown.name}")
    print(f"   - Filtered: {output_filtered.name}")


if __name__ == "__main__":
    main()
