"""
Interactive visualization of Cabinet Ministers tenure vs parliament duration.

Creates a scatter plot with Plotly showing:
- X-axis: Parliament length in days
- Y-axis: Tenure length in days
- Color: Political party
- Filters: Parliament session selection and House (Commons/Lords/Both)
"""

import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import numpy as np
import sys

# Import classification logic
sys.path.insert(0, str(Path(__file__).parent))
from cabinet_post_classifier import classify_post

# --- Configuration ----------------------------------------------------------
MIN_YEAR = 1966  # Only analyze data from this year onwards


def create_tenure_visualization():
    """Create interactive scatter plot of tenure vs parliament duration."""
    
    # Load the most recent cabinet ministers dataset
    extract_dir = sorted(Path('data_sources/parliament').glob('extract_*'), 
                        key=lambda p: p.stat().st_mtime)[-1]
    csv_file = extract_dir / 'cabinet_ministers.csv'
    
    print(f"Loading data from: {csv_file}")
    df = pd.read_csv(csv_file)
    
    # Convert dates
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date'] = pd.to_datetime(df['end_date'])
    df['parliament_start_date'] = pd.to_datetime(df['parliament_start_date'])
    
    # Convert numeric columns
    df['tenure_length_days'] = pd.to_numeric(df['tenure_length_days'], errors='coerce')
    df['parliament_length_days'] = pd.to_numeric(df['parliament_length_days'], errors='coerce')
    
    # Create parliament year for filtering
    df['parliament_year'] = df['parliament_start_date'].dt.year
    
    # Create parliament label
    df['parliament_label'] = (df['parliament_year'].astype(str) + 
        ' (' + df['parliament_start_date'].dt.strftime('%Y-%m-%d') + ')')
    
    # Remove rows with missing tenure or parliament data
    df_clean = df.dropna(subset=['tenure_length_days', 'parliament_length_days', 'parliament_start_date'])
    
    # Filter to MIN_YEAR onwards
    df_clean = df_clean[df_clean['parliament_year'] >= MIN_YEAR].reset_index(drop=True)
    print(f"Filtering to {MIN_YEAR} onwards")
    
    # Apply classification to identify senior posts
    print("Classifying posts...")
    classifications = df_clean['post'].apply(lambda p: classify_post(p, {}))
    df_clean['is_senior'] = classifications.apply(lambda c: c.is_senior)
    df_clean['post_category'] = classifications.apply(lambda c: c.category)
    
    print(f"Total records after filtering: {len(df_clean)}")
    print(f"  Senior posts: {df_clean['is_senior'].sum()}")
    print(f"  Non-senior posts: {(~df_clean['is_senior']).sum()}")
    print(f"Parliament sessions: {df_clean['parliament_label'].nunique()}")
    print(f"Parties: {df_clean['party'].unique()}")
    
    # Define party colors
    party_colors = {
        'Labour': '#E4003B',
        'Conservative': '#0087DC',
        'Liberal Democrat': '#FAA61A',
        'Crossbench': '#999999',
        'Other': '#CCCCCC'
    }
    
    # Get all unique parliaments
    parliaments = sorted(df_clean['parliament_label'].unique())
    
    # Create figure
    fig = go.Figure()
    
    # Get all unique parties
    parties = sorted(df_clean['party'].dropna().unique())
    
    # Create traces for each party
    # We'll create all combinations of party + house to enable flexible filtering
    trace_info = []  # Will store (party, house) tuples for each trace
    
    for party in parties:
        for house in ['Commons', 'Lords']:
            party_house_data = df_clean[(df_clean['party'] == party) & (df_clean['member_house'] == house)]
            
            if len(party_house_data) == 0:
                continue  # Skip if no data for this combination
            
            color = party_colors.get(party, '#999999')
            # Adjust opacity for Lords (make slightly more transparent)
            opacity = 0.5 if house == 'Lords' else 0.7
            line_width = 0.5 if house == 'Lords' else 1
            
            # Create marker symbol distinction
            marker_symbol = 'circle' if house == 'Commons' else 'diamond'
            
            fig.add_trace(go.Scatter(
                x=party_house_data['parliament_length_days'],
                y=party_house_data['tenure_length_days'],
                mode='markers',
                name=f"{party} ({house})",
                marker=dict(
                    size=8,
                    color=color,
                    opacity=opacity,
                    line=dict(width=line_width, color='white'),
                    symbol=marker_symbol
                ),
                text=[
                    f"<b>{row['given_name']} {row['family_name']}</b><br>" +
                    f"House: <b>{row['member_house']}</b><br>" +
                    f"Post: {row['post']}<br>" +
                    f"Tenure: {row['tenure_length_days']:.0f} days ({row['tenure_length_days']/30:.1f} months)<br>" +
                    f"Parliament: {row['parliament_year']}<br>" +
                    f"Parliament Duration: {row['parliament_length_days']:.0f} days ({row['parliament_length_days']/365:.1f} years)<br>" +
                    f"PM: {row['prime_minister']}<br>" +
                    f"Party: {row['party']}"
                    for _, row in party_house_data.iterrows()
                ],
                hovertemplate='%{text}<extra></extra>',
                visible=True,
                legendgroup=f"{party}_{house}",
                showlegend=True
            ))
            
            trace_info.append((party, house))
    
    # Create buttons for parliament filtering combined with house filtering
    parliament_buttons = []
    house_buttons = []
    
    # First set: Parliament filter (house will default to "Both")
    for parliament_label in (['All Parliaments'] + list(parliaments)):
        visibility = []
        
        for party, house in trace_info:
            if parliament_label == 'All Parliaments':
                # Show all data
                has_data = True
            else:
                # Check if this party-house combination has data in this parliament
                mask = (df_clean['party'] == party) & (df_clean['member_house'] == house) & (df_clean['parliament_label'] == parliament_label)
                has_data = mask.any()
            
            visibility.append(has_data)
        
        title_text = f'Cabinet Ministers: Tenure vs Parliament Duration ({parliament_label})'
        
        parliament_buttons.append(
            dict(
                label=parliament_label,
                method='update',
                args=[
                    {'visible': visibility},
                    {'title.text': title_text}
                ]
            )
        )
    
    # Second set: House filter (will show all parliaments)
    for house_filter in ['Both', 'Commons', 'Lords']:
        visibility = []
        
        for party, house in trace_info:
            if house_filter == 'Both':
                has_data = True
            else:
                has_data = (house == house_filter)
            
            visibility.append(has_data)
        
        house_buttons.append(
            dict(
                label=house_filter,
                method='update',
                args=[
                    {'visible': visibility},
                    {}
                ]
            )
        )
    
    # Update layout with both dropdown menus
    fig.update_layout(
        updatemenus=[
            # Parliament filter dropdown
            dict(
                active=0,
                buttons=parliament_buttons,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.0,
                xanchor="left",
                y=1.15,
                yanchor="top",
                bgcolor='#f0f0f0',
                bordercolor='#999999',
                borderwidth=1,
                name='Parliament'
            ),
            # House filter dropdown
            dict(
                active=0,
                buttons=house_buttons,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.25,
                xanchor="left",
                y=1.15,
                yanchor="top",
                bgcolor='#e8f4f8',
                bordercolor='#0087DC',
                borderwidth=1,
                name='House'
            )
        ],
        title=dict(
            text='Cabinet Ministers: Tenure vs Parliament Duration (All Parliaments)',
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title='Parliament Duration (days)',
            showgrid=True,
            gridwidth=1,
            gridcolor='#f0f0f0',
            zeroline=False
        ),
        yaxis=dict(
            title='Ministerial Tenure (days)',
            showgrid=True,
            gridwidth=1,
            gridcolor='#f0f0f0',
            zeroline=False
        ),
        hovermode='closest',
        plot_bgcolor='white',
        paper_bgcolor='white',
        width=1200,
        height=700,
        font=dict(family='Arial, sans-serif', size=11),
        legend=dict(
            x=1.02,
            y=1,
            xanchor='left',
            yanchor='top',
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='#999999',
            borderwidth=1
        ),
        margin=dict(l=80, r=200, t=180, b=80)
    )
    
    # Add annotations
    fig.add_annotation(
        text=f"Total appointments: {len(df_clean)} | Unique ministers: {df_clean['mnis_id'].nunique()} | " +
             f"Parliaments: {df_clean['parliament_label'].nunique()} | " +
             f"Commons: {len(df_clean[df_clean['member_house'] == 'Commons'])} | Lords: {len(df_clean[df_clean['member_house'] == 'Lords'])}",
        xref="paper", yref="paper",
        x=0.0, y=-0.08,
        showarrow=False,
        font=dict(size=10, color='#666666'),
        xanchor='left'
    )
    
    # Add labels for the dropdown menus
    fig.add_annotation(
        text="<b>Filter by Parliament:</b>",
        xref="paper", yref="paper",
        x=0.0, y=1.20,
        showarrow=False,
        font=dict(size=11, color='#333333'),
        xanchor='left',
        yanchor='bottom'
    )
    
    fig.add_annotation(
        text="<b>Filter by House:</b>",
        xref="paper", yref="paper",
        x=0.25, y=1.20,
        showarrow=False,
        font=dict(size=11, color='#0087DC'),
        xanchor='left',
        yanchor='bottom'
    )
    
    # Save to HTML
    output_dir = Path('generated_charts')
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'cabinet_ministers_tenure_parliament_{timestamp}.html'
    
    fig.write_html(str(output_file))
    print(f"\n✓ Interactive visualization saved to: {output_file}")
    
    return fig, output_file


def create_summary_statistics(df):
    """Print summary statistics about the visualization."""
    df['tenure_length_days'] = pd.to_numeric(df['tenure_length_days'], errors='coerce')
    df['parliament_length_days'] = pd.to_numeric(df['parliament_length_days'], errors='coerce')
    
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    print(f"\nHouse Distribution:")
    house_counts = df['member_house'].value_counts()
    for house, count in house_counts.items():
        pct = (count / len(df)) * 100
        print(f"  {house}: {count} ({pct:.1f}%)")
    
    print(f"\nTenure Statistics:")
    print(f"  Average: {df['tenure_length_days'].mean():.0f} days (~{df['tenure_length_days'].mean()/30:.1f} months)")
    print(f"  Median: {df['tenure_length_days'].median():.0f} days")
    print(f"  Min: {df['tenure_length_days'].min():.0f} days")
    print(f"  Max: {df['tenure_length_days'].max():.0f} days (~{df['tenure_length_days'].max()/365:.1f} years)")
    
    print(f"\nParliament Duration Statistics:")
    print(f"  Average: {df['parliament_length_days'].mean():.0f} days (~{df['parliament_length_days'].mean()/365:.2f} years)")
    print(f"  Median: {df['parliament_length_days'].median():.0f} days")
    print(f"  Min: {df['parliament_length_days'].min():.0f} days")
    print(f"  Max: {df['parliament_length_days'].max():.0f} days (~{df['parliament_length_days'].max()/365:.2f} years)")
    
    print(f"\nParty Distribution:")
    party_counts = df['party'].value_counts()
    for party, count in party_counts.items():
        pct = (count / len(df)) * 100
        print(f"  {party}: {count} ({pct:.1f}%)")


def main():
    """Main entry point."""
    print("\n=== Cabinet Ministers Tenure vs Parliament Duration Visualization ===\n")
    
    # Create visualization
    fig, output_file = create_tenure_visualization()
    
    # Load data for summary statistics
    extract_dir = sorted(Path('data_sources/parliament').glob('extract_*'), 
                        key=lambda p: p.stat().st_mtime)[-1]
    csv_file = extract_dir / 'cabinet_ministers.csv'
    df = pd.read_csv(csv_file)
    
    # Print summary statistics
    create_summary_statistics(df)
    
    print("\n" + "="*80)
    print("✓ Visualization complete!")
    print(f"Open {output_file} in a web browser to explore the interactive chart.")
    print("="*80)


if __name__ == "__main__":
    main()
