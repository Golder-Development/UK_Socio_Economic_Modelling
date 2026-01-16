"""
CORRECTED ANALYSIS: Final Year Before Election - Month-by-Month
Tests the election pension theory using actual election dates,
not calendar-based quarters.
"""

import pandas as pd
import numpy as np
from datetime import timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Load data
print("Loading cabinet ministers data...")
df = pd.read_csv('data_sources/parliament/most recent extract/cabinet_ministers.csv', parse_dates=['start_date', 'end_date'])

# Filter for senior cabinet posts (Commons only, non-PM)
senior_keywords = ['secretary of state', 'chancellor', 'lord chancellor', 
                   'chief secretary', 'lord president', 'minister without portfolio']

df['post_lower'] = df['post'].str.lower()
df['is_senior'] = df['post_lower'].str.contains('|'.join(senior_keywords), na=False)
df['is_commons'] = df['member_house'] == 'Commons'
df['is_pm'] = df['post'].str.lower().str.contains('prime minister', na=False)

senior_df = df[(df['is_senior']) & (df['is_commons']) & (~df['is_pm'])].copy()

# Calculate tenure in years
senior_df['tenure_years'] = senior_df['tenure_length_days'] / 365.25

# Get unique elections (from the election_cycle_analysis if it exists)
elections = [
    pd.Timestamp('1970-06-18'), pd.Timestamp('1974-02-28'), pd.Timestamp('1974-10-10'),
    pd.Timestamp('1979-05-03'), pd.Timestamp('1983-06-09'), pd.Timestamp('1987-06-11'),
    pd.Timestamp('1992-04-09'), pd.Timestamp('1997-05-01'), pd.Timestamp('2001-06-07'),
    pd.Timestamp('2005-05-05'), pd.Timestamp('2010-05-06'), pd.Timestamp('2015-05-07'),
    pd.Timestamp('2017-06-08'), pd.Timestamp('2019-12-12'), pd.Timestamp('2024-07-04'),
]

print(f"\nAnalyzing {len(senior_df)} senior cabinet posts across {len(elections)} elections")

# For each election, look at the final year
final_year_results = []
first_timers_by_election = {}

for election_idx, election_date in enumerate(elections):
    election_year = election_date.year
    
    # Final year = 12 months before election
    final_year_start = election_date - timedelta(days=365)
    
    # Get appointments in final year
    final_year_appts = senior_df[
        (senior_df['start_date'] >= final_year_start) & 
        (senior_df['start_date'] < election_date)
    ].copy()
    
    if len(final_year_appts) == 0:
        continue
    
    # Calculate months before election for each appointment
    final_year_appts['months_before_election'] = (
        (election_date - final_year_appts['start_date']).dt.days / 30.44
    )
    
    # Identify first-timers (people with no prior cabinet service before this appointment)
    unique_people_final_year = final_year_appts['person_id'].unique()
    
    # Get all appointments for these people BEFORE the final year
    prior_appts = senior_df[
        (senior_df['person_id'].isin(unique_people_final_year)) &
        (senior_df['start_date'] < final_year_start)
    ]
    
    # First-timers are those with no prior appointments
    prior_appt_people = prior_appts['person_id'].unique()
    first_timers = final_year_appts[~final_year_appts['person_id'].isin(prior_appt_people)]
    
    # Store first-timer data
    first_timers_by_election[election_date.strftime('%Y-%m-%d')] = {
        'election_date': election_date,
        'first_timers': first_timers,
        'all_appointments': final_year_appts,
    }
    
    # Break final year into months and count
    for month_range in [12, 9, 6, 3, 1]:  # 12-9 months, 9-6 months, 6-3 months, 3-1 months, <1 month
        if month_range == 12:
            month_label = "12-9 months before"
            start_days = 365
            end_days = 275
        elif month_range == 9:
            month_label = "9-6 months before"
            start_days = 275
            end_days = 183
        elif month_range == 6:
            month_label = "6-3 months before"
            start_days = 183
            end_days = 91
        elif month_range == 3:
            month_label = "3-1 months before"
            start_days = 91
            end_days = 30
        else:
            month_label = "<1 month before"
            start_days = 30
            end_days = 0
        
        period_appts = final_year_appts[
            (final_year_appts['months_before_election'] >= end_days/30.44) &
            (final_year_appts['months_before_election'] < start_days/30.44)
        ]
        
        period_first_timers = period_appts[~period_appts['person_id'].isin(prior_appt_people)]
        
        if len(period_appts) > 0:
            final_year_results.append({
                'election_date': election_date,
                'election_year': election_year,
                'time_period': month_label,
                'total_appointments': len(period_appts),
                'unique_people': period_appts['person_id'].nunique(),
                'first_timers': len(period_first_timers),
                'avg_tenure_years': period_appts['tenure_years'].mean(),
                'short_tenures_pct': (period_appts['tenure_years'] < 1.0).sum() / len(period_appts) * 100,
            })

# Create results dataframe
results_df = pd.DataFrame(final_year_results)

print("\n" + "="*100)
print("FINAL YEAR BEFORE ELECTION - MONTH-BY-MONTH ANALYSIS")
print("="*100)

for election_date in elections:
    election_data = results_df[results_df['election_date'] == election_date]
    if len(election_data) > 0:
        print(f"\n{election_date.strftime('%B %Y')} Election ({election_date.strftime('%Y-%m-%d')})")
        print("-" * 100)
        for _, row in election_data.iterrows():
            print(f"  {row['time_period']:20s}: {row['total_appointments']:2.0f} appts, "
                  f"{row['unique_people']:2.0f} unique people, "
                  f"{row['first_timers']:2.0f} first-timers, "
                  f"avg tenure {row['avg_tenure_years']:5.2f} yrs, "
                  f"{row['short_tenures_pct']:5.1f}% <1yr")

# Aggregate across all elections
print("\n" + "="*100)
print("AGGREGATE: All Elections Combined")
print("="*100)

agg_summary = results_df.groupby('time_period').agg({
    'total_appointments': 'sum',
    'unique_people': 'sum',
    'first_timers': 'sum',
    'avg_tenure_years': 'mean',
    'short_tenures_pct': 'mean',
}).reset_index()

# Ensure correct order
period_order = ["12-9 months before", "9-6 months before", "6-3 months before", 
                "3-1 months before", "<1 month before"]
agg_summary['period_order'] = agg_summary['time_period'].map({p: i for i, p in enumerate(period_order)})
agg_summary = agg_summary.sort_values('period_order')

print("\nTime Period              | Total Appts | Unique People | First-Timers | Avg Tenure | Short Tenures")
print("-" * 100)
for _, row in agg_summary.iterrows():
    print(f"{row['time_period']:24s} | {row['total_appointments']:11.0f} | "
          f"{row['unique_people']:13.0f} | {row['first_timers']:12.0f} | "
          f"{row['avg_tenure_years']:10.2f} | {row['short_tenures_pct']:13.1f}%")

# Count first-timers by party in final 3 months
print("\n" + "="*100)
print("FIRST-TIMERS BY PARTY - Final 3 Months Before Election")
print("="*100)

final_3m_first_timers = results_df[
    results_df['time_period'].isin(['3-1 months before', '<1 month before'])
]

all_final_3m_appts = []
for election_date in elections:
    final_year_start = election_date - timedelta(days=365)
    final_3m_start = election_date - timedelta(days=91)
    
    appts_3m = senior_df[
        (senior_df['start_date'] >= final_3m_start) & 
        (senior_df['start_date'] < election_date)
    ].copy()
    
    if len(appts_3m) == 0:
        continue
    
    # Check if first-timer
    prior_appts = senior_df[
        (senior_df['person_id'].isin(appts_3m['person_id'].unique())) &
        (senior_df['start_date'] < final_year_start)
    ]
    prior_people = prior_appts['person_id'].unique()
    
    appts_3m['is_first_timer'] = ~appts_3m['person_id'].isin(prior_people)
    appts_3m['election_date'] = election_date
    all_final_3m_appts.append(appts_3m)

if all_final_3m_appts:
    final_3m_df = pd.concat(all_final_3m_appts, ignore_index=True)
    
    # Count by party
    first_timers_3m = final_3m_df[final_3m_df['is_first_timer']]
    party_counts = first_timers_3m['party'].value_counts()
    
    print("\nFirst-Timers in Final 3 Months by Party:")
    print("-" * 100)
    for party, count in party_counts.items():
        total_3m = len(final_3m_df[final_3m_df['party'] == party])
        pct = (count / total_3m * 100) if total_3m > 0 else 0
        print(f"  {party:30s}: {count:3.0f} first-timers out of {total_3m:3.0f} total ({pct:5.1f}%)")

# Save results
results_df.to_csv('generated_charts/final_year_analysis.csv', index=False)
print(f"\n✓ Saved: generated_charts/final_year_analysis.csv")

# Create visualization
print("\nGenerating visualization...")
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        'Total Appointments by Month',
        'First-Timers by Month',
        'Average Tenure by Month',
        'First-Timers as % of All Appointments'
    ),
    specs=[[{'secondary_y': False}, {'secondary_y': False}],
           [{'secondary_y': False}, {'secondary_y': False}]]
)

# Use the aggregate summary
agg_summary_sorted = agg_summary.sort_values('period_order')
periods = agg_summary_sorted['time_period'].tolist()
colors = ['#4caf50', '#8bc34a', '#ffc107', '#ff9800', '#d32f2f']

fig.add_trace(
    go.Bar(x=periods, y=agg_summary_sorted['total_appointments'], 
           marker=dict(color=colors), name='Total Appointments',
           text=agg_summary_sorted['total_appointments'], textposition='auto'),
    row=1, col=1
)

fig.add_trace(
    go.Bar(x=periods, y=agg_summary_sorted['first_timers'], 
           marker=dict(color=colors), name='First-Timers',
           text=agg_summary_sorted['first_timers'], textposition='auto'),
    row=1, col=2
)

fig.add_trace(
    go.Bar(x=periods, y=agg_summary_sorted['avg_tenure_years'], 
           marker=dict(color=colors), name='Avg Tenure',
           text=agg_summary_sorted['avg_tenure_years'].round(2), textposition='auto'),
    row=2, col=1
)

# Calculate first-timers percentage
agg_summary_sorted['first_timers_pct'] = (
    agg_summary_sorted['first_timers'] / agg_summary_sorted['total_appointments'] * 100
)

fig.add_trace(
    go.Bar(x=periods, y=agg_summary_sorted['first_timers_pct'], 
           marker=dict(color=colors), name='First-Timer %',
           text=agg_summary_sorted['first_timers_pct'].round(1), textposition='auto'),
    row=2, col=2
)

fig.update_yaxes(title_text="Count", row=1, col=1)
fig.update_yaxes(title_text="Count", row=1, col=2)
fig.update_yaxes(title_text="Years", row=2, col=1)
fig.update_yaxes(title_text="Percentage", row=2, col=2)

fig.update_layout(
    height=700,
    title_text="Cabinet Appointments in Final Year Before Election",
    showlegend=False,
    hovermode='x unified'
)

# Save with proper path handling for GitHub Pages compatibility
from pathlib import Path
output_dir = Path(__file__).parent.parent / "generated_charts"
output_path = output_dir / "final_year_pension_analysis.html"
fig.write_html(str(output_path), include_plotlyjs='cdn')
print(f"✓ Saved: {output_path}")

print("\n✓ Analysis complete!")
