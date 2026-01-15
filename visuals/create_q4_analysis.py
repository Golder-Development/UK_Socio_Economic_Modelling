"""
Create detailed Q4 analysis visualizations for the election pension theory.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Load the parliamentary phase analysis
phase_df = pd.read_csv('generated_charts/parliamentary_phase_analysis.csv')

# Focus on Q4 data
q4_data = phase_df[phase_df['quarter'] == 4].copy()

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        'Q4 (Election Phase): Appointments Over Time',
        'Q4 (Election Phase): Average Tenure Over Time',
        'Q4: Percentage of Short Tenures (<1 year)',
        'Q4 vs Q1 Comparison: Tenure Length'
    ),
    specs=[[{'secondary_y': False}, {'secondary_y': False}],
           [{'secondary_y': False}, {'secondary_y': False}]]
)

# Plot 1: Q4 Appointments over time
fig.add_trace(
    go.Scatter(
        x=q4_data['parliament_year'],
        y=q4_data['appointments'],
        mode='lines+markers',
        name='Q4 Appointments',
        line=dict(color='#d32f2f', width=2),
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor='rgba(211, 47, 47, 0.2)',
    ),
    row=1, col=1
)

# Plot 2: Q4 Tenure over time
fig.add_trace(
    go.Scatter(
        x=q4_data['parliament_year'],
        y=q4_data['avg_tenure_years'],
        mode='lines+markers',
        name='Q4 Avg Tenure',
        line=dict(color='#1976d2', width=2),
        marker=dict(size=8),
    ),
    row=1, col=2
)

# Add Q1 comparison line
q1_data = phase_df[phase_df['quarter'] == 1].copy()
avg_q1_tenure = phase_df[phase_df['quarter'] == 1]['avg_tenure_years'].mean()
fig.add_hline(y=avg_q1_tenure, line_dash="dash", line_color="#4caf50",
              annotation_text=f"Q1 Avg: {avg_q1_tenure:.2f}yr", 
              row=1, col=2)

# Plot 3: Q4 Short tenures percentage
fig.add_trace(
    go.Bar(
        x=q4_data['parliament_year'],
        y=q4_data['short_tenures_pct'],
        name='Short Tenures %',
        marker=dict(color='#ff9800'),
        text=q4_data['short_tenures_pct'].round(1),
        textposition='auto',
    ),
    row=2, col=1
)

# Plot 4: Q4 vs Q1 side-by-side
parliament_years = sorted(phase_df['parliament_year'].unique())
q1_tenures_by_parl = []
q4_tenures_by_parl = []

for year in parliament_years:
    q1_year = phase_df[(phase_df['parliament_year'] == year) & (phase_df['quarter'] == 1)]
    q4_year = phase_df[(phase_df['parliament_year'] == year) & (phase_df['quarter'] == 4)]
    
    if len(q1_year) > 0:
        q1_tenures_by_parl.append(q1_year['avg_tenure_years'].values[0])
    else:
        q1_tenures_by_parl.append(None)
    
    if len(q4_year) > 0:
        q4_tenures_by_parl.append(q4_year['avg_tenure_years'].values[0])
    else:
        q4_tenures_by_parl.append(None)

x_labels = [str(y) for y in parliament_years]

fig.add_trace(
    go.Bar(
        x=x_labels,
        y=q1_tenures_by_parl,
        name='Q1 (Early)',
        marker=dict(color='#4caf50'),
    ),
    row=2, col=2
)

fig.add_trace(
    go.Bar(
        x=x_labels,
        y=q4_tenures_by_parl,
        name='Q4 (Election)',
        marker=dict(color='#d32f2f'),
    ),
    row=2, col=2
)

# Update axes
fig.update_yaxes(title_text="Count", row=1, col=1)
fig.update_yaxes(title_text="Years", row=1, col=2)
fig.update_yaxes(title_text="Percentage", row=2, col=1)
fig.update_yaxes(title_text="Average Tenure (years)", row=2, col=2)

fig.update_xaxes(title_text="Parliament Year", row=2, col=1)
fig.update_xaxes(title_text="Parliament Year", row=2, col=2)

fig.update_layout(
    height=900,
    title_text="<b>Q4 (Final Quarter/Election Phase) Analysis</b><br><sub>Does the 'Election Pension' theory predict shorter or longer tenures before elections?</sub>",
    showlegend=True,
    hovermode='x unified'
)

fig.write_html('generated_charts/q4_election_phase_analysis.html')
print("✓ Generated: q4_election_phase_analysis.html")

# Create summary statistics
print("\n" + "="*90)
print("Q4 ELECTION PHASE ANALYSIS SUMMARY")
print("="*90)

print(f"\nQ4 Statistics (Final Quarter Before Elections):")
print(f"  Average appointments: {q4_data['appointments'].mean():.1f}")
print(f"  Average tenure: {q4_data['avg_tenure_years'].mean():.2f} years")
print(f"  % appointments <1 year: {q4_data['short_tenures_pct'].mean():.1f}%")

print(f"\nQ1 Statistics (Early Quarter After Elections/Start of Parliament):")
q1_avg = phase_df[phase_df['quarter'] == 1]['appointments'].mean()
q1_tenure = phase_df[phase_df['quarter'] == 1]['avg_tenure_years'].mean()
q1_short = phase_df[phase_df['quarter'] == 1]['short_tenures_pct'].mean()
print(f"  Average appointments: {q1_avg:.1f}")
print(f"  Average tenure: {q1_tenure:.2f} years")
print(f"  % appointments <1 year: {q1_short:.1f}%")

print(f"\nDifference (Q4 - Q1):")
print(f"  Appointments: {q4_data['appointments'].mean() - q1_avg:.1f} ({((q4_data['appointments'].mean() - q1_avg) / q1_avg * 100):+.1f}%)")
print(f"  Tenure: {q4_data['avg_tenure_years'].mean() - q1_tenure:.2f} years ({((q4_data['avg_tenure_years'].mean() - q1_tenure) / q1_tenure * 100):+.1f}%)")
print(f"  Short tenures: {q4_data['short_tenures_pct'].mean() - q1_short:.1f}% points")

print(f"\nElection Pension Theory Prediction:")
print(f"  Theory says: Q4 should have MORE long-tenure appointments to secure pensions")
print(f"  Data shows: Q4 has SHORTER average tenure ({q4_data['avg_tenure_years'].mean():.2f}yr) than Q1 ({q1_tenure:.2f}yr)")
print(f"  Theory prediction: NOT SUPPORTED ✗")
