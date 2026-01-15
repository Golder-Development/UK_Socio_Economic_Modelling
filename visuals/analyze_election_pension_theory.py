"""
Analysis of Cabinet Appointments Around Parliamentary Elections
Theory: Governments may increase cabinet appointments and shorten tenures near election dates
to ensure more senior members qualify for cabinet pensions before losing office.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from pathlib import Path

# Configuration
DATA_FILE = Path("data_sources/parliament/most recent extract/cabinet_ministers.csv")
OUTPUT_DIR = Path("generated_charts")

def load_cabinet_data():
    """Load and clean cabinet ministers data."""
    df = pd.read_csv(DATA_FILE)
    
    # Parse dates
    for date_col in ['start_date', 'end_date', 'parliament_start_date']:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    # Calculate years into parliament
    df['parliament_start_year'] = df['parliament_start_date'].dt.year
    df['years_into_parliament'] = (df['start_date'] - df['parliament_start_date']).dt.days / 365.25
    df['tenure_days'] = pd.to_numeric(df['tenure_length_days'], errors='coerce')
    df['tenure_years'] = df['tenure_days'] / 365.25
    
    return df

def prepare_ministers_data(df):
    """Prepare all ministers data, marking senior cabinet roles and excluding PMs."""
    print("Preparing all ministers data...")
    
    # Filter for Commons only and exclude PMs
    def is_pm(post):
        if pd.isna(post):
            return False
        return 'prime minister' in str(post).lower()
    
    commons_df = df[(df['member_house'] == 'Commons') & ~df['post'].apply(is_pm)].copy()
    
    # Mark senior Cabinet posts
    def is_senior_cabinet(post):
        if pd.isna(post):
            return False
        post_str = str(post).lower()
        # Look for Secretary of State or other high-level positions
        senior_keywords = ['secretary of state', 'chancellor', 'lord chancellor', 
                          'chief secretary', 'lord president', 'minister without portfolio']
        return any(keyword in post_str for keyword in senior_keywords)
    
    commons_df['is_senior_cabinet'] = commons_df['post'].apply(is_senior_cabinet)
    
    print(f"Total Commons ministers (non-PM): {len(commons_df)}")
    print(f"Senior Cabinet posts: {commons_df['is_senior_cabinet'].sum()}")
    print(f"Other ministerial posts: {(~commons_df['is_senior_cabinet']).sum()}")
    
    return commons_df

def analyze_election_cycle_patterns(df):
    """Analyze patterns around parliamentary elections."""
    
    # Excluding Feb 1974 and 2017 as snap election anomalies
    elections = [
        ('1970-06-18', 'Conservative - Heath'),
        ('1974-10-10', 'Labour - Wilson'),
        ('1979-05-03', 'Conservative - Thatcher'),
        ('1983-06-09', 'Conservative - Thatcher'),
        ('1987-06-11', 'Conservative - Thatcher'),
        ('1992-04-09', 'Conservative - Major'),
        ('1997-05-01', 'Labour - Blair'),
        ('2001-06-07', 'Labour - Blair'),
        ('2005-05-05', 'Labour - Blair'),
        ('2010-05-06', 'Conservative - Cameron'),
        ('2015-05-07', 'Conservative - Cameron'),
        ('2019-12-12', 'Conservative - Johnson'),
        ('2024-07-04', 'Labour - Starmer'),
    ]
    
    results = []
    
    for election_date_str, party_leader in elections:
        election_date = pd.to_datetime(election_date_str)
        
        # Define periods: 6 months before, 6 months after, and full cycles
        six_months_before = election_date - pd.Timedelta(days=180)
        six_months_after = election_date + pd.Timedelta(days=180)
        one_year_before = election_date - pd.Timedelta(days=365)
        one_year_after = election_date + pd.Timedelta(days=365)
        
        # Count appointments and analyze tenure in each period
        before_6m = df[(df['start_date'] >= six_months_before) & (df['start_date'] < election_date)]
        after_6m = df[(df['start_date'] >= election_date) & (df['start_date'] < six_months_after)]
        before_1y = df[(df['start_date'] >= one_year_before) & (df['start_date'] < election_date)]
        
        results.append({
            'election_date': election_date,
            'party_leader': party_leader,
            'appointments_6m_before': len(before_6m),
            'avg_tenure_6m_before': before_6m['tenure_years'].mean() if len(before_6m) > 0 else np.nan,
            'appointments_6m_after': len(after_6m),
            'avg_tenure_6m_after': after_6m['tenure_years'].mean() if len(after_6m) > 0 else np.nan,
            'appointments_1y_before': len(before_1y),
            'avg_tenure_1y_before': before_1y['tenure_years'].mean() if len(before_1y) > 0 else np.nan,
            'unique_people_6m_before': before_6m['person_id'].nunique(),
            'unique_people_6m_after': after_6m['person_id'].nunique(),
        })
    
    return pd.DataFrame(results)

def analyze_per_election(df):
    """Analyze pension abuse patterns for each individual election."""
    
    # Identify one-time only appointees
    appointment_counts = df.groupby('person_id').size()
    one_time_only = appointment_counts[appointment_counts == 1].index
    df = df.copy()
    df['is_one_time_only'] = df['person_id'].isin(one_time_only)
    
    # Excluding Feb 1974, 2017 (snap election anomalies), and 2024 (still sitting)
    elections = [
        ('1970-06-18', 'Conservative - Heath'),
        ('1974-10-10', 'Labour - Wilson'),
        ('1979-05-03', 'Conservative - Thatcher'),
        ('1983-06-09', 'Conservative - Thatcher'),
        ('1987-06-11', 'Conservative - Thatcher'),
        ('1992-04-09', 'Conservative - Major'),
        ('1997-05-01', 'Labour - Blair'),
        ('2001-06-07', 'Labour - Blair'),
        ('2005-05-05', 'Labour - Blair'),
        ('2010-05-06', 'Conservative - Cameron'),
        ('2015-05-07', 'Conservative - Cameron'),
        ('2019-12-12', 'Conservative - Johnson'),
    ]
    
    results = []
    
    for election_date_str, party_leader in elections:
        election_date = pd.to_datetime(election_date_str)
        pension_era = 'Pre-2015' if election_date < pd.to_datetime('2015-05-07') else '2015+'
        
        # Appointments in final 3 months
        three_months_before = election_date - pd.Timedelta(days=90)
        final_3m = df[(df['start_date'] >= three_months_before) & (df['start_date'] < election_date)]
        pension_abusers_3m = final_3m[final_3m['is_one_time_only']]
        senior_3m = final_3m[final_3m['is_senior_cabinet']]
        senior_abusers_3m = final_3m[final_3m['is_senior_cabinet'] & final_3m['is_one_time_only']]
        
        # Appointments in final 6 months
        six_months_before = election_date - pd.Timedelta(days=180)
        final_6m = df[(df['start_date'] >= six_months_before) & (df['start_date'] < election_date)]
        pension_abusers_6m = final_6m[final_6m['is_one_time_only']]
        senior_6m = final_6m[final_6m['is_senior_cabinet']]
        senior_abusers_6m = final_6m[final_6m['is_senior_cabinet'] & final_6m['is_one_time_only']]
        
        # Appointments in final 9 months
        nine_months_before = election_date - pd.Timedelta(days=270)
        final_9m = df[(df['start_date'] >= nine_months_before) & (df['start_date'] < election_date)]
        pension_abusers_9m = final_9m[final_9m['is_one_time_only']]
        senior_9m = final_9m[final_9m['is_senior_cabinet']]
        senior_abusers_9m = final_9m[final_9m['is_senior_cabinet'] & final_9m['is_one_time_only']]
        
        # Appointments in final 12 months
        twelve_months_before = election_date - pd.Timedelta(days=365)
        final_12m = df[(df['start_date'] >= twelve_months_before) & (df['start_date'] < election_date)]
        pension_abusers_12m = final_12m[final_12m['is_one_time_only']]
        senior_12m = final_12m[final_12m['is_senior_cabinet']]
        senior_abusers_12m = final_12m[final_12m['is_senior_cabinet'] & final_12m['is_one_time_only']]
        
        results.append({
            'election_date': election_date,
            'year': election_date.year,
            'party_leader': party_leader,
            'party': party_leader.split(' - ')[0],
            'pension_era': pension_era,
            'appts_3m': len(final_3m),
            'senior_appts_3m': len(senior_3m),
            'pension_abusers_3m': len(pension_abusers_3m),
            'senior_abusers_3m': len(senior_abusers_3m),
            'pension_abuse_pct_3m': (len(pension_abusers_3m) / len(final_3m) * 100) if len(final_3m) > 0 else 0,
            'avg_tenure_3m': final_3m['tenure_years'].mean() if len(final_3m) > 0 else 0,
            'appts_6m': len(final_6m),
            'senior_appts_6m': len(senior_6m),
            'pension_abusers_6m': len(pension_abusers_6m),
            'senior_abusers_6m': len(senior_abusers_6m),
            'pension_abuse_pct_6m': (len(pension_abusers_6m) / len(final_6m) * 100) if len(final_6m) > 0 else 0,
            'avg_tenure_6m': final_6m['tenure_years'].mean() if len(final_6m) > 0 else 0,
            'appts_9m': len(final_9m),
            'senior_appts_9m': len(senior_9m),
            'pension_abusers_9m': len(pension_abusers_9m),
            'senior_abusers_9m': len(senior_abusers_9m),
            'pension_abuse_pct_9m': (len(pension_abusers_9m) / len(final_9m) * 100) if len(final_9m) > 0 else 0,
            'avg_tenure_9m': final_9m['tenure_years'].mean() if len(final_9m) > 0 else 0,
            'appts_12m': len(final_12m),
            'senior_appts_12m': len(senior_12m),
            'pension_abusers_12m': len(pension_abusers_12m),
            'senior_abusers_12m': len(senior_abusers_12m),
            'pension_abuse_pct_12m': (len(pension_abusers_12m) / len(final_12m) * 100) if len(final_12m) > 0 else 0,
            'avg_tenure_12m': final_12m['tenure_years'].mean() if len(final_12m) > 0 else 0,
        })
    
    return pd.DataFrame(results)

def analyze_by_months_to_election(df):
    """Analyze appointments by how close they were made to the election date.
    Focus on 'pension abusers' - people with only ONE cabinet appointment ever."""
    
    # First, identify people with only one cabinet appointment (true pension abusers)
    appointment_counts = df.groupby('person_id').size()
    one_time_only = appointment_counts[appointment_counts == 1].index
    
    df = df.copy()
    df['is_one_time_only'] = df['person_id'].isin(one_time_only)
    
    # Excluding Feb 1974, 2017 (snap election anomalies), and 2024 (still sitting)
    elections = [
        pd.to_datetime('1970-06-18'),
        pd.to_datetime('1974-10-10'),
        pd.to_datetime('1979-05-03'),
        pd.to_datetime('1983-06-09'),
        pd.to_datetime('1987-06-11'),
        pd.to_datetime('1992-04-09'),
        pd.to_datetime('1997-05-01'),
        pd.to_datetime('2001-06-07'),
        pd.to_datetime('2005-05-05'),
        pd.to_datetime('2010-05-06'),
        pd.to_datetime('2015-05-07'),
        pd.to_datetime('2019-12-12'),
    ]
    
    # Define time windows: appointments made in the final X months before election
    time_windows = [
        ('Last 1 month', 1),
        ('Last 3 months', 3),
        ('Last 6 months', 6),
        ('Last 12 months', 12),
        ('More than 12 months', None)
    ]
    
    results = []
    
    for election in elections:
        # Determine pension era based on election date
        pension_era = 'Pre-2015' if election < pd.to_datetime('2015-05-07') else '2015+'
        
        # For each time window, count appointments made in that final period
        for window_name, months_before in time_windows:
            if months_before is None:
                # More than 12 months before
                start_cutoff = None
                end_cutoff = election - pd.Timedelta(days=365)
            else:
                # Within X months of election
                start_cutoff = election - pd.Timedelta(days=months_before * 30.44)
                end_cutoff = election
            
            # Filter appointments in this window
            if start_cutoff is None:
                # All appointments more than 12 months before this election
                window_appts = df[(df['start_date'] < end_cutoff)]
            else:
                window_appts = df[(df['start_date'] >= start_cutoff) & (df['start_date'] < end_cutoff)]
            
            if len(window_appts) > 0:
                # Count pension abusers (one-time only appointees)
                pension_abusers = window_appts[window_appts['is_one_time_only']]
                
                results.append({
                    'election_date': election,
                    'pension_era': pension_era,
                    'time_window': window_name,
                    'months_before': months_before if months_before else 999,
                    'appointments': len(window_appts),
                    'avg_tenure_years': window_appts['tenure_years'].mean(),
                    'median_tenure_years': window_appts['tenure_years'].median(),
                    'unique_people': window_appts['person_id'].nunique(),
                    'short_tenures_count': (window_appts['tenure_years'] < 1.0).sum(),
                    'first_timers_count': window_appts['is_first_cabinet_appointment'].sum(),
                    'one_time_only_count': len(pension_abusers),
                    'one_time_only_avg_tenure': pension_abusers['tenure_years'].mean() if len(pension_abusers) > 0 else 0,
                })
    
    detail_df = pd.DataFrame(results)
    
    # Aggregate by pension era and time window
    summary = detail_df.groupby(['pension_era', 'time_window']).agg({
        'appointments': 'sum',
        'avg_tenure_years': 'mean',
        'unique_people': 'sum',
        'short_tenures_count': 'sum',
        'first_timers_count': 'sum',
        'one_time_only_count': 'sum',
        'one_time_only_avg_tenure': 'mean',
        'election_date': 'nunique'  # Count number of elections
    }).reset_index()
    
    # Rename election count column
    summary.rename(columns={'election_date': 'num_elections'}, inplace=True)
    
    # Calculate per-election rates for fair comparison
    summary['appts_per_election'] = (summary['appointments'] / summary['num_elections']).round(2)
    summary['one_time_per_election'] = (summary['one_time_only_count'] / summary['num_elections']).round(2)
    
    summary['short_tenures_pct'] = (summary['short_tenures_count'] / summary['appointments'] * 100)
    summary['first_timers_pct'] = (summary['first_timers_count'] / summary['appointments'] * 100)
    summary['one_time_only_pct'] = (summary['one_time_only_count'] / summary['appointments'] * 100)
    
    # Sort by pension era and time window order
    window_order = ['Last 1 month', 'Last 3 months', 'Last 6 months', 'Last 12 months', 'More than 12 months']
    summary['window_order'] = summary['time_window'].apply(lambda x: window_order.index(x) if x in window_order else 999)
    summary = summary.sort_values(['pension_era', 'window_order']).drop('window_order', axis=1)
    
    return summary, detail_df

def create_election_cycle_chart(election_analysis):
    """Create visualization of appointment patterns around elections."""
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Appointments Around Elections', 'Average Tenure Around Elections'),
        specs=[[{'secondary_y': False}], [{'secondary_y': False}]]
    )
    
    # Plot 1: Appointments
    x_labels = [f"{row['party_leader'][:20]}\n{pd.to_datetime(row['election_date']).year}" 
                for _, row in election_analysis.iterrows()]
    
    fig.add_trace(
        go.Bar(
            x=x_labels,
            y=election_analysis['appointments_6m_before'],
            name='6 months before',
            marker=dict(color='#ffcccc'),
            text=election_analysis['appointments_6m_before'],
            textposition='auto',
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=x_labels,
            y=election_analysis['appointments_6m_after'],
            name='6 months after',
            marker=dict(color='#ccccff'),
            text=election_analysis['appointments_6m_after'],
            textposition='auto',
        ),
        row=1, col=1
    )
    
    # Plot 2: Average tenure
    fig.add_trace(
        go.Scatter(
            x=x_labels,
            y=election_analysis['avg_tenure_6m_before'],
            name='Avg tenure (6m before)',
            mode='lines+markers',
            line=dict(color='#ff6666', width=2),
            marker=dict(size=8),
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=x_labels,
            y=election_analysis['avg_tenure_6m_after'],
            name='Avg tenure (6m after)',
            mode='lines+markers',
            line=dict(color='#6666ff', width=2),
            marker=dict(size=8),
        ),
        row=2, col=1
    )
    
    fig.update_yaxes(title_text="Number of Appointments", row=1, col=1)
    fig.update_yaxes(title_text="Average Tenure (years)", row=2, col=1)
    
    fig.update_layout(height=800, title_text="Cabinet Appointment Patterns Around UK Elections")
    
    return fig

def create_months_to_election_chart(summary_df):
    """Create visualization comparing pre-2015 vs 2015+ appointment patterns, highlighting pension abusers."""
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Total Appointments vs One-Time Only ("Pension Abusers")',
            'One-Time Only as % of Appointments',
            'Average Tenure: All vs One-Time Only',
            'Short Tenures (<1yr) %'
        ),
        specs=[[{'secondary_y': False}, {'secondary_y': False}],
               [{'secondary_y': False}, {'secondary_y': False}]]
    )
    
    # Define window order
    window_order = ['Last 1 month', 'Last 3 months', 'Last 6 months', 'Last 12 months', 'More than 12 months']
    
    # Pre-2015 data
    pre_2015 = summary_df[summary_df['pension_era'] == 'Pre-2015'].copy()
    pre_2015['time_window'] = pd.Categorical(pre_2015['time_window'], categories=window_order, ordered=True)
    pre_2015 = pre_2015.sort_values('time_window')
    
    # 2015+ data
    post_2015 = summary_df[summary_df['pension_era'] == '2015+'].copy()
    post_2015['time_window'] = pd.Categorical(post_2015['time_window'], categories=window_order, ordered=True)
    post_2015 = post_2015.sort_values('time_window')
    
    # Plot 1: Total appointments vs one-time only
    fig.add_trace(
        go.Bar(x=pre_2015['time_window'], y=pre_2015['appointments'], 
               name='Pre-2015 Total', marker=dict(color='#ffcccc'),
               text=pre_2015['appointments'], textposition='auto'),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(x=pre_2015['time_window'], y=pre_2015['one_time_only_count'],
               name='Pre-2015 One-Time', marker=dict(color='#ff0000'),
               text=pre_2015['one_time_only_count'], textposition='auto'),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(x=post_2015['time_window'], y=post_2015['appointments'],
               name='2015+ Total', marker=dict(color='#ccccff'),
               text=post_2015['appointments'], textposition='auto'),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(x=post_2015['time_window'], y=post_2015['one_time_only_count'],
               name='2015+ One-Time', marker=dict(color='#0000ff'),
               text=post_2015['one_time_only_count'], textposition='auto'),
        row=1, col=1
    )
    
    # Plot 2: One-time only percentage
    fig.add_trace(
        go.Bar(x=pre_2015['time_window'], y=pre_2015['one_time_only_pct'],
               name='Pre-2015', marker=dict(color='#ff9999'),
               text=pre_2015['one_time_only_pct'].round(1), textposition='auto',
               showlegend=False),
        row=1, col=2
    )
    fig.add_trace(
        go.Bar(x=post_2015['time_window'], y=post_2015['one_time_only_pct'],
               name='2015+', marker=dict(color='#9999ff'),
               text=post_2015['one_time_only_pct'].round(1), textposition='auto',
               showlegend=False),
        row=1, col=2
    )
    
    # Plot 3: Average tenure comparison
    fig.add_trace(
        go.Scatter(x=pre_2015['time_window'], y=pre_2015['avg_tenure_years'],
                   mode='lines+markers', name='Pre-2015 All',
                   line=dict(color='#ff9999', width=2, dash='solid'), marker=dict(size=8),
                   showlegend=False),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=pre_2015['time_window'], y=pre_2015['one_time_only_avg_tenure'],
                   mode='lines+markers', name='Pre-2015 One-Time',
                   line=dict(color='#cc0000', width=2, dash='dash'), marker=dict(size=8),
                   showlegend=False),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=post_2015['time_window'], y=post_2015['avg_tenure_years'],
                   mode='lines+markers', name='2015+ All',
                   line=dict(color='#9999ff', width=2, dash='solid'), marker=dict(size=8),
                   showlegend=False),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=post_2015['time_window'], y=post_2015['one_time_only_avg_tenure'],
                   mode='lines+markers', name='2015+ One-Time',
                   line=dict(color='#0000cc', width=2, dash='dash'), marker=dict(size=8),
                   showlegend=False),
        row=2, col=1
    )
    
    # Plot 4: Short tenures percentage
    fig.add_trace(
        go.Bar(x=pre_2015['time_window'], y=pre_2015['short_tenures_pct'],
               name='Pre-2015 (short)', marker=dict(color='#ff9999'),
               text=pre_2015['short_tenures_pct'].round(1), textposition='auto',
               showlegend=False),
        row=2, col=2
    )
    fig.add_trace(
        go.Bar(x=post_2015['time_window'], y=post_2015['short_tenures_pct'],
               name='2015+ (short)', marker=dict(color='#9999ff'),
               text=post_2015['short_tenures_pct'].round(1), textposition='auto',
               showlegend=False),
        row=2, col=2
    )
    
    fig.update_yaxes(title_text="Count", row=1, col=1)
    fig.update_yaxes(title_text="Percentage", row=1, col=2)
    fig.update_yaxes(title_text="Years", row=2, col=1)
    fig.update_yaxes(title_text="Percentage", row=2, col=2)
    
    fig.update_xaxes(tickangle=-45)
    
    fig.update_layout(
        height=900,
        title_text="Pension Abuse Analysis: One-Time Cabinet Appointees (Pre-2015 vs 2015+)",
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig

def create_parliamentary_phase_chart(phase_analysis):
    """Create visualization of patterns through parliamentary lifecycle."""
    
    if len(phase_analysis) == 0:
        # Create empty placeholder if no data
        fig = go.Figure()
        fig.add_annotation(text="No phase data available", xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Group by quarter across all parliaments
    quarter_summary = phase_analysis.groupby('quarter').agg({
        'appointments': 'mean',
        'avg_tenure_years': 'mean',
        'short_tenures_pct': 'mean',
    }).reset_index()
    
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=('Avg Appointments per Quarter', 'Avg Tenure by Quarter', 'Short Tenures % by Quarter')
    )
    
    quarters = ['Q1\n(Early)', 'Q2\n(Mid)', 'Q3\n(Mid)', 'Q4\n(Late)']
    colors = ['#90EE90', '#FFD700', '#FFA500', '#FF6347']
    
    fig.add_trace(
        go.Bar(x=quarters, y=quarter_summary['appointments'], marker=dict(color=colors),
               text=quarter_summary['appointments'].round(1), textposition='auto'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=quarters, y=quarter_summary['avg_tenure_years'], marker=dict(color=colors),
               text=quarter_summary['avg_tenure_years'].round(2), textposition='auto'),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Bar(x=quarters, y=quarter_summary['short_tenures_pct'], marker=dict(color=colors),
               text=quarter_summary['short_tenures_pct'].round(1), textposition='auto'),
        row=1, col=3
    )
    
    fig.update_yaxes(title_text="Count", row=1, col=1)
    fig.update_yaxes(title_text="Years", row=1, col=2)
    fig.update_yaxes(title_text="Percentage", row=1, col=3)
    
    fig.update_layout(height=500, title_text="Cabinet Appointments Through Parliamentary Lifecycle",
                     showlegend=False)
    
    return fig

def create_per_election_chart(per_election_df):
    """Create visualization showing pension abuse per election by party across multiple time windows."""
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Final 3 Months', 'Final 6 Months', 'Final 9 Months', 'Final 12 Months'),
        vertical_spacing=0.15,
        horizontal_spacing=0.1,
        specs=[[{'secondary_y': False}, {'secondary_y': False}], 
               [{'secondary_y': False}, {'secondary_y': False}]]
    )
    
    # Color by party
    party_colors = {
        'Conservative': '#0087DC',
        'Labour': '#E4003B'
    }
    
    # X-axis labels
    df = per_election_df.copy()
    df['label'] = df['year'].astype(str)
    
    # Time windows to plot
    time_windows = [
        ('3m', 1, 1),
        ('6m', 1, 2),
        ('9m', 2, 1),
        ('12m', 2, 2)
    ]
    
    for window, row, col in time_windows:
        # Filter data for elections with appointments in this window
        df_window = df[df[f'appts_{window}'] > 0].copy()
        
        if len(df_window) > 0:
            # Pre-2015 count for vertical line
            pre_2015_count = len(df_window[df_window['pension_era'] == 'Pre-2015'])
            
            # Plot bars by party
            for party in df_window['party'].unique():
                party_data = df_window[df_window['party'] == party]
                fig.add_trace(
                    go.Bar(
                        x=party_data['label'],
                        y=party_data[f'pension_abusers_{window}'],
                        name=party,
                        marker=dict(color=party_colors.get(party, '#999999')),
                        text=party_data[f'pension_abusers_{window}'],
                        textposition='auto',
                        showlegend=(row == 1 and col == 1),
                        legendgroup=party
                    ),
                    row=row, col=col
                )
            
            # Add vertical line at 2015 reform
            if pre_2015_count > 0:
                fig.add_vline(x=pre_2015_count - 0.5, line_dash="dash", line_color="red", 
                              opacity=0.5, row=row, col=col)
    
    # Update axes
    for row in [1, 2]:
        for col in [1, 2]:
            fig.update_yaxes(title_text="Pension Abusers", row=row, col=col)
            fig.update_xaxes(tickangle=-45, row=row, col=col)
    
    fig.update_layout(
        height=800,
        title_text="Pension Abuse by Election and Time Window (One-Time Cabinet Appointees)",
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig

def generate_html_report(election_analysis, months_summary, appointments_detail, per_election_df, 
                         per_election_chart, months_chart, election_chart):
    """Generate comprehensive HTML report with pension era comparisons."""
    
    # Convert charts to JSON
    per_election_json = per_election_chart.to_json()
    months_json = months_chart.to_json()
    election_json = election_chart.to_json()
    
    # Calculate key statistics
    avg_appt_before = election_analysis['appointments_6m_before'].mean()
    avg_appt_after = election_analysis['appointments_6m_after'].mean()
    change_pct = ((avg_appt_after - avg_appt_before) / avg_appt_before * 100) if avg_appt_before > 0 else 0
    
    avg_tenure_before = election_analysis['avg_tenure_6m_before'].mean()
    avg_tenure_after = election_analysis['avg_tenure_6m_after'].mean()
    tenure_change_pct = ((avg_tenure_after - avg_tenure_before) / avg_tenure_before * 100) if avg_tenure_before > 0 else 0
    
    # Pension era comparisons
    pre_2015 = months_summary[months_summary['pension_era'] == 'Pre-2015']
    post_2015 = months_summary[months_summary['pension_era'] == '2015+']
    
    # Compare final 6 months periods
    pre_2015_6m = pre_2015[pre_2015['time_window'] == 'Last 6 months']
    post_2015_6m = post_2015[post_2015['time_window'] == 'Last 6 months']
    
    # Compare final 12 months periods  
    pre_2015_12m = pre_2015[pre_2015['time_window'] == 'Last 12 months']
    post_2015_12m = post_2015[post_2015['time_window'] == 'Last 12 months']
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Election Pension Theory Analysis - Cabinet Appointments</title>
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
            .finding {{
                background: #fff9c4;
                border-left: 4px solid #f57f17;
                padding: 15px;
                margin: 15px 0;
                border-radius: 4px;
            }}
            .finding strong {{
                color: #f57f17;
            }}
            .reform-highlight {{
                background: #e3f2fd;
                border-left: 4px solid #1976d2;
                padding: 15px;
                margin: 15px 0;
                border-radius: 4px;
            }}
            .reform-highlight strong {{
                color: #0d47a1;
            }}
            .stat-box {{
                display: inline-block;
                background: #f5f5f5;
                padding: 15px 25px;
                margin: 10px 10px 10px 0;
                border-left: 4px solid #283593;
                border-radius: 4px;
                min-width: 200px;
            }}
            .stat-box h4 {{
                margin: 0 0 5px 0;
                color: #666;
                font-size: 0.9em;
                text-transform: uppercase;
            }}
            .stat-box .value {{
                font-size: 1.6em;
                font-weight: bold;
                color: #1a237e;
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
            .chart-container {{
                margin: 20px 0;
            }}
            .positive {{
                color: #d32f2f;
            }}
            .neutral {{
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Election Pension Theory Analysis</h1>
            <p>Do governments increase cabinet appointments as elections approach to secure pensions?</p>
            <p style="font-size: 0.95em; opacity: 0.8;">Analysis by months until election, comparing Pre-2015 vs 2015+ pension rules (1970-2024)</p>
        </div>
        
        <div class="section">
            <h2>Hypothesis & 2015 Pension Reform</h2>
            <p><strong>Election Pension Theory:</strong> When a government believes it may lose the next election, it may accelerate cabinet appointments and shorten individual tenures to ensure more senior members qualify for a cabinet pension.</p>
            
            <div class="reform-highlight">
                <strong>🔍 2015 Pension Reform:</strong> In 2015, the UK government reformed ministerial pensions, significantly reducing benefits. This provides a natural experiment:
                <ul>
                    <li><strong>Pre-2015:</strong> More generous pension terms may have incentivized "pension padding"</li>
                    <li><strong>2015+:</strong> Reduced pension benefits should decrease incentive for strategic appointments</li>
                </ul>
                <p><strong>Prediction:</strong> If the pension theory is valid, we should see a decline in "one-time only" appointments after 2015.</p>
            </div>
            
            <div class="finding">
                <strong>🎯 Focus on "Pension Abusers":</strong> The clearest signal of pension abuse would be ministers appointed ONCE and never again - people with only a single cabinet appointment in their entire career. These "one-and-done" ministers are the most suspicious:
                <ul>
                    <li>Never held cabinet office before</li>
                    <li>Never held cabinet office after</li>
                    <li>Likely appointed specifically to qualify for pension benefits</li>
                </ul>
            </div>
        </div>
        
        <div class="section">
            <h2>Key Findings: Pre-2015 vs 2015+ Comparison</h2>
            
            <h3>Final 6 Months Before Election</h3>"""
    
    if len(pre_2015_6m) > 0 and len(post_2015_6m) > 0:
        pre_appts = pre_2015_6m['appointments'].values[0]
        post_appts = post_2015_6m['appointments'].values[0]
        pre_one_time = pre_2015_6m['one_time_only_count'].values[0]
        post_one_time = post_2015_6m['one_time_only_count'].values[0]
        pre_one_time_pct = pre_2015_6m['one_time_only_pct'].values[0]
        post_one_time_pct = post_2015_6m['one_time_only_pct'].values[0]
        pre_short = pre_2015_6m['short_tenures_pct'].values[0]
        post_short = post_2015_6m['short_tenures_pct'].values[0]
        pre_first = pre_2015_6m['first_timers_pct'].values[0]
        post_first = post_2015_6m['first_timers_pct'].values[0]
        
        html += f"""
            <div class="stat-box">
                <h4>Pre-2015 ({int(pre_2015_6m['num_elections'].values[0])} elections)</h4>
                <div class="value">{pre_2015_6m['appts_per_election'].values[0]:.2f}</div>
                <p style="margin: 5px 0 0 0; font-size: 0.9em;">Appointments per election</p>
            </div>
            
            <div class="stat-box">
                <h4>Pre-2015 Pension Abusers</h4>
                <div class="value" style="color: #c62828;">{pre_2015_6m['one_time_per_election'].values[0]:.2f}</div>
                <p style="margin: 5px 0 0 0; font-size: 0.9em;">Per election ({pre_one_time_pct:.1f}%)</p>
            </div>
            
            <div class="stat-box">
                <h4>2015+ ({int(post_2015_6m['num_elections'].values[0])} elections)</h4>
                <div class="value">{post_2015_6m['appts_per_election'].values[0]:.2f}</div>
                <p style="margin: 5px 0 0 0; font-size: 0.9em;">Appointments per election</p>
            </div>
            
            <div class="stat-box">
                <h4>2015+ Pension Abusers</h4>
                <div class="value" style="color: #1565c0;">{post_2015_6m['one_time_per_election'].values[0]:.2f}</div>
                <p style="margin: 5px 0 0 0; font-size: 0.9em;">Per election ({post_one_time_pct:.1f}%)</p>
            </div>
            
            <br style="clear: both;">
            
            <div class="stat-box">
                <h4>Rate Change (per election)</h4>
                <div class="value"><span class="{('positive' if (post_2015_6m['one_time_per_election'].values[0] - pre_2015_6m['one_time_per_election'].values[0]) < 0 else 'neutral')}">{(post_2015_6m['one_time_per_election'].values[0] - pre_2015_6m['one_time_per_election'].values[0]):+.2f}</span></div>
                <p style="margin: 5px 0 0 0; font-size: 0.9em;">Pension abusers per election</p>
            </div>
            
            <div class="stat-box">
                <h4>As % of Appointments</h4>
                <div class="value"><span class="{'positive' if post_one_time_pct < pre_one_time_pct else 'neutral'}">{post_one_time_pct - pre_one_time_pct:+.1f}pp</span></div>
                <p style="margin: 5px 0 0 0; font-size: 0.9em;">Percentage point change</p>
            </div>
            
            <br style="clear: both;">
            
            <div class="reform-highlight">
                <strong>📊 Critical Finding:</strong> 
                {f"Pre-2015 averaged <strong>{pre_2015_6m['one_time_per_election'].values[0]:.2f}</strong> pension abusers per election ({pre_one_time_pct:.1f}% of appointments). "
                 f"2015+ averaged <strong>{post_2015_6m['one_time_per_election'].values[0]:.2f}</strong> pension abusers per election ({post_one_time_pct:.1f}% of appointments). "}
                {f"<strong style='color: #2e7d32;'>✓ SUPPORTS PENSION THEORY</strong> - Pension abusers declined by {abs(post_2015_6m['one_time_per_election'].values[0] - pre_2015_6m['one_time_per_election'].values[0]):.2f} per election ({abs(post_one_time_pct - pre_one_time_pct):.1f}pp) after reform."
                 if post_2015_6m['one_time_per_election'].values[0] < pre_2015_6m['one_time_per_election'].values[0] else
                 f"<strong style='color: #c62828;'>✗ CONTRADICTS PENSION THEORY</strong> - Pension abusers increased by {abs(post_2015_6m['one_time_per_election'].values[0] - pre_2015_6m['one_time_per_election'].values[0]):.2f} per election ({abs(post_one_time_pct - pre_one_time_pct):.1f}pp) after reform."}
            </div>
            
            <div class="finding">
                <strong>📈 Context: Overall Appointment Patterns (per election)</strong>
                <ul>
                    <li><strong>Volume:</strong> {pre_2015_6m['appts_per_election'].values[0]:.2f} per election (Pre-2015) vs {post_2015_6m['appts_per_election'].values[0]:.2f} (2015+) = {((post_2015_6m['appts_per_election'].values[0] - pre_2015_6m['appts_per_election'].values[0]) / pre_2015_6m['appts_per_election'].values[0] * 100):+.1f}% change</li>
                    <li><strong>Average Tenure:</strong> {pre_2015_6m['avg_tenure_years'].values[0]:.2f} years (Pre-2015) vs {post_2015_6m['avg_tenure_years'].values[0]:.2f} years (2015+)</li>
                    <li><strong>Short Tenures:</strong> {pre_short:.1f}% (Pre-2015) vs {post_short:.1f}% (2015+)</li>
                    <li><strong>First-Timers:</strong> {pre_first:.1f}% (Pre-2015) vs {post_first:.1f}% (2015+)</li>
                </ul>
            </div>"""
    
    html += """
            
            <h3>Appointment Timing Pattern Table</h3>
            <table>
                <tr>
                    <th>Time Window</th>
                    <th>Total Appts</th>
                    <th>One-Time Only</th>
                    <th>One-Time %</th>
                    <th>Avg Tenure</th>
                    <th>Short %</th>
                </tr>
"""
    
    # Group by pension era for better readability
    for era in ['Pre-2015', '2015+']:
        era_data = months_summary[months_summary['pension_era'] == era]
        if len(era_data) > 0:
            html += f"""
                <tr class="group-header">
                    <td colspan="6" style="background-color: #e8f4f8; font-weight: bold; text-align: left; padding: 10px;">
                        {era} Era
                    </td>
                </tr>
"""
            for _, row in era_data.iterrows():
                html += f"""
                <tr>
                    <td><strong>{row['time_window']}</strong></td>
                    <td>{int(row['appointments'])}</td>
                    <td><strong>{int(row['one_time_only_count'])}</strong></td>
                    <td>{row['one_time_only_pct']:.1f}%</td>
                    <td>{row['avg_tenure_years']:.2f}</td>
                    <td>{row['short_tenures_pct']:.1f}%</td>
                </tr>
"""
    
    html += """
            </table>
        </div>
        
        <div class="section">
            <h2>Breakdown by Individual Election</h2>
            <p>Pension abuse patterns for each parliament, showing appointments made in different time windows before each election:</p>
            
            <div class="chart-container" id="per-election-chart"></div>
            
            <h3>Per-Election Detail Table</h3>
            <table>
                <tr>
                    <th rowspan="2">Year</th>
                    <th rowspan="2">Party</th>
                    <th rowspan="2">Era</th>
                    <th colspan="2">Final 3 Months</th>
                    <th colspan="2">Final 6 Months</th>
                    <th colspan="2">Final 9 Months</th>
                    <th colspan="2">Final 12 Months</th>
                </tr>
                <tr>
                    <th>Appts</th>
                    <th>Abusers (%)</th>
                    <th>Appts</th>
                    <th>Abusers (%)</th>
                    <th>Appts</th>
                    <th>Abusers (%)</th>
                    <th>Appts</th>
                    <th>Abusers (%)</th>
                </tr>
"""
    
    for _, row in per_election_df.iterrows():
        html += f"""
                <tr>
                    <td><strong>{row['year']}</strong></td>
                    <td>{row['party']}</td>
                    <td>{row['pension_era']}</td>
                    <td>{int(row['appts_3m'])}</td>
                    <td><strong>{int(row['pension_abusers_3m'])}</strong> ({row['pension_abuse_pct_3m']:.1f}%)</td>
                    <td>{int(row['appts_6m'])}</td>
                    <td><strong>{int(row['pension_abusers_6m'])}</strong> ({row['pension_abuse_pct_6m']:.1f}%)</td>
                    <td>{int(row['appts_9m'])}</td>
                    <td><strong>{int(row['pension_abusers_9m'])}</strong> ({row['pension_abuse_pct_9m']:.1f}%)</td>
                    <td>{int(row['appts_12m'])}</td>
                    <td><strong>{int(row['pension_abusers_12m'])}</strong> ({row['pension_abuse_pct_12m']:.1f}%)</td>
                </tr>
"""
    
    html += """
            </table>
        </div>
        
        <div class="section">
            <h2>Conclusions</h2>
            <p>This analysis examines whether governments systematically accelerate cabinet appointments as elections approach, and whether the 2015 pension reform affected this behavior:</p>
            
            <ul>
                <li><strong>Proximity patterns:</strong> Analysis by months until election reveals distinct patterns in appointment timing.</li>
                <li><strong>Pension reform impact:</strong> Comparing pre-2015 vs 2015+ periods provides insight into whether pension incentives drove appointment behavior.</li>
                <li><strong>Short-tenure trends:</strong> The percentage of brief appointments in the final months indicates potential "pension padding" strategy.</li>
            </ul>
            
            <p><strong>Limitations:</strong></p>
            <ul>
                <li>Historical context (wars, economic crises, scandals) not accounted for</li>
                <li>Perceived election chances before the election unknown</li>
                <li>Changes in cabinet size over time</li>
                <li>Individual retirement vs. dismissal not distinguished</li>
                <li>Limited data points post-2015 (only 1 election: 2019)</li>
            </ul>
        </div>
        
        <script>
            var perElectionChart = {per_election_json};
            Plotly.newPlot('per-election-chart', perElectionChart.data, perElectionChart.layout, {{responsive: true}});
        </script>
    </body>
    </html>
    """
    
    return html

def main():
    print("Loading cabinet ministers data...")
    df = load_cabinet_data()
    
    print("Preparing all ministers data (Commons, non-PM)...")
    ministers_df = prepare_ministers_data(df)
    
    # Add first-timer detection
    print("Identifying first cabinet appointments...")
    person_first_appt = ministers_df.groupby('person_id')['start_date'].min().to_dict()
    ministers_df['is_first_cabinet_appointment'] = ministers_df.apply(
        lambda row: row['start_date'] == person_first_appt.get(row['person_id']), axis=1
    )
    
    print("Analyzing election cycle patterns...")
    election_analysis = analyze_election_cycle_patterns(ministers_df)
    print("\nElection cycle results:")
    print(election_analysis.to_string())
    
    print("\n\nAnalyzing per-election pension abuse...")
    per_election_df = analyze_per_election(ministers_df)
    print("\nPer-election analysis (showing all time windows + senior breakdown):")
    display_cols = ['year', 'party', 'appts_6m', 'senior_appts_6m', 'pension_abusers_6m', 'senior_abusers_6m', 
                    'appts_9m', 'senior_appts_9m', 'pension_abusers_9m', 'senior_abusers_9m']
    print(per_election_df[display_cols].to_string())
    
    print("\n\nAnalyzing by months to election (Pre-2015 vs 2015+)...")
    months_summary, appointments_detail = analyze_by_months_to_election(ministers_df)
    print("\nMonths-to-election analysis:")
    print(months_summary.to_string())
    
    # Create charts
    print("\nCreating per-election chart...")
    per_election_chart = create_per_election_chart(per_election_df)
    
    print("Creating months-to-election chart...")
    months_chart = create_months_to_election_chart(months_summary)
    
    print("Creating election cycle chart...")
    election_chart = create_election_cycle_chart(election_analysis)
    
    # Generate HTML report
    print("Generating HTML report...")
    html = generate_html_report(election_analysis, months_summary, appointments_detail, per_election_df,
                                per_election_chart, months_chart, election_chart)
    
    # Save files
    report_path = OUTPUT_DIR / "election_pension_theory_analysis.html"
    election_analysis.to_csv(OUTPUT_DIR / "election_cycle_analysis.csv", index=False)
    months_summary.to_csv(OUTPUT_DIR / "months_to_election_analysis.csv", index=False)
    appointments_detail.to_csv(OUTPUT_DIR / "appointments_detail.csv", index=False)
    per_election_df.to_csv(OUTPUT_DIR / "per_election_analysis.csv", index=False)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✓ Generated: {report_path}")
    print(f"✓ Generated: {OUTPUT_DIR / 'election_cycle_analysis.csv'}")
    print(f"✓ Generated: {OUTPUT_DIR / 'months_to_election_analysis.csv'}")
    print(f"✓ Generated: {OUTPUT_DIR / 'appointments_detail.csv'}")
    
    # Print summary statistics
    print("\n" + "="*90)
    print("ELECTION PENSION THEORY - SUMMARY")
    print("="*90)
    
    print(f"\nElection Cycle Analysis:")
    print(f"  Average appointments 6m before elections: {election_analysis['appointments_6m_before'].mean():.1f}")
    print(f"  Average appointments 6m after elections:  {election_analysis['appointments_6m_after'].mean():.1f}")
    print(f"  Change: {((election_analysis['appointments_6m_after'].mean() - election_analysis['appointments_6m_before'].mean()) / election_analysis['appointments_6m_before'].mean() * 100):+.1f}%")
    
    print(f"\nPension Abuse Analysis (Final 6 months before election):")
    pre_2015_6m = months_summary[(months_summary['pension_era'] == 'Pre-2015') & 
                                  (months_summary['time_window'] == 'Last 6 months')]
    post_2015_6m = months_summary[(months_summary['pension_era'] == '2015+') & 
                                   (months_summary['time_window'] == 'Last 6 months')]
    
    if len(pre_2015_6m) > 0:
        print(f"  Pre-2015:  {int(pre_2015_6m['appointments'].values[0])} appointments across {int(pre_2015_6m['num_elections'].values[0])} elections")
        print(f"             = {pre_2015_6m['appts_per_election'].values[0]:.2f} per election, "
              f"{pre_2015_6m['one_time_per_election'].values[0]:.2f} pension abusers per election ({pre_2015_6m['one_time_only_pct'].values[0]:.1f}%)")
    
    if len(post_2015_6m) > 0:
        print(f"  2015+:     {int(post_2015_6m['appointments'].values[0])} appointments across {int(post_2015_6m['num_elections'].values[0])} elections")
        print(f"             = {post_2015_6m['appts_per_election'].values[0]:.2f} per election, "
              f"{post_2015_6m['one_time_per_election'].values[0]:.2f} pension abusers per election ({post_2015_6m['one_time_only_pct'].values[0]:.1f}%)")
    
    if len(pre_2015_6m) > 0 and len(post_2015_6m) > 0:
        rate_change = post_2015_6m['one_time_per_election'].values[0] - pre_2015_6m['one_time_per_election'].values[0]
        pct_change = post_2015_6m['one_time_only_pct'].values[0] - pre_2015_6m['one_time_only_pct'].values[0]
        print(f"\n  Rate change: {rate_change:+.2f} pension abusers per election")
        print(f"  Percentage change: {pct_change:+.1f} percentage points")
        if rate_change < 0 or pct_change < 0:
            print(f"  ✓ SUPPORTS PENSION THEORY - Fewer pension abusers after reform")
        else:
            print(f"  ✗ CONTRADICTS PENSION THEORY - More pension abusers after reform")

if __name__ == "__main__":
    main()
