"""
Restore individual_cabinet_analysis.html to PDF 1 model
Spell-based analysis focusing on churn dynamics, not career length
Unit: Individual appointment spells
Focus: How stable or disposable are ministers within cabinet churn dynamics?
"""

import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Load and filter data
df = pd.read_csv('data_sources/parliament/most recent extract/cabinet_ministers.csv', parse_dates=['start_date', 'end_date'])

# Filter to senior Cabinet posts only (Commons, non-PM)
senior_keywords = ['secretary of state', 'chancellor', 'lord chancellor', 'chief secretary', 'lord president', 'minister without portfolio']
df['post_lower'] = df['post'].str.lower()
df['is_senior'] = df['post_lower'].apply(lambda x: any(kw in x for kw in senior_keywords))
df['is_commons'] = df['member_house'] == 'Commons'
df['is_pm'] = df['post_lower'].str.contains('prime minister')

df_filtered = df[(df['is_senior']) & (df['is_commons']) & (~df['is_pm'])].copy()

# Calculate tenure
df_filtered['tenure_length_days'] = (df_filtered['end_date'] - df_filtered['start_date']).dt.days
df_filtered['tenure_years'] = df_filtered['tenure_length_days'] / 365.25

# Calculate per-person statistics: SPELL-BASED (not career-based)
person_stats = df_filtered.groupby('person_id').agg({
    'given_name': 'first',
    'family_name': 'first',
    'tenure_years': ['count', 'mean', 'std', 'min', 'max']  # Spell-level stats
}).reset_index()

person_stats.columns = ['person_id', 'given_name', 'family_name', 'spell_count', 'avg_tenure_per_spell', 'tenure_variance', 'min_tenure', 'max_tenure']
person_stats['name'] = person_stats['given_name'] + ' ' + person_stats['family_name']

# Handle NaN variance (single-spell ministers)
person_stats['tenure_variance'].fillna(0, inplace=True)

# Create categories based on CHURN DYNAMICS (not career length)
# High spell count = frequent appointments = high churn / disposable
# High avg tenure per spell = stable in role = low churn / anchor
def categorize_churn(row):
    """Classify by appointment stability, not career length"""
    avg_tenure = row['avg_tenure_per_spell']
    spell_count = row['spell_count']
    variance = row['tenure_variance']
    
    # High-churn: many spells AND/OR short average tenure
    high_churn = (spell_count >= 5) or (avg_tenure < 1.0)
    stable_spell = avg_tenure >= 3.0
    
    if spell_count >= 5 and avg_tenure < 1.0:
        return 'Sacrificial Pawn'  # High churn: many short appointments
    elif spell_count >= 4 and avg_tenure >= 2.0:
        return 'Utility Minister'   # Moderate churn: multiple medium tenures
    elif spell_count == 1 and avg_tenure < 1.0:
        return 'One-Off Appointment'  # Single brief appointment
    elif spell_count == 1 and avg_tenure >= 5.0:
        return 'Departmental Expert'  # Single long tenure = deep expertise
    elif spell_count >= 2 and avg_tenure >= 3.0:
        return 'Anchor Role'  # Stable: given multiple long assignments
    elif spell_count >= 3 and avg_tenure >= 1.5:
        return 'Portfolio Cycler'  # Medium churn with moderate stability
    else:
        return 'Mixed Pattern'

person_stats['category'] = person_stats.apply(categorize_churn, axis=1)

# For scatter plot, exclude single-spell short appointments for clarity (as PDF 1 does)
plot_data = person_stats[~((person_stats['spell_count'] == 1) & (person_stats['avg_tenure_per_spell'] < 1.0))].copy()

# Create scatter plot: Spell Count vs Average Tenure Per Spell
fig = go.Figure()

categories = ['Sacrificial Pawn', 'Utility Minister', 'Portfolio Cycler', 'Anchor Role', 'Departmental Expert', 'One-Off Appointment', 'Mixed Pattern']
colors = {
    'Sacrificial Pawn': '#d84315',      # Red - high instability
    'Utility Minister': '#f57c00',      # Orange - moderate churn
    'Portfolio Cycler': '#ffa726',      # Light orange - regular rotation
    'Anchor Role': '#2e7d32',           # Green - stable assignments
    'Departmental Expert': '#1b5e20',   # Dark green - very stable
    'One-Off Appointment': '#90a4ae',   # Gray - single brief
    'Mixed Pattern': '#757575'          # Dark gray - irregular pattern
}

for cat in categories:
    cat_data = plot_data[plot_data['category'] == cat].sort_values('avg_tenure_per_spell', ascending=False)
    if len(cat_data) > 0:
        fig.add_trace(go.Scatter(
            x=cat_data['spell_count'],
            y=cat_data['avg_tenure_per_spell'],
            mode='markers',
            name=cat,
            marker=dict(
                size=8,
                color=colors.get(cat, '#999999'),
                line=dict(width=1, color='white'),
                opacity=0.8
            ),
            text=[f"{row['name']}<br>Spells: {int(row['spell_count'])}<br>Avg/Spell: {row['avg_tenure_per_spell']:.2f}yr<br>Variance: {row['tenure_variance']:.2f}" 
                  for _, row in cat_data.iterrows()],
            hovertemplate='%{text}<extra></extra>'
        ))

fig.update_layout(
    title='Cabinet Appointment Churn: Spell Count vs Average Tenure Per Spell',
    xaxis_title='Number of Separate Cabinet Appointments (Spells)',
    yaxis_title='Average Years Per Appointment',
    height=650,
    hovermode='closest',
    legend=dict(
        title='Appointment Pattern',
        yanchor='top',
        y=0.99,
        xanchor='right',
        x=0.99,
        bgcolor='rgba(255,255,255,0.8)'
    ),
    annotations=[
        dict(
            x=1, y=8,
            text='Stable = Long assignments',
            showarrow=False,
            xanchor='left',
            font=dict(size=9, color='gray')
        ),
        dict(
            x=10, y=0.5,
            text='Unstable = High churn',
            showarrow=False,
            xanchor='right',
            font=dict(size=9, color='gray')
        )
    ]
)

scatter_chart = fig.to_html(include_plotlyjs=False, div_id='churn-scatter')

# Count by category
category_counts = person_stats['category'].value_counts().to_dict()

# Category descriptions (churn-focused, not career-focused)
category_info = {
    'Sacrificial Pawn': {
        'icon': '🎲',
        'criteria': '5+ spells AND average <1 year per spell',
        'desc': 'Ministers subjected to frequent, brief appointments. High churn pattern suggests use as problem-solvers in crisis periods or disposable assets during transitions. Rarely retained in single role.'
    },
    'Utility Minister': {
        'icon': '🔧',
        'criteria': '4+ spells AND 2-3 years average per spell',
        'desc': 'Reliable ministers cycled through multiple roles with moderate tenure in each. Trusted enough for repeated appointment but expected to move regularly. Generalists across portfolios.'
    },
    'Portfolio Cycler': {
        'icon': '🔄',
        'criteria': '3+ spells AND 1.5-2.5 years average per spell',
        'desc': 'Ministers with regular rotation patterns. Moderate churn indicating movement between related or contrasting portfolios. Career defined by breadth across departments.'
    },
    'Anchor Role': {
        'icon': '⚓',
        'criteria': '2+ spells AND 3+ years average per spell',
        'desc': 'Ministers given substantial tenure in multiple roles. Long appointments indicate trust and stability. Not disposable; retained across government restructures.'
    },
    'Departmental Expert': {
        'icon': '🎓',
        'criteria': 'Single appointment lasting 5+ years',
        'desc': 'Ministers who became department specialists through long tenure. Deep expertise developed in one portfolio. Removed rarely, suggesting critical or specialist role.'
    },
    'One-Off Appointment': {
        'icon': '📍',
        'criteria': 'Single appointment lasting <1 year',
        'desc': 'Brief, singular cabinet service. May indicate specific purpose (crisis management, temporary fill), political gesture, or unsuccessful appointment quickly ended.'
    },
    'Mixed Pattern': {
        'icon': '❓',
        'criteria': 'Irregular spell/tenure combinations',
        'desc': 'Ministers with variable appointment patterns that do not fit standard churn categories. Unique or irregular career trajectories.'
    }
}

# Generate HTML
html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Individual Cabinet Member Analysis - Appointment Churn Dynamics</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #fafafa;
            color: #333;
        }
        .header {
            background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0 0 10px 0;
            font-size: 2.5em;
        }
        .header p {
            margin: 5px 0;
            font-size: 1.1em;
            opacity: 0.9;
        }
        .key-insights {
            background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
            border-left: 6px solid #f57c00;
            padding: 25px;
            margin: 25px 0;
            border-radius: 8px;
            font-size: 1.05em;
        }
        .key-insights h2 {
            margin-top: 0;
            color: #e65100;
            font-size: 1.8em;
        }
        .key-insights ul {
            margin: 15px 0;
            line-height: 1.7;
        }
        .section {
            background: white;
            padding: 25px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .section h2 {
            color: #1a237e;
            border-bottom: 3px solid #283593;
            padding-bottom: 10px;
            margin-top: 0;
        }
        .category {
            background: #e3f2fd;
            border-left: 4px solid #1976d2;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        .category h3 {
            margin-top: 0;
            color: #0d47a1;
        }
        .member-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }
        .member-card {
            background: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 10px;
            font-size: 0.8em;
        }
        .member-name {
            font-weight: bold;
            color: #0d47a1;
            margin-bottom: 4px;
            font-size: 0.85em;
        }
        .member-stat {
            color: #666;
            font-size: 0.75em;
            margin: 2px 0;
        }
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-box {
            background: #e8eaf6;
            border: 2px solid #5c6bc0;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }
        .stat-label {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 8px;
        }
        .stat-value {
            font-size: 2.2em;
            font-weight: bold;
            color: #1a237e;
        }
        .exclusion-note {
            background: #ffebee;
            border: 2px solid #c62828;
            padding: 15px;
            margin: 20px 0;
            border-radius: 6px;
            font-weight: bold;
            color: #b71c1c;
        }
        .methodology-note {
            background: #eceff1;
            border-left: 4px solid #37474f;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Individual Cabinet Member Analysis</h1>
        <p>Appointment Churn Dynamics & Spell Structure</p>
        <p style="font-size: 0.9em; margin-top: 10px;">How stable or disposable are ministers within cabinet churn dynamics?</p>
    </div>

    <div class="exclusion-note">
        <strong>Note:</strong> This analysis excludes Prime Ministers and focuses only on senior Cabinet positions held by Members of the House of Commons. Single-appointment ministers with tenure <1 year are excluded from the scatter plot for clarity.
    </div>

    <div class="key-insights">
        <h2>🔑 Key Insights</h2>
        <ul>
            <li><strong>""" + str(len(person_stats)) + """ individuals</strong> held """ + str(len(df_filtered)) + """ senior Cabinet appointments across their careers</li>
            <li><strong>Appointment instability varies dramatically:</strong> Average tenure per spell ranges from """ + f"{person_stats['avg_tenure_per_spell'].min():.1f}" + """ to """ + f"{person_stats['avg_tenure_per_spell'].max():.1f}" + """ years</li>
            <li><strong>Sacrificial Pawns</strong> (""" + str(category_counts.get('Sacrificial Pawn', 0)) + """ ministers): Frequent, brief assignments—high churn pattern</li>
            <li><strong>Anchor Roles</strong> (""" + str(category_counts.get('Anchor Role', 0)) + """ ministers): Stable, lengthy tenures across multiple appointments</li>
            <li><strong>Spell variance</strong> reveals inconsistency: ministers retained briefly in some roles, long in others</li>
        </ul>
    </div>

    <div class="section">
        <h2>Appointment Pattern Overview</h2>
        <div class="stat-grid">
            <div class="stat-box">
                <div class="stat-label">Total Individuals</div>
                <div class="stat-value">""" + str(len(person_stats)) + """</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Total Spells</div>
                <div class="stat-value">""" + str(int(person_stats['spell_count'].sum())) + """</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Avg Spells/Person</div>
                <div class="stat-value">""" + f"{person_stats['spell_count'].mean():.1f}" + """</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Avg Tenure/Spell</div>
                <div class="stat-value">""" + f"{person_stats['avg_tenure_per_spell'].mean():.2f}yr" + """</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Interactive Churn Dynamics Scatter Plot</h2>
        <p style="color: #666; margin-bottom: 15px;">
            <strong>Interpretation:</strong> X-axis shows number of separate appointments (spell count). Y-axis shows average years per appointment. 
            Ministers in the <strong>upper left</strong> (few spells, long tenure) = stable, anchored roles. 
            Ministers in the <strong>lower right</strong> (many spells, short tenure) = high-churn, disposable positions.
        </p>
        """ + scatter_chart + """
    </div>

    <div class="section">
        <h2>Appointment Churn Categories</h2>
"""

# Add detailed category sections with member listings
for cat in ['Sacrificial Pawn', 'Utility Minister', 'Portfolio Cycler', 'Anchor Role', 'Departmental Expert', 'One-Off Appointment', 'Mixed Pattern']:
    cat_data = person_stats[person_stats['category'] == cat].sort_values('avg_tenure_per_spell', ascending=False)
    if len(cat_data) == 0:
        continue
    
    info = category_info.get(cat, {'icon': '?', 'criteria': 'N/A', 'desc': 'No description'})
    
    html += f"""
        <div class="category">
            <h3>{info['icon']} {cat} ({len(cat_data)} ministers)</h3>
            <p><strong>Pattern:</strong> {info['criteria']}</p>
            <p>{info['desc']}</p>
            <div class="member-grid">
"""
    
    for _, member in cat_data.iterrows():
        html += f"""                <div class="member-card">
                    <div class="member-name">{member['name']}</div>
                    <div class="member-stat">Spells: {int(member['spell_count'])}</div>
                    <div class="member-stat">Avg: {member['avg_tenure_per_spell']:.2f}yr</div>
                    <div class="member-stat">Var: {member['tenure_variance']:.2f}</div>
                </div>
"""
    
    html += """            </div>
        </div>
"""

html += """
    </div>

    <div class="section">
        <h2>Methodology & Model Definition</h2>
        <div class="methodology-note">
            <strong>Analytical Focus:</strong> This analysis treats each cabinet appointment as a discrete spell and measures churn dynamics.
            It answers the question: <em>"How stable or disposable are ministers within cabinet churn dynamics?"</em>
        </div>
        <ul>
            <li><strong>Unit of analysis:</strong> Individual appointment spells (not career totals)</li>
            <li><strong>Data source:</strong> UK Parliament Members' Library cabinet ministers database</li>
            <li><strong>Time period:</strong> 1945–present</li>
            <li><strong>Senior posts:</strong> Secretary of State, Chancellor of the Exchequer, Lord Chancellor, Chief Secretary to the Treasury, Lord President of the Council, Minister without Portfolio</li>
            <li><strong>Exclusions:</strong> Prime Ministers, House of Lords-only appointments</li>
            <li><strong>Key metric:</strong> Average tenure per spell = total years across all spells ÷ number of spells</li>
            <li><strong>Churn indicator:</strong> Spell count and tenure variance reveal appointment stability patterns</li>
            <li><strong>Chart filtering:</strong> Single-spell ministers with tenure <1 year excluded from scatter plot for visual clarity (but included in category counts)</li>
        </ul>
    </div>

    <footer style="text-align: center; margin-top: 40px; padding: 20px; color: #666; border-top: 1px solid #ddd;">
        <p><em>Analysis generated: January 2026</em></p>
        <p>Data: UK Parliament Members' Library | Spell-based churn model</p>
    </footer>

</body>
</html>
"""

# Write the file
with open('generated_charts/individual_cabinet_analysis.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✓ Restored: individual_cabinet_analysis.html")
print(f"✓ Model: Spell-based churn analysis (PDF 1)")
print(f"✓ Analyzed: {len(person_stats)} individuals, {int(person_stats['spell_count'].sum())} total spells")
print(f"✓ Scatter plot: Spell Count vs Average Tenure Per Spell")
print(f"✓ Categories: {len([c for c in category_counts if category_counts[c] > 0])} churn patterns")
print("\nChurn category distribution:")
for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
    if count > 0:
        print(f"  {cat}: {count}")
