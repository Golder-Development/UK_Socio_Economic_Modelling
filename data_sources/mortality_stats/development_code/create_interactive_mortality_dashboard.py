"""
Create interactive Plotly dashboard for UK mortality data (1901-2025).
Shows deaths per 100k by harmonized category with filtering and drill-down.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from pathlib import Path
import zipfile

# Paths
BASE_DIR = Path(__file__).parent.parent
REPO_ROOT = BASE_DIR.parent.parent
OUTPUT_DIR = REPO_ROOT / "generated_charts"
# Prefer rebuilt harmonized file from archive (ZIP), then CSV
# If harmonized data stops at 2000, we will merge in modern 2001-2017 data
# from the comprehensive by-cause export to keep dashboards complete.
PREFERRED_ZIP = BASE_DIR / "uk_mortality_by_cause_1901_onwards.zip"
PREFERRED_CSV = BASE_DIR / "uk_mortality_by_cause_1901_onwards.csv"
HARM_FALLBACK_CSV = BASE_DIR / "uk_mortality_comprehensive_1901_2025_harmonized.csv"

# Comprehensive (unharmonized) by-cause data used to add 2001-2017 rows
COMPREHENSIVE_BY_CAUSE_ZIP = BASE_DIR / "uk_mortality_by_cause_1901_2025.zip"
COMPREHENSIVE_BY_CAUSE_INNER = "uk_mortality_by_cause_1901_2025.csv"

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


def _read_csv_from_zip(zip_path: Path, inner_name: str = None) -> pd.DataFrame:
    """Read a single CSV from a zip file. If inner_name is None, use the first .csv inside."""
    with zipfile.ZipFile(zip_path, 'r') as zf:
        name = inner_name
        if name is None:
            # choose the first csv entry
            candidates = [n for n in zf.namelist() if n.lower().endswith('.csv')]
            if not candidates:
                raise FileNotFoundError(f"No CSV found inside {zip_path}")
            name = candidates[0]
        with zf.open(name) as f:
            return pd.read_csv(f)


def _ensure_harmonized_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Create harmonized_category fields if they are missing (e.g., for modern ICD-10 data)."""
    df = df.copy()
    if 'harmonized_category_name' not in df.columns:
        # Use descriptive cause text if available; otherwise fall back to cause code
        if 'cause_description' in df.columns:
            df['harmonized_category_name'] = df['cause_description']
        else:
            df['harmonized_category_name'] = df.get('cause', pd.NA)
    if 'harmonized_category' not in df.columns:
        df['harmonized_category'] = (
            df['harmonized_category_name']
            .astype(str)
            .str.lower()
            .str.replace('[^a-z0-9]+', '-', regex=True)
            .str.strip('-')
        )
    return df


def load_and_prepare_data():
    """Load mortality data, merging modern ICD-10 rows if harmonized data stops at 2000."""
    print("Loading data...")

    harmonized_df = None
    source_used = None

    # 1) Load harmonized (historical) data if available
    if PREFERRED_ZIP.exists():
        harmonized_df = _read_csv_from_zip(PREFERRED_ZIP)
        source_used = PREFERRED_ZIP.name
    elif PREFERRED_CSV.exists():
        harmonized_df = pd.read_csv(PREFERRED_CSV)
        source_used = PREFERRED_CSV.name
    elif HARM_FALLBACK_CSV.exists():
        harmonized_df = pd.read_csv(HARM_FALLBACK_CSV)
        source_used = HARM_FALLBACK_CSV.name

    # 2) Optionally load comprehensive by-cause (includes 2001-2017) if needed
    modern_df = None
    if COMPREHENSIVE_BY_CAUSE_ZIP.exists():
        modern_df = _read_csv_from_zip(COMPREHENSIVE_BY_CAUSE_ZIP, COMPREHENSIVE_BY_CAUSE_INNER)
        modern_df = _ensure_harmonized_columns(modern_df)

    if harmonized_df is None and modern_df is None:
        raise FileNotFoundError(
            "No mortality dataset found. Expected harmonized (1901-2000) or comprehensive by-cause (1901-2025)."
        )

    # If harmonized data stops before modern years, append modern rows
    dfs_to_concat = []
    if harmonized_df is not None:
        dfs_to_concat.append(harmonized_df)
    if modern_df is not None:
        # Only add modern rows not already present in harmonized data
        if harmonized_df is not None:
            max_harm_year = harmonized_df["year"].max()
            modern_subset = modern_df[modern_df["year"] > max_harm_year]
        else:
            modern_subset = modern_df
        dfs_to_concat.append(modern_subset)

    df = pd.concat(dfs_to_concat, ignore_index=True, sort=False)

    # Ensure harmonized columns exist
    df = _ensure_harmonized_columns(df)

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
    if source_used:
        print(f"Base source: {source_used}")
    if modern_df is not None:
        print("Modern data merged (ICD-10)")

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
                {"title.text": "UK Mortality Rates per 100k (All Categories)"},
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
                    {"title.text": f"UK Mortality Rates per 100k - {category}"},
                ],
            }
        )

    # Update layout with dropdown menus
    fig.update_layout(
        title={
            "text": "<b>UK Mortality Rates per 100,000 Population (1901-2025)</b><br>"
            "<sub>Interactive Dashboard - Filter by Category, Age, and Sex</sub>",
            "x": 0.5,
            "xanchor": "center",
                    "font": {"size": 24, "color": "#1f1f1f"},
        },
        xaxis_title="Year",
        yaxis_title="Deaths per 100,000 Population",
        hovermode="closest",
        template="plotly_white",
        margin=dict(t=160),
        height=700,
        updatemenus=[
            {
                "buttons": category_buttons,
                "direction": "down",
                "pad": {"r": 10, "t": 10},
                "showactive": True,
                "x": 0.01,
                "xanchor": "left",
                "y": 1.06,
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
                "y": 1.08,
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
            "text": "<b>UK Mortality Dashboard with Sub-Category Drill-Down</b><br>"
            "<sub>Top panel: Harmonized categories | Bottom panel: Top 10 causes within category</sub>",
                        "font": {"size": 24, "color": "#1f1f1f"},
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
    """Create dashboard with age and sex filtering, plus stacked/unstacked toggle."""
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

    # UNSTACKED MODE (default): Line chart with one line per category
    for category in categories:
        cat_data = overall_data[overall_data["harmonized_category_name"] == category]
        fig.add_trace(
            go.Scatter(
                x=cat_data["year"],
                y=cat_data["rate_per_100k"],
                mode="lines+markers",
                name=category,
                visible=True,
                stackgroup=None,  # Unstacked
            )
        )

    # STACKED MODE: Bar chart with stacked bars per category
    for category in categories:
        cat_data = overall_data[overall_data["harmonized_category_name"] == category]
        fig.add_trace(
            go.Bar(
                x=cat_data["year"],
                y=cat_data["rate_per_100k"],
                name=category,
                visible=False,
            )
        )

    # Create category filter buttons (affects both unstacked and stacked)
    category_buttons = [{"label": "All", "method": "restyle", "args": ["visible", [True] * len(categories) + [False] * len(categories)]}]

    for i, category in enumerate(categories):
        visible_unstacked = [j == i for j in range(len(categories))] + [False] * len(categories)
        visible_stacked = [False] * len(categories) + [j == i for j in range(len(categories))]
        category_buttons.append(
            {"label": category, "method": "restyle", "args": ["visible", visible_unstacked]}
        )
    
    # Create stacked/unstacked toggle buttons
    stack_buttons = [
        {
            "label": "Unstacked (Lines)",
            "method": "update",
            "args": [
                {"visible": [True] * len(categories) + [False] * len(categories)},
                {"title.text": "UK Mortality Rates Dashboard — Category Filter (Unstacked)<br><sub>Deaths per 100,000 population; line view for trend comparison</sub>"}
            ]
        },
        {
            "label": "Stacked (Area)",
            "method": "update",
            "args": [
                {"visible": [False] * len(categories) + [True] * len(categories)},
                {"title.text": "UK Mortality Rates Dashboard — Category Filter (Stacked)<br><sub>Deaths per 100,000 population; stacked view for composition analysis</sub>"}
            ]
        }
    ]

    fig.update_layout(
        title={
            "text": "<b>UK Mortality Rates Dashboard — Age/Sex Filtered</b><br>"
            "<sub>Deaths per 100,000 population with stacked/unstacked view toggle</sub>",
                        "font": {"size": 24, "color": "#1f1f1f"},
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="Year",
        yaxis_title="Deaths per 100,000",
            barmode="stack",  # Stack bars for stacked view
        height=700,
        template="plotly_white",
        margin=dict(t=160),
        updatemenus=[
            {
                "buttons": stack_buttons,
                "direction": "down",
                "pad": {"r": 10, "t": 10},
                "showactive": True,
                "x": 0.01,
                "xanchor": "left",
                "y": 1.06,
                "yanchor": "top",
            },
            {
                "buttons": category_buttons,
                "direction": "down",
                "pad": {"r": 10, "t": 10},
                "showactive": True,
                "x": 0.15,
                "xanchor": "left",
                "y": 1.06,
                "yanchor": "top",
            }
        ],
        annotations=[
            {
                "text": "View Mode:",
                "showarrow": False,
                "x": 0.01,
                "y": 1.08,
                "xref": "paper",
                "yref": "paper",
                "align": "left",
                "font": {"size": 11},
            },
            {
                "text": "Category Filter:",
                "showarrow": False,
                "x": 0.15,
                "y": 1.08,
                "xref": "paper",
                "yref": "paper",
                "align": "left",
                "font": {"size": 11},
            }
        ],
    )

    fig.update_xaxes(rangeslider_visible=True)

    return fig


def create_age_group_dashboard(df):
    """Create dashboard showing mortality by age group with stacked/unstacked toggle and metric selection."""
    print("Building age group dashboard...")

    # Define age groups
    def categorize_age(age_str):
        """Map age ranges to standard demographic groups."""
        if pd.isna(age_str):
            return "Unknown"
        
        age_str = str(age_str).strip().replace('T', '')
        
        # Handle special cases
        if age_str == '<1' or age_str == '00' or age_str == '0':
            return "0-4"
        if age_str in ['85+', '80+', '90+']:
            return "85+"
        
        # Extract starting age from range (e.g., "01-04" -> 1, "25-29" -> 25)
        try:
            if '-' in age_str:
                start_age = int(age_str.split('-')[0])
            else:
                start_age = int(age_str)
            
            # Categorize based on starting age
            if start_age <= 4:
                return "0-4"
            elif start_age <= 14:
                return "5-14"
            elif start_age <= 24:
                return "15-24"
            elif start_age <= 34:
                return "25-34"
            elif start_age <= 44:
                return "35-44"
            elif start_age <= 54:
                return "45-54"
            elif start_age <= 64:
                return "55-64"
            elif start_age <= 74:
                return "65-74"
            elif start_age <= 84:
                return "75-84"
            else:
                return "85+"
        except (ValueError, IndexError):
            return "Unknown"

    # Add age_group column
    df_with_groups = df.copy()
    df_with_groups["age_group"] = df_with_groups["age"].apply(categorize_age)

    # Aggregate by year and age group
    agg_data = (
        df_with_groups.groupby(["year", "age_group"])
        .agg({"deaths": "sum", "population": "first"})
        .reset_index()
    )
    agg_data["rate_per_100k"] = (agg_data["deaths"] / agg_data["population"]) * 100000
    agg_data["rate_per_10k"] = (agg_data["deaths"] / agg_data["population"]) * 10000

    # Get unique age groups in logical order
    age_group_order = ["0-4", "5-14", "15-24", "25-34", "35-44", "45-54", "55-64", "65-74", "75-84", "85+", "Unknown"]
    age_groups = [ag for ag in age_group_order if ag in agg_data["age_group"].unique()]

    # Create figure with multiple traces
    fig = go.Figure()

    # UNSTACKED MODE (default): Line chart with one line per age group
    for age_group in age_groups:
        ag_data = agg_data[agg_data["age_group"] == age_group].sort_values("year")
        fig.add_trace(
            go.Scatter(
                x=ag_data["year"],
                y=ag_data["rate_per_100k"],
                mode="lines+markers",
                name=age_group,
                visible=True,
                stackgroup=None,  # Unstacked
                customdata=list(zip(
                    ag_data["rate_per_10k"],
                    ag_data["deaths"]
                )),
            )
        )

    # STACKED MODE: Bar chart with stacked bars per age group
    for age_group in age_groups:
        ag_data = agg_data[agg_data["age_group"] == age_group].sort_values("year")
        fig.add_trace(
            go.Bar(
                x=ag_data["year"],
                y=ag_data["rate_per_100k"],
                name=age_group,
                visible=False,
                customdata=list(zip(
                    ag_data["rate_per_10k"],
                    ag_data["deaths"]
                )),
            )
        )

    # Create view toggle buttons (unstacked/stacked)
    view_buttons = [
        {
            "label": "Unstacked (Lines)",
            "method": "update",
            "args": [
                {"visible": [True] * len(age_groups) + [False] * len(age_groups)},
                {"title.text": "<b>UK Mortality by Age Group — Unstacked View</b><br><sub>Deaths per 100,000 population; line view for trend comparison</sub>"}
            ]
        },
        {
            "label": "Stacked (Area)",
            "method": "update",
            "args": [
                {"visible": [False] * len(age_groups) + [True] * len(age_groups)},
                {"title.text": "<b>UK Mortality by Age Group — Stacked View</b><br><sub>Deaths per 100,000 population; stacked view for composition analysis</sub>"}
            ]
        }
    ]

    # Create age group filter buttons
    age_group_buttons = [
        {
            "label": "All",
            "method": "restyle",
            "args": ["visible", [True] * len(age_groups) + [False] * len(age_groups)]
        }
    ]

    for i, age_group in enumerate(age_groups):
        visible_unstacked = [j == i for j in range(len(age_groups))] + [False] * len(age_groups)
        age_group_buttons.append(
            {"label": age_group, "method": "restyle", "args": ["visible", visible_unstacked]}
        )

    # Create metric toggle buttons
    metric_buttons = []
    for metric_name, y_field_idx in [("Per 100k", 0), ("Per 10k", 1), ("Actual Deaths", 2)]:
        if metric_name == "Per 100k":
            # Default: use y directly (already rate_per_100k)
            metric_buttons.append({
                "label": metric_name,
                "method": "restyle",
                "args": ["y", [agg_data[agg_data["age_group"] == ag].sort_values("year")["rate_per_100k"].tolist() for ag in age_groups] * 2]
            })
        elif metric_name == "Per 10k":
            metric_buttons.append({
                "label": metric_name,
                "method": "restyle",
                "args": ["y", [agg_data[agg_data["age_group"] == ag].sort_values("year")["rate_per_10k"].tolist() for ag in age_groups] * 2]
            })
        else:  # Actual Deaths
            metric_buttons.append({
                "label": metric_name,
                "method": "restyle",
                "args": ["y", [agg_data[agg_data["age_group"] == ag].sort_values("year")["deaths"].tolist() for ag in age_groups] * 2]
            })

    fig.update_layout(
        title={
            "text": "<b>UK Mortality by Age Group — Unstacked View</b><br>"
            "<sub>Deaths per 100,000 population; line view for trend comparison</sub>",
            "font": {"size": 24, "color": "#1f1f1f"},
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="Year",
        yaxis_title="Deaths per 100,000",
        barmode="stack",  # Stack bars for stacked view
        height=700,
        template="plotly_white",
        margin=dict(t=160),
        updatemenus=[
            {
                "buttons": view_buttons,
                "direction": "down",
                "pad": {"r": 10, "t": 10},
                "showactive": True,
                "x": 0.01,
                "xanchor": "left",
                "y": 1.06,
                "yanchor": "top",
                "bgcolor": "#e8e8e8",
                "bordercolor": "#333",
                "borderwidth": 1,
            },
            {
                "buttons": age_group_buttons,
                "direction": "down",
                "pad": {"r": 10, "t": 10},
                "showactive": True,
                "x": 0.22,
                "xanchor": "left",
                "y": 1.06,
                "yanchor": "top",
                "bgcolor": "#f0f0f0",
                "bordercolor": "#333",
                "borderwidth": 1,
            },
            {
                "buttons": metric_buttons,
                "direction": "right",
                "pad": {"r": 10, "t": 10},
                "showactive": True,
                "x": 0.60,
                "xanchor": "left",
                "y": 1.06,
                "yanchor": "top",
                "bgcolor": "#f8f8f8",
                "bordercolor": "#333",
                "borderwidth": 1,
            },
        ],
        annotations=[
            {"text": "View:", "showarrow": False, "x": 0.01, "y": 1.08, "xref": "paper", "yref": "paper"},
            {"text": "Age Group:", "showarrow": False, "x": 0.22, "y": 1.08, "xref": "paper", "yref": "paper"},
            {"text": "Metric:", "showarrow": False, "x": 0.60, "y": 1.08, "xref": "paper", "yref": "paper", "xanchor": "left"},
        ],
    )

    fig.update_xaxes(rangeslider_visible=True)

    return fig


def _build_subset_time_series(df_subset: pd.DataFrame):
    """Aggregate subset by year and category and prepare metric arrays for Plotly updates."""
    # Aggregate
    agg = (
        df_subset.groupby(["year", "harmonized_category_name"]).agg({"deaths": "sum", "population": "first"}).reset_index()
    )
    # Metrics
    agg["rate_per_100k"] = (agg["deaths"] / agg["population"]) * 100000
    agg["rate_per_10k"] = (agg["deaths"] / agg["population"]) * 10000

    categories = sorted(agg["harmonized_category_name"].unique())

    # Build per-category series for each metric
    years_sorted = sorted(agg["year"].unique())
    y_per_100k = []
    y_per_10k = []
    y_deaths = []
    for cat in categories:
        cat_df = agg[agg["harmonized_category_name"] == cat].sort_values("year")
        # Ensure alignment to full year range
        cat_df = cat_df.set_index("year").reindex(years_sorted)
        y_per_100k.append(cat_df["rate_per_100k"].tolist())
        y_per_10k.append(cat_df["rate_per_10k"].tolist())
        y_deaths.append(cat_df["deaths"].tolist())

    return {
        "years": years_sorted,
        "categories": categories,
        "y_per_100k": y_per_100k,
        "y_per_10k": y_per_10k,
        "y_deaths": y_deaths,
    }


def create_subset_dashboard(df: pd.DataFrame, subset_name: str, mask: pd.Series):
    """
    Create a compact dashboard for a specific subset with:
    - Category dropdown (25 harmonized codes)
    - Metric toggle: per 100k, per 10k, actual deaths

    Note: Rates use total population estimates as denominator.
    """
    print(f"Building subset dashboard: {subset_name} ...")
    df_sub = df.loc[mask].copy()
    prep = _build_subset_time_series(df_sub)

    years = prep["years"]
    categories = prep["categories"]
    y100k = prep["y_per_100k"]
    y10k = prep["y_per_10k"]
    yabs = prep["y_deaths"]

    fig = go.Figure()

    # Add traces (default metric: per 100k) - dual sets for view toggle
    # Lines (unstacked)
    for i, cat in enumerate(categories):
        fig.add_trace(
            go.Scatter(
                x=years,
                y=y100k[i],
                mode="lines+markers",
                name=cat,
                hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Value: %{y:.2f}<extra></extra>",
                visible=True,
            )
        )
    # Bars (stacked)
    for i, cat in enumerate(categories):
        fig.add_trace(
            go.Bar(
                x=years,
                y=y100k[i],
                name=cat,
                visible=False,
            )
        )

    # Helpers
    n = len(categories)
    all_lines = [True] * n + [False] * n
    all_bars = [False] * n + [True] * n

    # Category dropdown (affects current view mode defaulting to lines)
    cat_buttons = [
        {
            "label": "All Categories",
            "method": "update",
            "args": [
                {"visible": all_lines},
                {"title.text": f"{subset_name} — All Categories (Unstacked)"},
            ],
        }
    ]
    for i, cat in enumerate(categories):
        vis_lines = [False] * n
        vis_lines[i] = True
        vis = vis_lines + [False] * n
        cat_buttons.append(
            {
                "label": cat,
                "method": "update",
                "args": [
                    {"visible": vis},
                    {"title.text": f"{subset_name} — {cat} (Unstacked)"},
                ],
            }
        )

    # Metric toggle: update all traces' y arrays (lines + bars)
    metric_buttons = [
        {
            "label": "Deaths per 100k",
            "method": "update",
            "args": [
                {"y": y100k + y100k},
                {"yaxis": {"title": "Deaths per 100,000"}},
            ],
        },
        {
            "label": "Deaths per 10k",
            "method": "update",
            "args": [
                {"y": y10k + y10k},
                {"yaxis": {"title": "Deaths per 10,000"}},
            ],
        },
        {
            "label": "Actual deaths",
            "method": "update",
            "args": [
                {"y": yabs + yabs},
                {"yaxis": {"title": "Deaths (count)"}},
            ],
        },
    ]

    # View mode toggle: lines vs stacked bars
    view_buttons = [
        {
            "label": "Unstacked (Lines)",
            "method": "update",
            "args": [
                {"visible": all_lines},
                {"title.text": f"UK Mortality — {subset_name} (Unstacked)"},
            ],
        },
        {
            "label": "Stacked (Area)",
            "method": "update",
            "args": [
                {"visible": all_bars},
                {"title.text": f"UK Mortality — {subset_name} (Stacked)"},
            ],
        },
    ]

    fig.update_layout(
        title={
            "text": f"<b>UK Mortality Dashboard — {subset_name}</b><br><sub>Select category, metric, and view mode. Interactive controls below.</sub>",
                        "font": {"size": 24, "color": "#1f1f1f"},
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="Year",
        yaxis_title="Deaths per 100,000",
        template="plotly_white",
        height=700,
        hovermode="closest",
        barmode="stack",
        margin=dict(t=160),
        updatemenus=[
            {
                "buttons": view_buttons,
                "direction": "down",
                "pad": {"r": 10, "t": 10},
                "showactive": True,
                "x": 0.01,
                "xanchor": "left",
                "y": 1.06,
                "yanchor": "top",
                "bgcolor": "#f0f0f0",
                "bordercolor": "#333",
                "borderwidth": 1,
            },
            {
                "buttons": cat_buttons,
                "direction": "down",
                "pad": {"r": 10, "t": 10},
                "showactive": True,
                "x": 0.22,
                "xanchor": "left",
                "y": 1.06,
                "yanchor": "top",
                "bgcolor": "#f0f0f0",
                "bordercolor": "#333",
                "borderwidth": 1,
            },
            {
                "buttons": metric_buttons,
                "direction": "right",
                "pad": {"r": 10, "t": 10},
                "showactive": True,
                "x": 0.60,
                "xanchor": "left",
                "y": 1.06,
                "yanchor": "top",
                "bgcolor": "#f8f8f8",
                "bordercolor": "#333",
                "borderwidth": 1,
            },
        ],
        annotations=[
            {"text": "View:", "showarrow": False, "x": 0.01, "y": 1.08, "xref": "paper", "yref": "paper"},
            {"text": "Category:", "showarrow": False, "x": 0.22, "y": 1.08, "xref": "paper", "yref": "paper"},
            {"text": "Metric:", "showarrow": False, "x": 0.60, "y": 1.08, "xref": "paper", "yref": "paper", "xanchor": "left"},
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

    # Create age group dashboard
    print("4. Creating age group dashboard...")
    fig4 = create_age_group_dashboard(df)

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

    # Save age group dashboard
    output_age_groups = OUTPUT_DIR / "mortality_dashboard_age_groups.html"
    print(f"Saving age group dashboard to: {output_age_groups}")
    fig4.write_html(
        output_age_groups,
        config={"displayModeBar": True},
    )

    # Create subset dashboards (separate outputs)
    print("\n5. Creating subset dashboards...")

    # Use age_start column from harmonized data (already standardized)
    # If not present, extract it
    if 'age_start' not in df.columns:
        def extract_age_start(age_str):
            """Extract starting age from age range strings."""
            if pd.isna(age_str):
                return None
            s = str(age_str).strip()
            if s == '<1':
                return 0
            if s == '85+':
                return 85
            if '-' in s:
                try:
                    return int(s.split('-')[0].replace('T', ''))
                except (ValueError, IndexError):
                    return None
            try:
                return int(s.replace('T', ''))
            except ValueError:
                return None
        df['age_start'] = df['age'].apply(extract_age_start)

    # Age-based subsets: <=5, 6-19, 20-34, 35-64, 65-84, 85+
    subsets = [
        ("Preschool (<=5)", df['age_start'] <= 5, "mortality_dashboard_age_preschool.html"),
        ("School Age (6-19)", (df['age_start'] >= 6) & (df['age_start'] <= 19), "mortality_dashboard_age_school.html"),
        ("Young Adults (20-34)", (df['age_start'] >= 20) & (df['age_start'] <= 34), "mortality_dashboard_age_young_adults.html"),
        ("Older Adults (35-64)", (df['age_start'] >= 35) & (df['age_start'] <= 64), "mortality_dashboard_age_older_adults.html"),
        ("Young OAPs (65-84)", (df['age_start'] >= 65) & (df['age_start'] <= 84), "mortality_dashboard_age_young_oaps.html"),
        ("Old OAPs (85+)", df['age_start'] >= 85, "mortality_dashboard_age_old_oaps.html"),
    ]

    for title, mask, filename in subsets:
        try:
            fig_sub = create_subset_dashboard(df, title, mask)
            out_path = OUTPUT_DIR / filename
            print(f"Saving subset dashboard to: {out_path}")
            fig_sub.write_html(out_path, config={"displayModeBar": True})
        except Exception as e:
            print(f"Warning: failed to build subset '{title}': {e}")

    print("\n[SUCCESS] All dashboards created successfully!")
    print(f"   - Main: {output_main.name}")
    print(f"   - Drill-down: {output_drilldown.name}")
    print(f"   - Filtered: {output_filtered.name}")
    print(f"   - Age Groups: {output_age_groups.name}")
    print("   - Subsets: preschool, school, young_adults, older_adults, young_oaps, old_oaps")


if __name__ == "__main__":
    main()
