"""
Political Donations Summary Dashboard
Enhanced HTML dashboard with professional styling matching cabinet analysis design
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import json
from datetime import datetime
from formatting_reference import get_political_donations_styled_html, format_currency

OUTPUT_DIR = Path(__file__).parent.parent / 'generated_charts'
OUTPUT_DIR.mkdir(exist_ok=True)



def create_summary_dashboard(donations_df):
    """Create a comprehensive summary dashboard"""
    
    # Map column names
    donation_amount_col = 'Value'  # Amount column
    donor_col = 'CleanedDonorName'  # Donor column
    party_col = 'CleanedRegulatedEntityName'  # Party/recipient column
    date_col = 'AcceptedDate'  # Date column
    type_col = 'DonationType'  # Donation type column
    
    # Summary statistics
    total_donations = donations_df[donation_amount_col].sum()
    avg_donation = donations_df[donation_amount_col].mean()
    num_donors = donations_df[donor_col].nunique()
    num_donations = len(donations_df)
    
    # By donation type
    by_type = donations_df.groupby(type_col)[donation_amount_col].agg(['sum', 'count']).sort_values('sum', ascending=False)
    
    # By party
    by_party = donations_df.groupby(party_col)[donation_amount_col].sum().sort_values(ascending=False).head(15)
    
    # Top donors
    top_donors = donations_df.groupby(donor_col)[donation_amount_col].sum().sort_values(ascending=False).head(10)
    
    # Create visualizations
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            "Total Donations by Party (Top 15)",
            "Donations by Type",
            "Top 10 Donors",
            "Monthly Donation Trend",
            "Donor Count by Party (Top 15)",
            "Average Donation by Type"
        ),
        specs=[
            [{"type": "bar"}, {"type": "pie"}],
            [{"type": "bar"}, {"type": "scatter"}],
            [{"type": "bar"}, {"type": "bar"}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.12
    )
    
    # 1. Total by Party (Bar)
    fig.add_trace(
        go.Bar(
            x=by_party.index,
            y=by_party.values,
            marker_color='#1f77b4',
            hovertemplate='<b>%{x}</b><br>Total: £%{y:,.0f}<extra></extra>',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # 2. By Donation Type (Pie)
    type_colors = {
        'Cash': '#4CAF50',
        'Non-cash': '#2196F3',
        'Sponsorship': '#FF9800',
        'Public Fund': '#9C27B0',
        'Bequest': '#f44336',
        'Other': '#999'
    }
    fig.add_trace(
        go.Pie(
            labels=by_type.index,
            values=by_type['sum'],
            marker_colors=[type_colors.get(str(t), '#999') for t in by_type.index],
            hovertemplate='<b>%{label}</b><br>Total: £%{value:,.0f}<extra></extra>',
            showlegend=True
        ),
        row=1, col=2
    )
    
    # 3. Top 10 Donors (Bar)
    fig.add_trace(
        go.Bar(
            y=top_donors.index,
            x=top_donors.values,
            orientation='h',
            marker_color='#ff7f0e',
            hovertemplate='<b>%{y}</b><br>Total: £%{x:,.0f}<extra></extra>',
            showlegend=False
        ),
        row=2, col=1
    )
    
    # 4. Monthly Trend (Line)
    donations_df[date_col] = pd.to_datetime(donations_df[date_col], errors='coerce')
    monthly = donations_df.set_index(date_col).groupby(pd.Grouper(freq='M'))[donation_amount_col].sum()
    monthly = monthly[monthly > 0]  # Remove zero values
    
    if len(monthly) > 0:
        fig.add_trace(
            go.Scatter(
                x=monthly.index,
                y=monthly.values,
                mode='lines+markers',
                line_color='#2ca02c',
                marker_size=6,
                hovertemplate='<b>%{x|%b %Y}</b><br>Total: £%{y:,.0f}<extra></extra>',
                showlegend=False
            ),
            row=2, col=2
        )
    
    # 5. Donor Count by Party (Bar)
    donor_count = donations_df.groupby(party_col)[donor_col].nunique().sort_values(ascending=False).head(15)
    fig.add_trace(
        go.Bar(
            x=donor_count.index,
            y=donor_count.values,
            marker_color='#d62728',
            hovertemplate='<b>%{x}</b><br>Donors: %{y}<extra></extra>',
            showlegend=False
        ),
        row=3, col=1
    )
    
    # 6. Average Donation by Type (Bar)
    avg_by_type = donations_df.groupby(type_col)[donation_amount_col].mean().sort_values(ascending=False)
    fig.add_trace(
        go.Bar(
            x=avg_by_type.index,
            y=avg_by_type.values,
            marker_color='#9467bd',
            hovertemplate='<b>%{x}</b><br>Average: £%{y:,.0f}<extra></extra>',
            showlegend=False
        ),
        row=3, col=2
    )
    
    # Update layout
    fig.update_layout(
        title_text="<b>UK Political Donations - Summary Dashboard</b><br><sub>Comprehensive analysis of all donations</sub>",
        height=1200,
        showlegend=True,
        hovermode='closest',
        font=dict(size=11, family="Arial"),
        plot_bgcolor='#fafafa',
        paper_bgcolor='white'
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="Party", row=1, col=1)
    fig.update_yaxes(title_text="Total (GBP)", row=1, col=1)
    fig.update_xaxes(title_text="Donor", row=2, col=1)
    fig.update_yaxes(title_text="Total (GBP)", row=2, col=1)
    fig.update_xaxes(title_text="Month", row=2, col=2)
    fig.update_yaxes(title_text="Total (GBP)", row=2, col=2)
    fig.update_xaxes(title_text="Party", row=3, col=1)
    fig.update_yaxes(title_text="Count", row=3, col=1)
    fig.update_xaxes(title_text="Donation Type", row=3, col=2)
    fig.update_yaxes(title_text="Average (GBP)", row=3, col=2)
    
    # Generate HTML with styling
    chart_html = fig.to_html(include_plotlyjs='cdn')
    
    # Prepare body content
    body_content = """
    <div class="section">
        <h2>Key Statistics</h2>
        <div class="stats-grid">
            <div class="stat-box">
                <h4>Total Donations</h4>
                <div class="value">{total_donations}</div>
                <div class="subvalue">Across all parties and types</div>
            </div>
            <div class="stat-box">
                <h4>Number of Donations</h4>
                <div class="value">{num_donations:,}</div>
                <div class="subvalue">Individual donation records</div>
            </div>
            <div class="stat-box">
                <h4>Unique Donors</h4>
                <div class="value">{num_donors:,}</div>
                <div class="subvalue">Individual or corporate donors</div>
            </div>
            <div class="stat-box">
                <h4>Average Donation</h4>
                <div class="value">{avg_donation}</div>
                <div class="subvalue">Mean donation value</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>Donation Analytics</h2>
        <div class="chart-container">
            {visualization}
        </div>
    </div>
    
    <div class="section">
        <h2>Donation Types</h2>
        <p>Understand the different categories of political donations:</p>
        <div style="margin: 15px 0;">
            <div style="margin: 10px 0;">
                <span class="badge badge-cash">Cash</span> Direct monetary contributions to political parties
            </div>
            <div style="margin: 10px 0;">
                <span class="badge badge-non-cash">Non-Cash</span> In-kind donations (goods, services, resources)
            </div>
            <div style="margin: 10px 0;">
                <span class="badge badge-sponsorship">Sponsorship</span> Funding for party events and activities
            </div>
            <div style="margin: 10px 0;">
                <span class="badge badge-public-fund">Public Fund</span> State-funded donations or grants
            </div>
            <div style="margin: 10px 0;">
                <span class="badge badge-bequest">Bequest</span> Donations from wills and legacies
            </div>
            <div style="margin: 10px 0;">
                <span class="badge badge-other">Other</span> Miscellaneous donation types
            </div>
        </div>
    </div>
    
    <div class="insight">
        <h3>Key Insights</h3>
        <ul style="margin: 10px 0; padding-left: 20px;">
            <li>Political donations form a critical part of party financing in the UK</li>
            <li>Individual donors and corporate entities contribute across different donation types</li>
            <li>Donation patterns can reveal funding priorities and party strategies</li>
            <li>Transparency in donations is essential for democratic accountability</li>
        </ul>
    </div>
    """.format(
        total_donations=format_currency(total_donations),
        num_donations=num_donations,
        num_donors=num_donors,
        avg_donation=format_currency(avg_donation),
        visualization=chart_html
    )
    
    # Use formatting reference to generate styled HTML
    styled_html = get_political_donations_styled_html(
        title="UK Political Donations - Summary Dashboard",
        subtitle="Comprehensive Analysis of Political Funding Landscape",
        body_content=body_content,
        include_legend=True
    )
    
    output_path = OUTPUT_DIR / 'political_donations_summary_dashboard.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(styled_html)
    
    print(f"✓ Summary dashboard created: {output_path}")
    return output_path

def load_donations_data():
    """Load political donations data"""
    try:
        # Try multiple possible data source locations
        potential_paths = [
            Path(__file__).parent.parent / 'data_sources' / 'dashboard_demo_readonly' / 'output' / 'cleaned_donations.csv',
            Path(__file__).parent.parent / 'data_sources' / 'political_donations.csv',
            Path(__file__).parent.parent / 'generated_charts' / 'political_donations.csv',
        ]
        
        for path in potential_paths:
            if path.exists():
                print(f"  Loading data from: {path}")
                df = pd.read_csv(path)
                # Ensure date column is datetime
                if 'donation_date' in df.columns:
                    df['donation_date'] = pd.to_datetime(df['donation_date'])
                elif 'Date' in df.columns:
                    df.rename(columns={'Date': 'donation_date'}, inplace=True)
                    df['donation_date'] = pd.to_datetime(df['donation_date'])
                return df
        
        print("⚠ Political donations data file not found")
        return None
    except Exception as e:
        print(f"⚠ Error loading donations data: {e}")
        return None

if __name__ == '__main__':
    print("Loading political donations data...")
    donations_df = load_donations_data()
    
    if donations_df is not None and len(donations_df) > 0:
        print("Creating summary dashboard...")
        create_summary_dashboard(donations_df)
        print("\n✓ Political donations summary dashboard complete!")
    else:
        print("\n⚠ No donations data available for dashboard")
