"""
Restore individual_cabinet_analysis.html to original format with member listings
"""

import pandas as pd
import plotly.graph_objects as go

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

# Calculate per-person statistics
person_stats = df_filtered.groupby('person_id').agg({
    'given_name': 'first',
    'family_name': 'first',
    'post': 'count',  # number of spells
    'tenure_years': 'sum'  # total years
}).reset_index()

person_stats.columns = ['person_id', 'given_name', 'family_name', 'spell_count', 'total_years']
person_stats['name'] = person_stats['given_name'] + ' ' + person_stats['family_name']

# Calculate average tenure per spell
person_stats['avg_tenure_per_spell'] = person_stats['total_years'] / person_stats['spell_count']

# Create categories based on career patterns
def categorize_career(row):
    if row['spell_count'] >= 4 and row['total_years'] >= 5:
        return 'Stalwart'
    elif row['spell_count'] >= 3 and row['avg_tenure_per_spell'] < 1:
        return 'Sacrificial Pawn'
    elif row['spell_count'] == 1 and row['total_years'] >= 5:
        return 'Long-Tenure Specialist'
    elif row['spell_count'] >= 2 and row['avg_tenure_per_spell'] >= 3:
        return 'Rising Star'
    elif row['spell_count'] >= 3 and row['avg_tenure_per_spell'] >= 2:
        return 'Portfolio Rotator'
    else:
        return 'Other'

person_stats['category'] = person_stats.apply(categorize_career, axis=1)

# Create scatter plot
fig = go.Figure()

categories = ['Stalwart', 'Sacrificial Pawn', 'Long-Tenure Specialist', 'Rising Star', 'Portfolio Rotator', 'Other']
colors = {
    'Stalwart': '#2E86AB',
    'Sacrificial Pawn': '#A23B72',
    'Long-Tenure Specialist': '#F18F01',
    'Rising Star': '#C73E1D',
    'Portfolio Rotator': '#6A994E',
    'Other': '#999999'
}

for cat in categories:
    cat_data = person_stats[person_stats['category'] == cat]
    fig.add_trace(go.Scatter(
        x=cat_data['spell_count'],
        y=cat_data['total_years'],
        mode='markers',
        name=cat,
        marker=dict(
            size=10,
            color=colors[cat],
            line=dict(width=1, color='white')
        ),
        text=[f"{row['name']}<br>Spells: {row['spell_count']}<br>Total: {row['total_years']:.1f}yr<br>Avg: {row['avg_tenure_per_spell']:.1f}yr" 
              for _, row in cat_data.iterrows()],
        hovertemplate='%{text}<extra></extra>'
    ))

fig.update_layout(
    title='Career Pattern Scatter Plot: Cabinet Ministers by Tenure & Spell Count',
    xaxis_title='Number of Cabinet Spells',
    yaxis_title='Total Years in Cabinet',
    height=600,
    hovermode='closest',
    legend=dict(
        title='Career Pattern',
        yanchor='top',
        y=0.99,
        xanchor='left',
        x=0.01
    ),
    annotations=[
        dict(
            x=1, y=10,
            text='Top-left = Long-Tenure',
            showarrow=False,
            xanchor='left',
            font=dict(size=10, color='gray')
        ),
        dict(
            x=6, y=2,
            text='Bottom-right = Rotator',
            showarrow=False,
            xanchor='right',
            font=dict(size=10, color='gray')
        )
    ]
)

scatter_chart = fig.to_html(include_plotlyjs=False, div_id='career-scatter')

# Count by category
category_counts = person_stats['category'].value_counts().to_dict()

# Build category descriptions
category_info = {
    'Stalwart': {
        'icon': '🏛️',
        'criteria': '4+ cabinet spells AND 5+ total years',
        'desc': 'Experienced politicians who served in multiple senior roles across extended periods. These are the backbone of government, often trusted with difficult portfolios during crises.'
    },
    'Sacrificial Pawn': {
        'icon': '🎲',
        'criteria': '3+ spells AND average tenure <1 year per spell',
        'desc': 'Ministers who had frequent but brief appointments, often during periods of political instability or cabinet reshuffles. Their short tenures suggest they were used for specific purposes or during transitional periods.'
    },
    'Long-Tenure Specialist': {
        'icon': '📚',
        'criteria': 'Exactly 1 spell AND 5+ total years',
        'desc': 'Ministers who held a single cabinet position for an extended period, developing deep expertise in that portfolio. These specialists brought continuity and institutional knowledge to their departments.'
    },
    'Rising Star': {
        'icon': '⭐',
        'criteria': '2+ spells AND average 3+ years per spell',
        'desc': 'Ministers who showed career progression with substantial tenure in each role. These politicians demonstrated competence and were given increasing responsibility over time.'
    },
    'Portfolio Rotator': {
        'icon': '🔄',
        'criteria': '3+ spells AND average 2+ years per spell',
        'desc': 'Experienced ministers who moved between multiple portfolios with moderate tenure in each. They brought broad government experience and were trusted across different departments.'
    },
    'Other': {
        'icon': '📊',
        'criteria': 'Other patterns',
        'desc': 'Cabinet members who don\'t fit the above patterns, including brief single appointments, moderate-length careers, or unique patterns that defy easy categorization.'
    }
}

# Generate HTML
html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Individual Cabinet Minister Career Patterns</title>
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
            font-size: 1.15em;
        }
        .key-insights h2 {
            margin-top: 0;
            color: #e65100;
            font-size: 1.8em;
        }
        .key-insights ul {
            margin: 15px 0;
            line-height: 1.8;
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
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }
        .member-card {
            background: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 10px;
            font-size: 0.85em;
        }
        .member-name {
            font-weight: bold;
            color: #0d47a1;
            margin-bottom: 5px;
        }
        .member-stat {
            color: #666;
            font-size: 0.8em;
            margin: 2px 0;
        }
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
            font-size: 0.9em;
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
    </style>
</head>
<body>
    <div class="header">
        <h1>Individual Cabinet Minister Career Patterns</h1>
        <p>Analysis of """ + str(len(person_stats)) + """ Senior Cabinet Members (1959-2024)</p>
        <p style="font-size: 0.9em; margin-top: 10px;">Commons Only • Senior Posts Only</p>
    </div>

    <div class="exclusion-note">
        <strong>Note:</strong> This analysis excludes Prime Ministers and focuses only on senior Cabinet positions held by Members of the House of Commons. Lords-only appointments are not included.
    </div>

    <div class="key-insights">
        <h2>🔑 Key Insights</h2>
        <ul>
            <li><strong>""" + str(len(person_stats)) + """ unique individuals</strong> served in senior Cabinet roles between 1959-2024</li>
            <li><strong>Stalwarts</strong> (""" + str(category_counts.get('Stalwart', 0)) + """ members) had multiple spells and long tenure, representing experienced leadership</li>
            <li><strong>Sacrificial Pawns</strong> (""" + str(category_counts.get('Sacrificial Pawn', 0)) + """ members) had frequent but brief appointments, often during crises</li>
            <li><strong>Long-Tenure Specialists</strong> (""" + str(category_counts.get('Long-Tenure Specialist', 0)) + """ members) held single positions for extended periods</li>
            <li><strong>Rising Stars</strong> (""" + str(category_counts.get('Rising Star', 0)) + """ members) showed progression with longer tenures across appointments</li>
            <li><strong>Portfolio Rotators</strong> (""" + str(category_counts.get('Portfolio Rotator', 0)) + """ members) moved between multiple positions with moderate tenure</li>
        </ul>
    </div>

    <div class="section">
        <h2>Career Pattern Distribution</h2>
        <div class="stat-grid">
            <div class="stat-box">
                <div class="stat-label">Total Individuals</div>
                <div class="stat-value">""" + str(len(person_stats)) + """</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Average Spells</div>
                <div class="stat-value">""" + f"{person_stats['spell_count'].mean():.1f}" + """</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Average Total Years</div>
                <div class="stat-value">""" + f"{person_stats['total_years'].mean():.1f}" + """</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Longest Career</div>
                <div class="stat-value">""" + f"{person_stats['total_years'].max():.1f}yr" + """</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Interactive Career Pattern Scatter Plot</h2>
        """ + scatter_chart + """
        <p style="margin-top: 20px; color: #666; font-size: 0.95em;">
            <strong>How to Read:</strong> Each point represents one cabinet member. The x-axis shows number of different cabinet appointments, 
            while the y-axis shows total years served. Hover over points to see individual names and details.
        </p>
    </div>

    <div class="section">
        <h2>Career Pattern Categories with Members</h2>
"""

# Add detailed category sections with member listings
for cat in categories:
    cat_data = person_stats[person_stats['category'] == cat].sort_values('total_years', ascending=False)
    info = category_info[cat]
    
    html += f"""
        <div class="category">
            <h3>{info['icon']} {cat} ({len(cat_data)} members)</h3>
            <p><strong>Criteria:</strong> {info['criteria']}</p>
            <p>{info['desc']}</p>
            <div class="member-grid">
"""
    
    for _, member in cat_data.iterrows():
        html += f"""                <div class="member-card">
                    <div class="member-name">{member['name']}</div>
                    <div class="member-stat">Spells: {int(member['spell_count'])}</div>
                    <div class="member-stat">Total: {member['total_years']:.1f} years</div>
                    <div class="member-stat">Avg/Spell: {member['avg_tenure_per_spell']:.1f} years</div>
                </div>
"""
    
    html += """            </div>
        </div>
"""

html += """
    </div>

    <div class="section">
        <h2>Methodology</h2>
        <ul>
            <li><strong>Data Source:</strong> UK Parliament Members' Library cabinet ministers database</li>
            <li><strong>Time Period:</strong> 1959-2024 (modern cabinet era)</li>
            <li><strong>Senior Posts:</strong> Secretary of State, Chancellor of the Exchequer, Lord Chancellor, Chief Secretary to the Treasury, Lord President of the Council, Minister without Portfolio</li>
            <li><strong>Exclusions:</strong> Prime Ministers (analyzed separately), House of Lords-only appointments</li>
            <li><strong>Dataset:</strong> 578 senior cabinet appointments across """ + str(len(person_stats)) + """ unique individuals</li>
            <li><strong>Spell Definition:</strong> Each distinct appointment to a cabinet position, counted even if brief</li>
            <li><strong>Tenure Calculation:</strong> Days between start_date and end_date, converted to years (÷365.25)</li>
        </ul>
    </div>

    <footer style="text-align: center; margin-top: 40px; padding: 20px; color: #666; border-top: 1px solid #ddd;">
        <p><em>Analysis generated: January 2026</em></p>
        <p>Data: UK Parliament Members' Library</p>
    </footer>

</body>
</html>
"""

# Write the file
with open('generated_charts/individual_cabinet_analysis.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✓ Restored: individual_cabinet_analysis.html")
print(f"✓ Analyzed: {len(person_stats)} unique cabinet members")
print(f"✓ Categories: {len(categories)} career patterns with member listings")
print("✓ Format: Original career pattern focus with member details, no pension content")
print(f"✓ Stalwarts: {category_counts.get('Stalwart', 0)} | Sacrificial Pawns: {category_counts.get('Sacrificial Pawn', 0)} | Long-Tenure: {category_counts.get('Long-Tenure Specialist', 0)} | Rising Stars: {category_counts.get('Rising Star', 0)} | Portfolio Rotators: {category_counts.get('Portfolio Rotator', 0)}")
