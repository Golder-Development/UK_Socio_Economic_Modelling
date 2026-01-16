"""
Interactive Political Donations Visualization Suite

Generates interactive HTML dashboards for UK political donations with:
- Time period filters (by year, quarter, reporting period)
- Donor type breakdowns (Cash, Non-Cash, Sponsorship, Public Funds, Bequests)
- Party-specific and comparative summary views
- Trend analysis and heatmaps
- Donor loyalty and concentration metrics

Outputs:
- generated_charts/donations_by_party_summary.html (all parties comparison)
- generated_charts/donations_by_party_<PARTY>.html (per major party)
- generated_charts/donations_donor_type_analysis.html (donor type trends)
- generated_charts/donations_time_analysis.html (temporal patterns)

Data source:
- data_sources/dashboard_demo_readonly/source/Donations_accepted_by_political_parties.csv

Features:
- Interactive year-based filtering (buttons for common time ranges)
- All donation types: Cash, Non-Cash, Sponsorship, Public Fund, Bequest, Other
- Hover tooltips for detailed information
- Comparative analysis across parties and time periods
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime
import sys
import warnings
import os

# Import formatting reference
from formatting_reference import get_political_donations_styled_html, format_currency

# Set encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Suppress warnings
warnings.filterwarnings('ignore')

# Configuration
DATA_FILE = Path(__file__).parent.parent / "data_sources" / "dashboard_demo_readonly" / "output" / "cleaned_donations.csv"
OUTPUT_DIR = Path(__file__).parent.parent / "generated_charts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Party groupings
MAJOR_PARTIES = [
    'Conservative and Unionist Party',
    'Labour Party',
    'Liberal Democrats',
    'UK Independence Party (UKIP)',
    'Green Party',
    'Scottish National Party (SNP)',
    'Plaid Cymru - The Party of Wales',
    'Democratic Unionist Party - D.U.P.',
    'Reform UK'
]

DONOR_TYPES = ['Cash', 'Non-Cash', 'Sponsorship', 'Public Fund', 'Bequest', 'Other']


def get_time_periods(df: pd.DataFrame) -> dict:
    """Define time periods for filtering based on available data."""
    years = sorted(df['Year'].dropna().unique())
    if len(years) == 0:
        return {'All Years': (None, None)}
    
    min_year = int(years[0])
    max_year = int(years[-1])
    
    periods = {
        'All Years': (min_year, max_year),
        'Last 5 Years': (max_year - 4, max_year),
        'Last 10 Years': (max_year - 9, max_year),
        '2001-2010': (2001, 2010),
        '2011-2020': (2011, 2020),
        '2021-Present': (2021, max_year),
    }
    
    # Only include periods that have data
    valid_periods = {}
    for name, (start, end) in periods.items():
        if name == 'All Years' or (start >= min_year and start <= max_year):
            valid_periods[name] = (start, end)
    
    return valid_periods


def filter_by_period(df: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    """Filter dataframe by year range."""
    if start_year is None or end_year is None:
        return df
    return df[(df['Year'] >= start_year) & (df['Year'] <= end_year)]


def create_year_filter_buttons(df: pd.DataFrame, fig: go.Figure, year_col: str = 'Year') -> go.Figure:
    """Add interactive year range filter buttons to a figure."""
    years = sorted(df[year_col].dropna().unique())
    if len(years) == 0:
        return fig
    
    min_year = int(years[0])
    max_year = int(years[-1])
    
    # Create buttons for common year ranges
    buttons = [
        dict(
            label="All Years",
            method="relayout",
            args=[{"xaxis.range": [min_year - 0.5, max_year + 0.5]}]
        ),
        dict(
            label="Last 5 Years",
            method="relayout",
            args=[{"xaxis.range": [max_year - 4.5, max_year + 0.5]}]
        ),
        dict(
            label="Last 10 Years",
            method="relayout",
            args=[{"xaxis.range": [max_year - 9.5, max_year + 0.5]}]
        ),
        dict(
            label="2015-2020",
            method="relayout",
            args=[{"xaxis.range": [2014.5, 2020.5]}]
        ),
        dict(
            label="2021-2025",
            method="relayout",
            args=[{"xaxis.range": [2020.5, 2025.5]}]
        ),
    ]
    
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=buttons,
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.0,
                xanchor="left",
                y=1.15,
                yanchor="top"
            ),
        ]
    )
    
    return fig


def load_and_prepare_data() -> pd.DataFrame:
    """Load and prepare donation data."""
    print("Loading donation data...")
    
    df = pd.read_csv(DATA_FILE, low_memory=False)
    
    # Parse dates
    for date_col in ['AcceptedDate', 'ReceivedDate', 'ReportedDate']:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], format='%d/%m/%Y', errors='coerce')
    
    # Clean Value column
    if 'Value' in df.columns:
        df['Value'] = df['Value'].astype(str).str.replace('£', '').str.replace(',', '')
        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    
    # Classify donation types
    df['DonationType_Clean'] = df['DonationType'].fillna('Unknown').astype(str)
    df['IsSponsorship_Bool'] = df['IsSponsorship'].astype(str).str.upper() == 'TRUE'
    df['IsBequest_Bool'] = df['IsBequest'].astype(str).str.upper() == 'TRUE'
    
    # Classify into donation categories
    def classify_donation_type(row):
        if row['IsBequest_Bool']:
            return 'Bequest'
        elif row['IsSponsorship_Bool']:
            return 'Sponsorship'
        elif 'Public Fund' in row['DonationType_Clean']:
            return 'Public Fund'
        elif 'Non Cash' in row['DonationType_Clean'] or 'Non-Cash' in row['DonationType_Clean']:
            return 'Non-Cash'
        elif 'Cash' in row['DonationType_Clean']:
            return 'Cash'
        else:
            # For Visit, Exempt Trust, etc. - classify as Other
            return 'Other'
    
    df['DonationCategory'] = df.apply(classify_donation_type, axis=1)
    
    # Extract year, quarter
    df['Year'] = df['AcceptedDate'].dt.year
    df['Quarter'] = df['AcceptedDate'].dt.quarter
    df['YearQuarter'] = df['Year'].astype(str) + '-Q' + df['Quarter'].astype(str)
    df['Month'] = df['AcceptedDate'].dt.month
    df['YearMonth'] = df['AcceptedDate'].dt.to_period('M').astype(str)
    
    # Parse party/entity from RegulatedEntityName (main party) or AccountingUnitName (sub-unit)
    df['Party'] = df['RegulatedEntityName'].fillna('Unknown')
    df['SubUnit'] = df['AccountingUnitName'].fillna('')
    
    # Filter to major parties
    df['IsMajorParty'] = df['Party'].isin(MAJOR_PARTIES)
    
    # Remove null values and NaN donations
    df = df.dropna(subset=['Value', 'AcceptedDate'])
    df = df[df['Value'] > 0]
    
    print("Loaded {0:,} donation records".format(len(df)))
    print("Date range: {0} to {1}".format(df['AcceptedDate'].min().date(), df['AcceptedDate'].max().date()))
    print("Total value: GBP {0:,.2f}".format(df['Value'].sum()))
    print("Parties: {0}".format(df['Party'].nunique()))
    print("Donors: {0}".format(df['DonorName'].nunique()))
    
    # Print donation type breakdown
    print("\nDonation Type Breakdown:")
    type_summary = df.groupby('DonationCategory').agg({
        'Value': ['sum', 'count']
    })
    for dtype in df['DonationCategory'].unique():
        if dtype in type_summary.index:
            total_val = type_summary.loc[dtype, ('Value', 'sum')]
            count_val = type_summary.loc[dtype, ('Value', 'count')]
            print("  {0}: {1:,} records, GBP {2:,.2f}".format(dtype, int(count_val), total_val))
    
    return df


def create_party_summary_dashboard(df: pd.DataFrame) -> None:
    """Create summary dashboard comparing all major parties with time period filtering."""
    print("\nCreating party summary dashboard...")
    
    df_major = df[df['IsMajorParty']].copy()
    time_periods = get_time_periods(df_major)
    
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'Total Donations by Party',
            'Donation Count by Party',
            'Donations by Type and Party (Stacked)',
            'Donor Concentration (Top 5 Donors per Party)',
            'Trend: Total Donations Over Time',
            'Donation Sources by Party'
        ),
        specs=[
            [{'type': 'bar'}, {'type': 'bar'}],
            [{'type': 'bar'}, {'type': 'scatter'}],
            [{'type': 'scatter'}, {'type': 'pie'}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # Store all traces for each time period
    all_traces = {period_name: [] for period_name in time_periods.keys()}
    
    for period_idx, (period_name, (start_year, end_year)) in enumerate(time_periods.items()):
        df_period = filter_by_period(df_major, start_year, end_year)
        
        # Calculate statistics for this period
        party_totals = df_period.groupby(['Party', 'DonationCategory']).agg({
            'Value': ['sum', 'count', 'mean'],
            'DonorName': 'nunique'
        }).reset_index()
        party_totals.columns = ['Party', 'DonationCategory', 'TotalValue', 'Count', 'AvgValue', 'UniqueDonors']
        
        party_by_type = party_totals.pivot(index='Party', columns='DonationCategory', values='TotalValue').fillna(0)
        party_counts = party_totals.pivot(index='Party', columns='DonationCategory', values='Count').fillna(0)
        
        time_series = df_period.groupby(['Party', 'YearQuarter']).agg({
            'Value': 'sum',
            'DonorName': 'nunique'
        }).reset_index().sort_values(['Party', 'YearQuarter'])
        
        visible = (period_idx == 0)  # Only first period visible initially
        
        # 1. Total by party (stacked bar)
        for dtype in DONOR_TYPES:
            if dtype in party_by_type.columns:
                values = party_by_type[dtype]
                fig.add_trace(
                    go.Bar(
                        y=values.index,
                        x=values.values,
                        name=dtype,
                        orientation='h',
                        text=['GBP {0:.1f}M'.format(v/1e6) for v in values.values],
                        textposition='inside',
                        visible=visible,
                        legendgroup=dtype,
                        showlegend=(period_idx == 0)
                    ),
                    row=1, col=1
                )
        
        # 2. Count by party
        total_counts = party_counts.sum(axis=1).sort_values(ascending=True)
        fig.add_trace(
            go.Bar(
                y=total_counts.index,
                x=total_counts.values,
                name='Donations',
                marker_color='rgba(100, 150, 200, 0.8)',
                text=total_counts.values,
                textposition='outside',
                orientation='h',
                visible=visible,
                showlegend=False
            ),
            row=1, col=2
        )
        
        # 3. Stacked bar by type
        for dtype in DONOR_TYPES:
            if dtype in party_by_type.columns:
                fig.add_trace(
                    go.Bar(
                        x=party_by_type.index,
                        y=party_by_type[dtype],
                        name=dtype,
                        hovertemplate='%{x}<br>' + dtype + ': GBP %{y:,.0f}<extra></extra>',
                        visible=visible,
                        legendgroup=dtype,
                        showlegend=False
                    ),
                    row=2, col=1
                )
        
        # 4. Top donors per party
        for party in MAJOR_PARTIES:
            party_df = df_period[df_period['Party'] == party]
            if len(party_df) > 0:
                top_donors = party_df.groupby('DonorName')['Value'].sum().nlargest(5)
                top_donors_pct = (top_donors / party_df['Value'].sum()) * 100
                
                fig.add_trace(
                    go.Bar(
                        x=top_donors_pct.index[::-1],
                        y=top_donors_pct.values[::-1],
                        name=party,
                        text=['{0:.1f}%'.format(v) for v in top_donors_pct.values[::-1]],
                        textposition='outside',
                        hovertemplate='%{x}<br>%{y:.1f}% of ' + party + '<extra></extra>',
                        visible=visible,
                        showlegend=False
                    ),
                    row=2, col=2
                )
        
        # 5. Trend line
        for party in MAJOR_PARTIES:
            party_time = time_series[time_series['Party'] == party].sort_values('YearQuarter')
            if len(party_time) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=party_time['YearQuarter'],
                        y=party_time['Value'],
                        mode='lines+markers',
                        name=party,
                        hovertemplate='%{x}<br>GBP %{y:,.0f}<extra></extra>',
                        line=dict(width=2),
                        visible=visible,
                        showlegend=False
                    ),
                    row=3, col=1
                )
        
        # 6. Pie chart
        party_totals_all = df_period.groupby('Party')['Value'].sum().sort_values(ascending=False)
        fig.add_trace(
            go.Pie(
                labels=party_totals_all.index,
                values=party_totals_all.values,
                hovertemplate='<b>%{label}</b><br>GBP %{value:,.0f}<br>%{percent}<extra></extra>',
                visible=visible,
                showlegend=False
            ),
            row=3, col=2
        )
    
    # Create dropdown menu for time period selection
    # Calculate number of traces per period
    traces_per_period = len(fig.data) // len(time_periods)
    
    buttons = []
    for period_idx, period_name in enumerate(time_periods.keys()):
        visible_list = [False] * len(fig.data)
        start_idx = period_idx * traces_per_period
        end_idx = start_idx + traces_per_period
        for i in range(start_idx, end_idx):
            visible_list[i] = True
        
        buttons.append(
            dict(
                label=period_name,
                method="update",
                args=[{"visible": visible_list},
                      {"title.text": "UK Political Donations - Party Comparison Dashboard<br><sub>Time Period: {0} | All donation types included</sub>".format(period_name)}]
            )
        )
    
    # Get year range for title
    years = sorted(df_major['Year'].dropna().unique())
    year_range_text = ""
    if len(years) > 0:
        year_range_text = " ({0}-{1})".format(int(years[0]), int(years[-1]))
    
    fig.update_layout(
        title_text="UK Political Donations - Party Comparison Dashboard<br><sub>Time Period: All Years | All donation types included</sub>",
        height=1400,
        showlegend=True,
        hovermode='closest',
        font=dict(size=11),
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                x=0.01,
                y=1.0,
                xanchor="left",
                yanchor="top",
                bgcolor="rgba(255, 255, 255, 0.9)",
                bordercolor="#888",
                borderwidth=2,
                buttons=buttons,
                active=0
            )
        ],
        annotations=[
            dict(
                text="<b>Time Period:</b>",
                showarrow=False,
                x=0.01,
                y=1.02,
                xref="paper",
                yref="paper",
                xanchor="left",
                yanchor="bottom",
                font=dict(size=12, color="black")
            )
        ]
    )
    
    # 4. Donor concentration (this section was already handled in the loop above)
    # 5. Trend line (this section was already handled in the loop above)
    # 6. Pie chart (this section was already handled in the loop above)
    
    # Update axis labels
    fig.update_xaxes(title_text="Total Value (GBP)", row=1, col=1)
    fig.update_xaxes(title_text="Number of Donations", row=1, col=2)
    fig.update_yaxes(title_text="Party", row=1, col=1)
    fig.update_yaxes(title_text="Party", row=1, col=2)
    
    fig.update_xaxes(title_text="Party", row=2, col=1)
    fig.update_yaxes(title_text="Total Value (GBP)", row=2, col=1)
    
    fig.update_xaxes(title_text="Donor", row=2, col=2)
    fig.update_yaxes(title_text="Percent of Total", row=2, col=2)
    
    fig.update_xaxes(title_text="Year-Quarter", row=3, col=1)
    fig.update_yaxes(title_text="Total Donations (GBP)", row=3, col=1)
    
    output_path = OUTPUT_DIR / "donations_by_party_summary.html"
    fig.write_html(str(output_path), include_plotlyjs='cdn')
    print("[DONE] Generated: {0}".format(output_path))


def create_donor_type_analysis(df: pd.DataFrame) -> None:
    """Create donor type analysis dashboard."""
    print("\nCreating donor type analysis...")
    
    df_major = df[df['IsMajorParty']].copy()
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Donations by Type (All Time)',
            'Donation Count by Type',
            'Type Distribution by Party',
            'Type Trends Over Time'
        ),
        specs=[[{'type': 'pie'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'scatter'}]],
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )
    
    # 1. Pie chart
    type_totals = df_major.groupby('DonationCategory')['Value'].sum()
    fig.add_trace(
        go.Pie(
            labels=type_totals.index,
            values=type_totals.values,
            hovertemplate='<b>%{label}</b><br>GBP %{value:,.0f}<br>%{percent}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # 2. Count by type
    type_counts = df_major.groupby('DonationCategory').size()
    fig.add_trace(
        go.Bar(
            x=type_counts.index,
            y=type_counts.values,
            marker_color='rgba(100, 200, 150, 0.8)',
            text=type_counts.values,
            textposition='outside',
            name='Count',
            hovertemplate='%{x}<br>%{y} donations<extra></extra>'
        ),
        row=1, col=2
    )
    
    # 3. Type distribution
    type_by_party = df_major.groupby(['Party', 'DonationCategory'])['Value'].sum().unstack(fill_value=0)
    type_by_party_pct = type_by_party.div(type_by_party.sum(axis=1), axis=0) * 100
    
    for dtype in DONOR_TYPES:
        if dtype in type_by_party_pct.columns:
            fig.add_trace(
                go.Bar(
                    x=type_by_party_pct.index,
                    y=type_by_party_pct[dtype],
                    name=dtype,
                    hovertemplate='%{x}<br>' + dtype + ': %{y:.1f}%<extra></extra>'
                ),
                row=2, col=1
            )
    
    # 4. Type trends over time
    type_time = df_major.groupby(['YearQuarter', 'DonationCategory'])['Value'].sum().reset_index()
    for dtype in DONOR_TYPES:
        dtype_data = type_time[type_time['DonationCategory'] == dtype].sort_values('YearQuarter')
        if len(dtype_data) > 0:
            fig.add_trace(
                go.Scatter(
                    x=dtype_data['YearQuarter'],
                    y=dtype_data['Value'],
                    mode='lines+markers',
                    name=dtype,
                    hovertemplate='%{x}<br>GBP %{y:,.0f}<extra></extra>',
                    line=dict(width=2)
                ),
                row=2, col=2
            )
    
    # Get year range for title
    years = sorted(df_major['Year'].dropna().unique())
    year_range_text = ""
    if len(years) > 0:
        year_range_text = " ({0}-{1})".format(int(years[0]), int(years[-1]))
    
    fig.update_layout(
        title_text="Political Donations - Donor Type Analysis{0}<br><sub>Breakdown: Cash, Non-Cash, Sponsorship, Public Fund, Bequest, Other</sub>".format(year_range_text),
        height=900,
        showlegend=True,
        hovermode='closest',
        font=dict(size=11)
    )
    
    fig.update_xaxes(title_text="Type", row=1, col=2)
    fig.update_yaxes(title_text="Count", row=1, col=2)
    
    fig.update_xaxes(title_text="Party", row=2, col=1)
    fig.update_yaxes(title_text="Percentage", row=2, col=1)
    fig.update_xaxes(title_text="Year-Quarter", row=2, col=2)
    fig.update_yaxes(title_text="Total Value (GBP)", row=2, col=2)
    
    output_path = OUTPUT_DIR / "donations_donor_type_analysis.html"
    fig.write_html(str(output_path), include_plotlyjs='cdn')
    print("[DONE] Generated: {0}".format(output_path))


def create_time_analysis(df: pd.DataFrame) -> None:
    """Create temporal analysis."""
    print("\nCreating time analysis...")
    
    df_major = df[df['IsMajorParty']].copy()
    
    monthly = df_major.groupby(['YearMonth', 'Party']).agg({
        'Value': 'sum',
        'DonorName': 'nunique'
    }).reset_index()
    monthly['YearMonth'] = monthly['YearMonth'].astype(str)
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=(
            'Monthly Donations by Party',
            'Donor Activity Over Time'
        ),
        specs=[[{'secondary_y': True}],
               [{'secondary_y': True}]],
        vertical_spacing=0.15
    )
    
    parties_to_plot = df_major.groupby('Party')['Value'].sum().nlargest(5).index
    
    for party in parties_to_plot:
        party_monthly = monthly[monthly['Party'] == party].sort_values('YearMonth')
        
        fig.add_trace(
            go.Scatter(
                x=party_monthly['YearMonth'],
                y=party_monthly['Value'],
                mode='lines',
                name=party,
                hovertemplate='%{x}<br>GBP %{y:,.0f}<extra></extra>',
                line=dict(width=2)
            ),
            row=1, col=1,
            secondary_y=False
        )
    
    donor_activity = df_major.groupby(['YearMonth', 'Party'])['DonorName'].nunique().reset_index()
    
    for party in parties_to_plot:
        party_donors = donor_activity[donor_activity['Party'] == party].sort_values('YearMonth')
        
        fig.add_trace(
            go.Bar(
                x=party_donors['YearMonth'],
                y=party_donors['DonorName'],
                name=party + ' (Donors)',
                showlegend=False,
                hovertemplate='%{x}<br>%{y} unique donors<extra></extra>',
                opacity=0.5
            ),
            row=2, col=1,
            secondary_y=False
        )
    
    fig.update_xaxes(title_text="Month", row=1, col=1)
    fig.update_yaxes(title_text="Total Donations (GBP)", row=1, col=1, secondary_y=False)
    
    fig.update_xaxes(title_text="Month", row=2, col=1)
    fig.update_yaxes(title_text="Unique Donors", row=2, col=1, secondary_y=False)
    
    # Get year range for title and slider
    years = sorted(df_major['Year'].dropna().unique())
    year_range_text = ""
    if len(years) > 0:
        min_year = int(years[0])
        max_year = int(years[-1])
        year_range_text = " ({0}-{1})".format(min_year, max_year)
    
    fig.update_layout(
        title_text="Political Donations - Temporal Analysis{0}<br><sub>Use range slider below charts to filter by date. All donation types included.</sub>".format(year_range_text),
        height=900,
        showlegend=True,
        hovermode='x unified',
        font=dict(size=11),
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(count=5, label="5y", step="year", stepmode="backward"),
                    dict(count=10, label="10y", step="year", stepmode="backward"),
                    dict(step="all", label="All")
                ]),
                bgcolor="rgba(255, 255, 255, 0.8)",
                x=0.0,
                y=1.08,
                xanchor='left',
                yanchor='top'
            ),
            rangeslider=dict(visible=True, thickness=0.05),
            type="date"
        )
    )
    
    output_path = OUTPUT_DIR / "donations_time_analysis.html"
    fig.write_html(str(output_path), include_plotlyjs='cdn')
    print("[DONE] Generated: {0}".format(output_path))


def create_party_specific_dashboard(df: pd.DataFrame, party: str) -> None:
    """Create detailed dashboard for a specific party with time period filtering."""
    party_df = df[df['Party'] == party].copy()
    
    if len(party_df) == 0:
        return
    
    time_periods = get_time_periods(party_df)
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '{0} - Donations by Type'.format(party),
            '{0} - Top 10 Donors'.format(party),
            '{0} - Monthly Trends'.format(party),
            '{0} - Donor Statistics'.format(party)
        ),
        specs=[[{'type': 'pie'}, {'type': 'bar'}],
               [{'type': 'scatter'}, {'type': 'box'}]],
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )
    
    # Generate traces for each time period
    for period_idx, (period_name, (start_year, end_year)) in enumerate(time_periods.items()):
        df_period = filter_by_period(party_df, start_year, end_year)
        
        visible = (period_idx == 0)  # Only first period visible initially
        
        # 1. Pie - by type
        type_totals = df_period.groupby('DonationCategory')['Value'].sum()
        fig.add_trace(
            go.Pie(
                labels=type_totals.index,
                values=type_totals.values,
                hovertemplate='<b>%{label}</b><br>GBP %{value:,.0f}<br>%{percent}<extra></extra>',
                visible=visible
            ),
            row=1, col=1
        )
        
        # 2. Top donors
        top_donors = df_period.groupby('DonorName')['Value'].sum().nlargest(10).sort_values()
        fig.add_trace(
            go.Bar(
                y=top_donors.index,
                x=top_donors.values,
                orientation='h',
                marker_color='rgba(150, 100, 200, 0.8)',
                text=['GBP {0:.2f}M'.format(v/1e6) if v >= 1e6 else 'GBP {0:.0f}K'.format(v/1e3) for v in top_donors.values],
                textposition='outside',
                hovertemplate='%{y}<br>GBP %{x:,.0f}<extra></extra>',
                visible=visible
            ),
            row=1, col=2
        )
        
        # 3. Monthly trend
        monthly = df_period.groupby('YearMonth')['Value'].sum().sort_index()
        fig.add_trace(
            go.Scatter(
                x=[str(m) for m in monthly.index],
                y=monthly.values,
                mode='lines+markers',
                fill='tozeroy',
                fillcolor='rgba(100, 150, 200, 0.2)',
                line=dict(color='rgba(100, 150, 200, 1)', width=2),
                hovertemplate='%{x}<br>GBP %{y:,.0f}<extra></extra>',
                visible=visible
            ),
            row=2, col=1
        )
        
        # 4. Distribution by type
        for dtype in sorted(df_period['DonationCategory'].unique()):
            dtype_data = df_period[df_period['DonationCategory'] == dtype]['Value']
            if len(dtype_data) > 0:
                fig.add_trace(
                    go.Box(
                        y=dtype_data,
                        name=dtype,
                        hovertemplate='<b>' + dtype + '</b><br>GBP %{y:,.0f}<extra></extra>',
                        visible=visible,
                        showlegend=(period_idx == 0)
                    ),
                    row=2, col=2
                )
    
    # Create dropdown menu
    traces_per_period = len(fig.data) // len(time_periods)
    
    buttons = []
    for period_idx, period_name in enumerate(time_periods.keys()):
        visible_list = [False] * len(fig.data)
        start_idx = period_idx * traces_per_period
        end_idx = start_idx + traces_per_period
        for i in range(start_idx, end_idx):
            visible_list[i] = True
        
        buttons.append(
            dict(
                label=period_name,
                method="update",
                args=[{"visible": visible_list},
                      {"title.text": "{0} - Detailed Donation Analysis<br><sub>Time Period: {1} | All donation types included</sub>".format(party, period_name)}]
            )
        )
    
    # Get year range for title
    years = sorted(party_df['Year'].dropna().unique())
    year_range_text = ""
    if len(years) > 0:
        year_range_text = " ({0}-{1})".format(int(years[0]), int(years[-1]))
    
    fig.update_layout(
        title_text="{0} - Detailed Donation Analysis<br><sub>Time Period: All Years | All donation types included</sub>".format(party),
        height=900,
        showlegend=False,
        hovermode='closest',
        font=dict(size=11),
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                x=0.01,
                y=1.0,
                xanchor="left",
                yanchor="top",
                bgcolor="rgba(255, 255, 255, 0.9)",
                bordercolor="#888",
                borderwidth=2,
                buttons=buttons,
                active=0
            )
        ],
        annotations=[
            dict(
                text="<b>Time Period:</b>",
                showarrow=False,
                x=0.01,
                y=1.02,
                xref="paper",
                yref="paper",
                xanchor="left",
                yanchor="bottom",
                font=dict(size=12, color="black")
            )
        ]
    )
    
    fig.update_xaxes(title_text="Month", row=2, col=1)
    fig.update_yaxes(title_text="Total Donations (GBP)", row=2, col=1)
    fig.update_yaxes(title_text="Donation Value (GBP)", row=2, col=2, type='log')
    
    # Sanitize party name for GitHub Pages compatibility
    # Remove special characters, dots, parentheses, and normalize spacing
    safe_party_name = party.lower()
    safe_party_name = safe_party_name.replace('&', 'and')
    safe_party_name = safe_party_name.replace('(', '').replace(')', '')
    safe_party_name = safe_party_name.replace('.', '').replace('-', '_')
    safe_party_name = safe_party_name.replace(' ', '_')
    # Remove consecutive underscores
    while '__' in safe_party_name:
        safe_party_name = safe_party_name.replace('__', '_')
    safe_party_name = safe_party_name.strip('_')
    
    output_path = OUTPUT_DIR / "donations_by_party_{0}.html".format(safe_party_name)
    
    # Generate chart HTML
    chart_html = fig.to_html(include_plotlyjs='cdn', div_id="donation-chart")
    
    # Create body content with about section
    body_content = """
    <div class="section">
        <h2>About This Dashboard</h2>
        <p>Use the <strong>Time Period</strong> dropdown menu at the top of the visualizations to explore donations across different time ranges. All panels update simultaneously when you change the time period.</p>
        <p>Donation types represented:</p>
        <div style="margin: 10px 0;">
            <span class="badge badge-cash">Cash</span>
            <span class="badge badge-non-cash">Non-Cash</span>
            <span class="badge badge-sponsorship">Sponsorship</span>
            <span class="badge badge-public-fund">Public Fund</span>
            <span class="badge badge-bequest">Bequest</span>
            <span class="badge badge-other">Other</span>
        </div>
    </div>
    
    <div class="section">
        <h2>Interactive Visualizations</h2>
        <h3>Donation Analysis</h3>
        <div class="chart-container">
            {0}
        </div>
    </div>
    """.format(chart_html)
    
    # Use formatting reference to generate styled HTML
    styled_html = get_political_donations_styled_html(
        title="{0} - Donation Analysis".format(party),
        subtitle="Comprehensive analysis of political donations received",
        body_content=body_content,
        include_legend=True
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(styled_html)
    print("  [DONE] {0}".format(output_path))


def create_comparative_heatmap(df: pd.DataFrame) -> None:
    """Create heatmap comparing parties across dimensions."""
    print("\nCreating comparative heatmap...")
    
    df_major = df[df['IsMajorParty']].copy()
    
    metrics = df_major.groupby('Party').agg({
        'Value': ['sum', 'mean', 'count'],
        'DonorName': 'nunique',
        'DonationCategory': lambda x: (x == 'Cash').sum() / len(x) * 100 if len(x) > 0 else 0
    }).reset_index()
    
    metrics.columns = ['Party', 'TotalValue', 'AvgDonation', 'Count', 'UniqueDonors', 'CashPct']
    
    heatmap_data = metrics.set_index('Party').copy()
    for col in heatmap_data.columns:
        max_val = heatmap_data[col].max()
        if max_val > 0:
            heatmap_data[col] = (heatmap_data[col] / max_val) * 100
    
    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale='RdYlGn',
            hovertemplate='<b>%{y}</b><br>%{x}: %{z:.1f}%<extra></extra>',
            text=np.round(heatmap_data.values, 1),
            texttemplate='%{text:.0f}%',
            textfont={"size": 10}
        )
    )
    
    fig.update_layout(
        title_text="Party Comparison Heatmap (Normalized Metrics)",
        xaxis_title="Metric",
        yaxis_title="Party",
        height=500,
        width=700,
        hovermode='closest'
    )
    
    output_path = OUTPUT_DIR / "donations_party_heatmap.html"
    fig.write_html(str(output_path), include_plotlyjs='cdn')
    print("[DONE] Generated: {0}".format(output_path))


def main():
    """Generate all donation visualizations."""
    print("=" * 90)
    print("POLITICAL DONATIONS INTERACTIVE VISUALIZATION SUITE")
    print("=" * 90)
    
    try:
        df = load_and_prepare_data()
        
        create_party_summary_dashboard(df)
        create_donor_type_analysis(df)
        create_time_analysis(df)
        create_comparative_heatmap(df)
        
        print("\nCreating party-specific dashboards...")
        for party in MAJOR_PARTIES:
            if party in df['Party'].unique():
                create_party_specific_dashboard(df, party)
        
        print("\n" + "=" * 90)
        print("[OK] COMPLETE: All donation visualizations generated")
        print("=" * 90)
        
    except Exception as e:
        print("\n[ERROR] {0}".format(e), file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
