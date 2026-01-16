"""
Analyze impact of 2015 pension reform on pre-election cabinet turnover patterns

Key change in 2015:
- Before: 50% of salary defined benefit pension
- After: Defined contribution scheme
- BUT: Ministers still get 2 pensions (MP + Ministerial) based on tenure

Question: Did pre-election acceleration decrease after 2015 when pension became less generous?

Elections to compare:
Pre-2015: 1970, 1974x2, 1979, 1983, 1987, 1992, 1997, 2001, 2005, 2010
Post-2015: 2015, 2017, 2019, 2024
"""

import pandas as pd
import numpy as np
from datetime import timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Load data
print("Loading data...")
df = pd.read_csv('data_sources/parliament/most recent extract/cabinet_ministers.csv', parse_dates=['start_date', 'end_date'])

# Filter for senior cabinet posts (Commons only, non-PM)
senior_keywords = ['secretary of state', 'chancellor', 'lord chancellor', 
                   'chief secretary', 'lord president', 'minister without portfolio']

df['post_lower'] = df['post'].str.lower()
df['is_senior'] = df['post_lower'].str.contains('|'.join(senior_keywords), na=False)
df['is_commons'] = df['member_house'] == 'Commons'
df['is_pm'] = df['post'].str.lower().str.contains('prime minister', na=False)

senior_df = df[(df['is_senior']) & (df['is_commons']) & (~df['is_pm'])].copy()
senior_df['tenure_years'] = senior_df['tenure_length_days'] / 365.25

print(f"Total senior cabinet posts: {len(senior_df)}")

# Define elections
elections = [
    pd.Timestamp('1970-06-18'), pd.Timestamp('1974-02-28'), pd.Timestamp('1974-10-10'),
    pd.Timestamp('1979-05-03'), pd.Timestamp('1983-06-09'), pd.Timestamp('1987-06-11'),
    pd.Timestamp('1992-04-09'), pd.Timestamp('1997-05-01'), pd.Timestamp('2001-06-07'),
    pd.Timestamp('2005-05-05'), pd.Timestamp('2010-05-06'), pd.Timestamp('2015-05-07'),
    pd.Timestamp('2017-06-08'), pd.Timestamp('2019-12-12'), pd.Timestamp('2024-07-04'),
]

# 2015 pension reform cutoff
PENSION_REFORM_DATE = pd.Timestamp('2015-05-07')

# For each election, analyze final year patterns
results_pre_2015 = []
results_post_2015 = []

for election_date in elections:
    election_year = election_date.year
    is_post_reform = election_date >= PENSION_REFORM_DATE
    
    # Final year = 12 months before election
    final_year_start = election_date - timedelta(days=365)
    
    # Get appointments in final year
    final_year_appts = senior_df[
        (senior_df['start_date'] >= final_year_start) & 
        (senior_df['start_date'] < election_date)
    ].copy()
    
    if len(final_year_appts) == 0:
        continue
    
    # Get appointments in same 12-month period 1 year earlier (control period)
    control_start = final_year_start - timedelta(days=365)
    control_end = election_date - timedelta(days=365)
    
    control_appts = senior_df[
        (senior_df['start_date'] >= control_start) & 
        (senior_df['start_date'] < control_end)
    ].copy()
    
    # Identify first-timers (no cabinet experience before final year started)
    unique_people_final_year = final_year_appts['person_id'].unique()
    prior_appts = senior_df[
        (senior_df['person_id'].isin(unique_people_final_year)) &
        (senior_df['start_date'] < final_year_start)
    ]
    prior_people = prior_appts['person_id'].unique()
    first_timers = final_year_appts[~final_year_appts['person_id'].isin(prior_people)]
    
    # Same for control period
    unique_people_control = control_appts['person_id'].unique() if len(control_appts) > 0 else []
    prior_appts_control = senior_df[
        (senior_df['person_id'].isin(unique_people_control)) &
        (senior_df['start_date'] < control_start)
    ]
    prior_people_control = prior_appts_control['person_id'].unique()
    first_timers_control = control_appts[~control_appts['person_id'].isin(prior_people_control)] if len(control_appts) > 0 else pd.DataFrame()
    
    result = {
        'election_date': election_date,
        'election_year': election_year,
        'is_post_reform': is_post_reform,
        'final_year_appointments': len(final_year_appts),
        'final_year_unique_people': final_year_appts['person_id'].nunique(),
        'final_year_first_timers': len(first_timers),
        'final_year_avg_tenure': final_year_appts['tenure_years'].mean(),
        'final_year_short_pct': (final_year_appts['tenure_years'] < 1.0).sum() / len(final_year_appts) * 100,
        'control_appointments': len(control_appts),
        'control_unique_people': control_appts['person_id'].nunique() if len(control_appts) > 0 else 0,
        'control_first_timers': len(first_timers_control),
        'control_avg_tenure': control_appts['tenure_years'].mean() if len(control_appts) > 0 else 0,
        'control_short_pct': (control_appts['tenure_years'] < 1.0).sum() / len(control_appts) * 100 if len(control_appts) > 0 else 0,
    }
    
    if is_post_reform:
        results_post_2015.append(result)
    else:
        results_pre_2015.append(result)

pre_df = pd.DataFrame(results_pre_2015)
post_df = pd.DataFrame(results_post_2015)

print("\n" + "="*100)
print("PENSION REFORM IMPACT ANALYSIS")
print("="*100)

print("\nPRE-2015 (Generous 50% Salary Pension)")
print("-" * 100)
print(f"Elections analyzed: {len(pre_df)}")
print(f"\nFinal Year Before Election:")
print(f"  Average appointments: {pre_df['final_year_appointments'].mean():.1f}")
print(f"  Average first-timers: {pre_df['final_year_first_timers'].mean():.1f} ({pre_df['final_year_first_timers'].mean() / pre_df['final_year_appointments'].mean() * 100:.1f}%)")
print(f"  Average tenure: {pre_df['final_year_avg_tenure'].mean():.2f} years")
print(f"  % with <1 year tenure: {pre_df['final_year_short_pct'].mean():.1f}%")

print(f"\nControl Period (Year Before Final Year):")
print(f"  Average appointments: {pre_df['control_appointments'].mean():.1f}")
print(f"  Average first-timers: {pre_df['control_first_timers'].mean():.1f} ({pre_df['control_first_timers'].mean() / pre_df['control_appointments'].mean() * 100:.1f}%)")
print(f"  Average tenure: {pre_df['control_avg_tenure'].mean():.2f} years")
print(f"  % with <1 year tenure: {pre_df['control_short_pct'].mean():.1f}%")

print(f"\nAcceleration Ratio (Final Year / Control):")
print(f"  Appointments: {pre_df['final_year_appointments'].mean() / pre_df['control_appointments'].mean():.2f}x")
print(f"  First-timers: {pre_df['final_year_first_timers'].mean() / pre_df['control_first_timers'].mean():.2f}x")

print("\n" + "="*100)
print("POST-2015 (Defined Contribution Pension)")
print("-" * 100)
print(f"Elections analyzed: {len(post_df)}")
print(f"\nFinal Year Before Election:")
print(f"  Average appointments: {post_df['final_year_appointments'].mean():.1f}")
print(f"  Average first-timers: {post_df['final_year_first_timers'].mean():.1f} ({post_df['final_year_first_timers'].mean() / post_df['final_year_appointments'].mean() * 100:.1f}%)")
print(f"  Average tenure: {post_df['final_year_avg_tenure'].mean():.2f} years")
print(f"  % with <1 year tenure: {post_df['final_year_short_pct'].mean():.1f}%")

print(f"\nControl Period (Year Before Final Year):")
print(f"  Average appointments: {post_df['control_appointments'].mean():.1f}")
print(f"  Average first-timers: {post_df['control_first_timers'].mean():.1f} ({post_df['control_first_timers'].mean() / post_df['control_appointments'].mean() * 100:.1f}%)")
print(f"  Average tenure: {post_df['control_avg_tenure'].mean():.2f} years")
print(f"  % with <1 year tenure: {post_df['control_short_pct'].mean():.1f}%")

print(f"\nAcceleration Ratio (Final Year / Control):")
print(f"  Appointments: {post_df['final_year_appointments'].mean() / post_df['control_appointments'].mean():.2f}x")
print(f"  First-timers: {post_df['final_year_first_timers'].mean() / post_df['control_first_timers'].mean():.2f}x")

print("\n" + "="*100)
print("COMPARISON: Pre-2015 vs Post-2015")
print("="*100)

pre_acceleration = pre_df['final_year_appointments'].mean() / pre_df['control_appointments'].mean()
post_acceleration = post_df['final_year_appointments'].mean() / post_df['control_appointments'].mean()

print(f"\nPre-Election Acceleration (Final Year / Control):")
print(f"  Pre-2015:  {pre_acceleration:.2f}x")
print(f"  Post-2015: {post_acceleration:.2f}x")
print(f"  Change: {((post_acceleration - pre_acceleration) / pre_acceleration * 100):+.1f}%")

pre_first_timer_ratio = pre_df['final_year_first_timers'].mean() / pre_df['final_year_appointments'].mean()
post_first_timer_ratio = post_df['final_year_first_timers'].mean() / post_df['final_year_appointments'].mean()

print(f"\nFirst-Timer Ratio (First-Timers / Total Appointments in Final Year):")
print(f"  Pre-2015:  {pre_first_timer_ratio:.1%}")
print(f"  Post-2015: {post_first_timer_ratio:.1%}")
print(f"  Change: {((post_first_timer_ratio - pre_first_timer_ratio) / pre_first_timer_ratio * 100):+.1f}%")

print(f"\nShort Tenure Prevalence (% <1 year in Final Year):")
print(f"  Pre-2015:  {pre_df['final_year_short_pct'].mean():.1f}%")
print(f"  Post-2015: {post_df['final_year_short_pct'].mean():.1f}%")
print(f"  Change: {(post_df['final_year_short_pct'].mean() - pre_df['final_year_short_pct'].mean()):+.1f} percentage points")

# Create visualization
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        'Final Year Appointments: Pre vs Post-2015',
        'First-Timers: Pre vs Post-2015',
        'Acceleration Ratio by Era',
        'Short Tenure Prevalence by Era'
    ),
    specs=[[{'secondary_y': False}, {'secondary_y': False}],
           [{'secondary_y': False}, {'secondary_y': False}]]
)

# Plot 1: Appointments
fig.add_trace(
    go.Box(y=pre_df['final_year_appointments'], name='Pre-2015', marker_color='#3498db'),
    row=1, col=1
)
fig.add_trace(
    go.Box(y=post_df['final_year_appointments'], name='Post-2015', marker_color='#e74c3c'),
    row=1, col=1
)

# Plot 2: First-timers
fig.add_trace(
    go.Box(y=pre_df['final_year_first_timers'], name='Pre-2015', marker_color='#3498db', showlegend=False),
    row=1, col=2
)
fig.add_trace(
    go.Box(y=post_df['final_year_first_timers'], name='Post-2015', marker_color='#e74c3c', showlegend=False),
    row=1, col=2
)

# Plot 3: Acceleration ratios
pre_accel_ratio = pre_df['final_year_appointments'] / pre_df['control_appointments']
post_accel_ratio = post_df['final_year_appointments'] / post_df['control_appointments']

fig.add_trace(
    go.Bar(x=['Pre-2015', 'Post-2015'], 
           y=[pre_accel_ratio.mean(), post_accel_ratio.mean()],
           marker_color=['#3498db', '#e74c3c'],
           text=[f"{pre_accel_ratio.mean():.2f}x", f"{post_accel_ratio.mean():.2f}x"],
           textposition='auto',
           showlegend=False),
    row=2, col=1
)

# Plot 4: Short tenure %
fig.add_trace(
    go.Bar(x=['Pre-2015', 'Post-2015'],
           y=[pre_df['final_year_short_pct'].mean(), post_df['final_year_short_pct'].mean()],
           marker_color=['#3498db', '#e74c3c'],
           text=[f"{pre_df['final_year_short_pct'].mean():.1f}%", f"{post_df['final_year_short_pct'].mean():.1f}%"],
           textposition='auto',
           showlegend=False),
    row=2, col=2
)

fig.update_yaxes(title_text="Appointments", row=1, col=1)
fig.update_yaxes(title_text="First-Timers", row=1, col=2)
fig.update_yaxes(title_text="Ratio", row=2, col=1)
fig.update_yaxes(title_text="Percentage", row=2, col=2)

fig.update_layout(
    height=800,
    title_text="Impact of 2015 Pension Reform on Pre-Election Cabinet Turnover",
    showlegend=True
)

# Save with proper path handling for GitHub Pages compatibility
from pathlib import Path
output_dir = Path(__file__).parent.parent / "generated_charts"
output_path = output_dir / "pension_reform_impact.html"
fig.write_html(str(output_path), include_plotlyjs='cdn')
print(f"\n✓ Generated: {output_path}")

# Save detailed results
combined_df = pd.concat([pre_df, post_df], ignore_index=True)
combined_df.to_csv(str(output_dir / 'pension_reform_comparison.csv'), index=False)
print(f"✓ Saved: generated_charts/pension_reform_comparison.csv")

print("\n" + "="*100)
print("CONCLUSION")
print("="*100)

if post_acceleration < pre_acceleration:
    change_direction = "DECREASED"
    interpretation = "The 2015 pension reform appears to have REDUCED the pre-election acceleration pattern."
elif post_acceleration > pre_acceleration:
    change_direction = "INCREASED"
    interpretation = "Surprisingly, the pre-election acceleration INCREASED after the 2015 pension reform."
else:
    change_direction = "REMAINED STABLE"
    interpretation = "The 2015 pension reform had NO SIGNIFICANT IMPACT on pre-election acceleration."

print(f"\nPre-election appointment acceleration has {change_direction} after the 2015 pension reform.")
print(f"\n{interpretation}")
print("\nPossible explanations:")
if post_acceleration < pre_acceleration:
    print("  • Less financial incentive with defined contribution scheme")
    print("  • Ministers still get 2 pensions, but less generous")
    print("  • Party may have shifted strategy")
elif post_acceleration > pre_acceleration:
    print("  • Despite pension changes, 2 pensions still valuable")
    print("  • Tenure-based system still incentivizes brief appointments")
    print("  • Other factors (experience, resume-building) may drive behavior")
    print("  • Recent elections (2017, 2019) had unusual political circumstances")

print("\n✓ Analysis complete!")
