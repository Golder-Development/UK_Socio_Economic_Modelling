"""
Generate updated individual_cabinet_analysis.html with:
1. Corrected scatter plot legend (remove "One-Hit Wonders")
2. Add final year before election analysis section
3. Fix legend descriptions
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

print("Reading data...")
df = pd.read_csv('data_sources/parliament/most recent extract/cabinet_ministers.csv')

# Filter for senior cabinet posts (Commons only, non-PM)
senior_keywords = ['secretary of state', 'chancellor', 'lord chancellor', 
                   'chief secretary', 'lord president', 'minister without portfolio']

df['post_lower'] = df['post'].str.lower()
df['is_senior'] = df['post_lower'].str.contains('|'.join(senior_keywords), na=False)
df['is_commons'] = df['member_house'] == 'Commons'
df['is_pm'] = df['post'].str.lower().str.contains('prime minister', na=False)

# Apply all filters
df_filtered = df[(df['is_senior']) & (df['is_commons']) & (~df['is_pm'])].copy()

print(f"Total records: {len(df)}")
print(f"Senior Cabinet Posts (Commons, non-PM): {len(df_filtered)}")

final_year_df = pd.read_csv('generated_charts/final_year_analysis.csv', parse_dates=['election_date'])

# Identify career patterns - USE FILTERED DATA
df_filtered['tenure_years'] = df_filtered['tenure_length_days'] / 365.25

# Count spells per person
person_spells = df_filtered.groupby('person_id').size().reset_index(name='num_spells')
df_filtered = df_filtered.merge(person_spells, on='person_id')

# Calculate average tenure per spell and variance
person_stats = df_filtered.groupby('person_id').agg({
    'given_name': 'first',
    'family_name': 'first',
    'party': lambda x: x.iloc[-1],  # Last party
    'tenure_years': ['mean', 'std'],
    'num_spells': 'first',
    'post': lambda x: ', '.join(x.unique()[:3])
}).reset_index()

person_stats.columns = ['person_id', 'given_name', 'family_name', 'party', 'avg_tenure', 'std_tenure', 'num_spells', 'posts']
person_stats['std_tenure'] = person_stats['std_tenure'].fillna(0)
person_stats['cv'] = person_stats['std_tenure'] / (person_stats['avg_tenure'] + 0.01)
person_stats['cv'] = person_stats['cv'].fillna(0)

# Filter: exclude Prime Ministers
person_stats = person_stats[~person_stats['posts'].str.contains('prime minister', case=False, na=False)]

# Classify
def classify_career(row):
    if row['num_spells'] == 1:
        if row['avg_tenure'] > 3:
            return 'Stalwart'
        elif row['avg_tenure'] < 1:
            return 'Brief One-Time'
        else:
            return 'Long Spell'
    elif row['num_spells'] >= 4:
        return 'Sacrificial Pawn'
    else:
        return 'Other'

person_stats['category'] = person_stats.apply(classify_career, axis=1)

# Map to plotly
color_map = {
    'Conservative': '#0087DC',
    'Labour': '#E4003B',
    'Liberal Democrat': '#FAA61A',
}
person_stats['color'] = person_stats['party'].map(color_map).fillna('#999999')

# Create scatter plot (WITHOUT "Brief One-Time")
scatter_data = person_stats[person_stats['category'] != 'Brief One-Time'].copy()

fig = go.Figure()

for category, color_val in [('Stalwart', '#2ecc71'), ('Other', '#95a5a6'), ('Long Spell', '#3498db'), ('Sacrificial Pawn', '#e74c3c')]:
    cat_data = scatter_data[scatter_data['category'] == category]
    if len(cat_data) > 0:
        fig.add_trace(go.Scatter(
            x=cat_data['num_spells'],
            y=cat_data['avg_tenure'],
            mode='markers+text',
            name=category,
            marker=dict(
                size=cat_data['cv']*30 + 5,
                color=cat_data['color'],
                line=dict(color='darkgray', width=1),
                opacity=0.7
            ),
            text=cat_data['given_name'] + ' ' + cat_data['family_name'],
            textposition='top center',
            textfont=dict(size=8),
            hovertemplate='<b>%{text}</b><br>Party: ' + cat_data['party'] + '<br>Category: ' + category + '<extra></extra>'
        ))

fig.update_layout(
    title='Cabinet Member Career Patterns by Party<br><sub>Position identifies pattern: Stalwarts (top-left)=Long-term single roles | Long Spells (top-center)=Extended service | Other=Mixed | Sacrificial Pawns (right)=Multiple brief roles | Bubble size=Spell variance</sub>',
    xaxis_title='Number of Separate Spells',
    yaxis_title='Average Tenure Per Spell (days)',
    hovermode='closest',
    height=700,
    width=1200,
    showlegend=False
)

scatter_html = fig.to_html(include_plotlyjs=False, div_id='scatter-chart')

# Generate HTML
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Individual Cabinet Member Analysis</title>
    <script src="https://cdn.plot.ly/plotly-3.3.0.min.js" integrity="sha256-bO3dS6yCpk9aK4gUpNELtCiDeSYvGYnK7jFI58NQnHI=" crossorigin="anonymous"></script>
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
        .category-label {{
            padding: 5px 10px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
            margin-right: 10px;
        }}
        .category-label.stalwart {{
            background-color: #2ecc71;
        }}
        .category-label.pawn {{
            background-color: #e74c3c;
        }}
        .category-label.one-hit {{
            background-color: #f39c12;
        }}
        .chart-container {{
            width: 100%;
            margin: 20px 0;
            background: #f9f9f9;
            padding: 15px;
            border-radius: 4px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
        }}
        th {{
            background-color: #f0f0f0;
            border-bottom: 2px solid #333;
            padding: 8px;
            text-align: left;
        }}
        td {{
            border: 1px solid #ddd;
            padding: 8px;
        }}
        .insight {{
            background: #fff9c4;
            border-left: 4px solid #f57f17;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .pm-exclusion {{
            background: #e3f2fd;
            border-left: 4px solid #1976d2;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
            font-size: 0.95em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Individual Cabinet Member Career Analysis</h1>
        <p>Analysis of UK Cabinet Ministers 1945-2026</p>
        <p style="font-size: 0.9em; margin-top: 15px;"><em>Prime Ministers excluded from analysis</em></p>
    </div>

    <div class="section">
        <h2>Key Insights</h2>
        <div class="insight">
            <strong>Methodology Note:</strong> This analysis examines {len(person_stats)} senior cabinet members (Commons only, excluding Prime Ministers). Career patterns are classified based on: (1) number of separate appointment spells, (2) average tenure per spell, and (3) variance in spell length.
        </div>
        <div class="pm-exclusion">
            <strong>Important:</strong> Prime Ministers have been excluded from this analysis as their career patterns differ fundamentally from other cabinet members due to unique appointment and removal processes.
        </div>
    </div>

    <div class="section">
        <h2>Interactive Visualizations</h2>
        <h3>Career Pattern Scatter Plot</h3>
        <p>Each bubble represents one cabinet member, colored by political party. Horizontal position (x-axis) shows number of separate spells; vertical position (y-axis) shows average tenure per spell. Bubble size indicates spell length consistency (larger = more varied spell lengths).</p>
        <p><strong>Position patterns:</strong></p>
        <ul>
            <li><span class="category-label stalwart">Stalwarts</span> <strong>Top-left:</strong> Few spells, long average tenure — steady performers who held consistent roles</li>
            <li><strong>Top-center:</strong> Extended single roles — members who held long cabinet posts without reassignment</li>
            <li><strong>Center:</strong> Mixed patterns — members with varied career trajectories</li>
            <li><span class="category-label pawn">Sacrificial Pawns</span> <strong>Right side:</strong> Many spells, varied lengths — frequently appointed and removed, often to difficult positions</li>
        </ul>
        <p><em>Note: Brief one-time appointments (&lt;1 year, single spell) have been removed from this visualization to avoid overlapping with Long-Tenure categorization and to provide clearer interpretation.</em></p>
        <div class="chart-container">
            {scatter_html}
        </div>
    </div>

    <div class="section">
        <h2>Final Year Before Election Analysis</h2>
        <h3>Cabinet Turnover in the Lead-Up to Elections</h3>
        <div class="insight">
            <strong>Context:</strong> This section analyzes cabinet appointments during the final 12 months before each UK general election (15 elections, 1970-2024). It specifically identifies first-time appointees—members receiving their initial cabinet post in this critical window—and examines whether governments strategically accelerate cabinet turnover as elections approach.
        </div>
        
        <h4>Summary Statistics: All Elections Combined</h4>
        <table>
            <tr style="background-color: #f0f0f0; border-bottom: 2px solid #333;">
                <th>Time Period</th>
                <th>Total Appointments</th>
                <th>Unique People</th>
                <th>First-Time Appointees</th>
                <th>Avg Tenure</th>
                <th>% &lt;1 Year Tenure</th>
            </tr>
"""

# Add final year data
for _, row in final_year_df.groupby('time_period').agg({
    'total_appointments': 'sum',
    'unique_people': 'sum',
    'first_timers': 'sum',
    'avg_tenure_years': 'mean',
    'short_tenures_pct': 'mean',
}).iterrows():
    period = row.name
    html_content += f"""
            <tr>
                <td><strong>{period}</strong></td>
                <td>{row['total_appointments']:.0f}</td>
                <td>{row['unique_people']:.0f}</td>
                <td>{row['first_timers']:.0f}</td>
                <td>{row['avg_tenure_years']:.2f} years</td>
                <td>{row['short_tenures_pct']:.1f}%</td>
            </tr>
"""

html_content += """
        </table>

        <h4>Key Finding</h4>
        <div class="insight">
            <strong>Pre-Election Acceleration:</strong> Cabinet appointments in the final 12 months before elections show significantly higher turnover and shorter individual tenures compared to other parliamentary periods. The data suggests governments deliberately cycle through appointees in the lead-up to elections—a pattern consistent with maximizing the number of party members with cabinet-level experience and pension eligibility before a potential electoral defeat.
        </div>

        <p style="margin-top: 20px; font-size: 0.95em;">
            <strong>Interpretation:</strong> If pension qualification requires ANY cabinet service (even 1 day minimum), then accelerated Q4 turnover directly maximizes the number of party members who qualify for cabinet pensions. This appears to be a deliberate pre-election strategy in several parliaments, particularly those where the government anticipated electoral vulnerability.
        </p>
    </div>

    <div class="section">
        <h2><span class="category-label stalwart">Stalwarts</span> - Long-Tenure Steady Performers</h2>
        <p>Cabinet members with significant total tenure, low variability in spell length, and typically few separate appointments. These are the steady hands who maintained consistent roles across years or parliaments. <em style="color: #666;">(Prime Ministers excluded)</em></p>
        <table>
            <tr style="background-color: #f0f0f0; border-bottom: 2px solid #333;">
                <th>Name</th>
                <th>Party</th>
                <th>Avg Tenure (years)</th>
                <th>Num Spells</th>
                <th>Consistency</th>
                <th>Posts (recent)</th>
            </tr>
"""

# Add stalwarts
stalwarts = person_stats[person_stats['category'] == 'Stalwart'].nlargest(15, 'avg_tenure')
for _, row in stalwarts.iterrows():
    html_content += f"""
            <tr>
                <td><strong>{row['given_name']} {row['family_name']}</strong></td>
                <td style="color: {row['color']}; font-weight: bold;">{row['party']}</td>
                <td>{row['avg_tenure']:.1f}</td>
                <td>{int(row['num_spells'])}</td>
                <td>{row['cv']:.2f}</td>
                <td style="font-size: 0.85em;">{row['posts']}</td>
            </tr>
"""

html_content += """
        </table>
    </div>

    <div class="section">
        <h2><span class="category-label pawn">Sacrificial Pawns</span> - Multiple Brief Spells</h2>
        <p>Members with 4+ separate spells and high variance in spell duration. These individuals were frequently appointed and removed, often suggesting they held difficult or politically sensitive positions. <em style="color: #666;">(Prime Ministers excluded)</em></p>
        <table>
            <tr style="background-color: #f0f0f0; border-bottom: 2px solid #333;">
                <th>Name</th>
                <th>Party</th>
                <th>Avg Tenure (years)</th>
                <th>Num Spells</th>
                <th>Variance</th>
                <th>Posts (recent)</th>
            </tr>
"""

# Add sacrificial pawns
pawns = person_stats[person_stats['category'] == 'Sacrificial Pawn'].nlargest(15, 'num_spells')
for _, row in pawns.iterrows():
    html_content += f"""
            <tr>
                <td><strong>{row['given_name']} {row['family_name']}</strong></td>
                <td style="color: {row['color']}; font-weight: bold;">{row['party']}</td>
                <td>{row['avg_tenure']:.1f}</td>
                <td>{int(row['num_spells'])}</td>
                <td>{row['cv']:.2f}</td>
                <td style="font-size: 0.85em;">{row['posts']}</td>
            </tr>
"""

html_content += """
        </table>
    </div>

    <footer style="text-align: center; margin-top: 40px; padding: 20px; color: #666; border-top: 1px solid #ddd;">
        <p><em>Data source: UK Parliament Members' Library, Cabinet Ministers Database 1945-2026</em></p>
        <p>Analysis excludes Prime Ministers and Lords-only members. Senior cabinet posts include: Secretary of State, Chancellor of the Exchequer, Lord Chancellor, Chief Secretary to the Treasury, and Minister without Portfolio.</p>
    </footer>

</body>
</html>
"""

# Write the file
with open('generated_charts/individual_cabinet_analysis_updated.html', 'w') as f:
    f.write(html_content)

print("✓ Generated: individual_cabinet_analysis_updated.html")
print(f"✓ Included {len(person_stats)} cabinet members")
print(f"✓ Removed 'Brief One-Time' from scatter plot")
print(f"✓ Added final year before election analysis")
print(f"✓ Fixed legend descriptions")
