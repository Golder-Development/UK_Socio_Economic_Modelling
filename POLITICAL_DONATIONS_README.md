# Political Donations Analysis Dashboard

## Overview

This directory contains comprehensive interactive dashboards analyzing UK political donations from 2001-2025. The suite includes a summary overview, individual party analyses, and aggregate breakdowns by donation type and temporal trends.

**Total Data**: 90,006 donation records | £1.55 billion | 23,238 unique donors

---

## 📊 Dashboards

### Summary Dashboard (Start Here)

**File**: `political_donations_summary_dashboard.html`

A comprehensive 6-panel overview featuring:

- **Key Statistics Cards**: Total donations, number of records, unique donors, average size
- **Donations by Party**: Top 15 recipient parties (bar chart)
- **Donations by Type**: Distribution across donation categories (pie chart)
- **Top 10 Donors**: Individual/corporate donor rankings (horizontal bar)
- **Monthly Trends**: Temporal analysis showing funding patterns (line chart)
- **Donor Count**: Number of unique donors per party (bar chart)
- **Average Donation Size**: Mean contribution by donation type (bar chart)

**Best For**: Getting the big picture, understanding overall funding patterns, identifying major parties and donors

---

### Party-Specific Dashboards

Individual interactive dashboards for each major party with:

- Time-period filtering dropdown
- Donation type breakdowns
- Donor analysis
- Temporal trends
- Party-specific statistics

**Available Parties**:

1. `donations_by_party_conservative_and_unionist_party.html` - Conservative Party (largest recipient)
2. `donations_by_party_labour_party.html` - Labour Party
3. `donations_by_party_liberal_democrats.html` - Liberal Democrats
4. `donations_by_party_uk_independence_party_(ukip).html` - UKIP
5. `donations_by_party_green_party.html` - Green Party
6. `donations_by_party_scottish_national_party_(snp).html` - SNP
7. `donations_by_party_plaid_cymru_-_the_party_of_wales.html` - Plaid Cymru
8. `donations_by_party_democratic_unionist_party_-_d.u.p..html` - DUP
9. `donations_by_party_reform_uk.html` - Reform UK

**Best For**: Deep-diving into specific parties, comparing time periods, analyzing donor composition

---

### Aggregate Analyses

#### 1. Party Summary (`donations_by_party_summary.html`)

Comparative view across all parties showing:

- Party funding rankings
- Donation type distribution by party
- Donor diversity metrics
- Comparative statistics

**Best For**: Comparing parties side-by-side

#### 2. Donor Type Analysis (`donations_donor_type_analysis.html`)

Breakdown by donation category:

- Cash donations
- Non-cash contributions
- Sponsorship
- Public funding
- Bequests
- Other types

**Best For**: Understanding funding composition and donation patterns

#### 3. Time Analysis (`donations_time_analysis.html`)

Temporal trends showing:

- Monthly donation patterns
- Year-over-year comparisons
- Seasonal variations
- Long-term trends

**Best For**: Identifying funding cycles and temporal patterns

#### 4. Party Heatmap (`donations_party_heatmap.html`)

Comparative heatmap visualization:

- Party vs donation type matrix
- Intensity shows total funding
- Easy pattern spotting across dimensions

**Best For**: Identifying correlations between parties and donation types

---

## 💰 Key Statistics

### Overall Funding

- **Total**: £1,554,470,846.68 (£1.55 billion)
- **Records**: 90,006 donations
- **Unique Donors**: 23,238
- **Average Donation**: £17,266.48
- **Date Range**: 2001-01-01 to 2025-10-29

### By Donation Type

| Type        | Count  | Amount         |
| ----------- | ------ | -------------- |
| Cash        | 69,822 | £1,125,301,131 |
| Non-Cash    | 10,351 | £91,436,870    |
| Public Fund | 3,795  | £251,743,352   |
| Bequest     | 989    | £59,820,795    |
| Sponsorship | 884    | £7,131,326     |
| Other       | 4,165  | £19,037,374    |

### Color Coding

- 🟢 **Cash**: Green (#4CAF50)
- 🔵 **Non-Cash**: Blue (#2196F3)
- 🟠 **Sponsorship**: Orange (#FF9800)
- 🟣 **Public Fund**: Purple (#9C27B0)
- 🔴 **Bequest**: Red (#f44336)
- ⚪ **Other**: Grey (#999)

---

## 🔄 How to Refresh the Data

### Option 1: Regenerate Party Dashboards

```bash
python visuals/political_donations_interactive.py
```

Generates:

- All 9 party-specific dashboards
- Party summary analysis
- Donor type analysis
- Time analysis
- Party heatmap

**Output**: 14 HTML files in `generated_charts/`
**Time**: ~2-3 minutes

### Option 2: Regenerate Summary Dashboard

```bash
python visuals/political_donations_summary_dashboard.py
```

Generates:

- `political_donations_summary_dashboard.html`

**Output**: 1 HTML file
**Time**: ~30-60 seconds

### Option 3: Regenerate All

```bash
# Run both scripts in sequence
python visuals/political_donations_interactive.py
python visuals/political_donations_summary_dashboard.py
```

---

## 📁 File Organization

```
generated_charts/
├── political_donations_summary_dashboard.html    ← START HERE
├── donations_by_party_conservative_and_unionist_party.html
├── donations_by_party_labour_party.html
├── donations_by_party_liberal_democrats.html
├── donations_by_party_uk_independence_party_(ukip).html
├── donations_by_party_green_party.html
├── donations_by_party_scottish_national_party_(snp).html
├── donations_by_party_plaid_cymru_-_the_party_of_wales.html
├── donations_by_party_democratic_unionist_party_-_d.u.p..html
├── donations_by_party_reform_uk.html
├── donations_by_party_summary.html
├── donations_donor_type_analysis.html
├── donations_time_analysis.html
└── donations_party_heatmap.html

Data source:
data_sources/dashboard_demo_readonly/output/cleaned_donations.csv
```

---

## 🎨 Styling Features

All dashboards feature professional, consistent styling:

✅ **Gradient Headers** - Blue to indigo professional color scheme  
✅ **Color-Coded Badges** - Donation types instantly recognizable  
✅ **Interactive Charts** - Hover for details, click legends to toggle  
✅ **Responsive Design** - Works on desktop, tablet, mobile  
✅ **Clear Typography** - Readable fonts and proper hierarchy  
✅ **Insight Boxes** - Highlighted key findings and patterns  
✅ **Statistics Cards** - Key metrics prominently displayed

---

## 🔍 How to Use the Dashboards

### Exploring the Summary Dashboard

1. **Start with Statistics**: Review the 4 key stat cards at the top

   - Total donations
   - Number of records
   - Unique donors
   - Average donation

2. **Identify Major Players**: Check the "Top 10 Donors" section

   - See who funds the most
   - Identify corporate vs individual donors

3. **Understand Distribution**: Look at "Donations by Type" pie chart

   - Cash dominates (72% of total)
   - Other types are supplementary

4. **Spot Trends**: Examine the monthly trend line
   - Identify funding peaks and valleys
   - Notice any seasonal patterns

### Drilling into Party Dashboards

1. **Select a Party**: Click on a party name in the summary

   - Opens that party's dedicated dashboard

2. **Use Time Filter**: Select time period from dropdown

   - Compare across different eras
   - Focus on specific parliamentary sessions

3. **Hover for Details**: Mouse over any chart element

   - See exact values
   - Get contextual information

4. **Click Legend Items**: Toggle specific items on/off
   - Focus on specific parties or types
   - Reduce visual clutter

---

## 📈 Insights

### Major Finding: Cash Dominance

- Cash donations account for 72% of all funding (£1.1B of £1.55B)
- Shows reliance on direct monetary contributions
- Other types (sponsorship, bequests) are relatively small

### Party Funding Variations

- Major parties (Conservative, Labour) receive significantly more
- Smaller parties receive funding from diverse sources
- Regional parties (SNP, Plaid Cymru) have distinct donor bases

### Public Funding Contribution

- Public funds represent £251M (16% of total)
- Important supplement to private donations
- Shows mixed public/private funding model

### Donor Concentration

- Top 10 donors provide ~£X million (concentrated funding)
- Long tail of small individual donors
- Corporate donors vs individual donors show different patterns

---

## 🛠️ Technical Details

### Centralized Formatting System

All political donations dashboards now use a centralized formatting system located in `visuals/formatting_reference.py`. This ensures consistent styling across all visualizations and enables easy updates to the visual design.

**Key Features**:

- **COLOR_PALETTE**: Centralized color definitions (25+ named colors)
- **CSS_STYLES**: Parameterized CSS template with gradient headers, cards, badges
- **Helper Functions**: `get_styled_html()`, `create_stat_card_html()`, `create_badge_html()`
- **Preset Templates**: `get_political_donations_styled_html()` for donations dashboards
- **Utility Functions**: `format_currency()`, `format_number()` for consistent formatting

**Styling Consistency**:

- Gradient header: `linear-gradient(135deg, #1a237e 0%, #283593 50%, #3f51b5 100%)`
- Donation type colors: Cash (#4CAF50), Non-Cash (#2196F3), Sponsorship (#FF9800), etc.
- Component-based design with reusable CSS classes
- Responsive grid layouts

**Benefits**:

- Single source of truth for styling
- Easy to update all dashboards by changing formatting_reference.py
- Reduces code duplication (eliminated 300+ lines of duplicate CSS)
- Maintains visual consistency with cabinet analysis dashboards

### Scripts

**`visuals/political_donations_interactive.py`**

- Main script for party-specific dashboards
- Uses Electoral Commission data
- Generates interactive Plotly visualizations
- Creates dropdown filters for time-period analysis
- **Uses formatting_reference module for styling**
- Output: 14 HTML files

**`visuals/political_donations_summary_dashboard.py`**

- Creates comprehensive overview dashboard
- 6-panel analytics grid
- Key statistics cards
- Color-coded styling
- **Uses formatting_reference module for styling**
- Output: 1 HTML file

### Data Source

- **Path**: `data_sources/dashboard_demo_readonly/output/cleaned_donations.csv`
- **Format**: CSV with cleaned/normalized data
- **Records**: 90,006 donation entries
- **Columns**: Value, AcceptedDate, CleanedDonorName, CleanedRegulatedEntityName, DonationType, etc.

### Technology Stack

- **Python 3.8+**
- **Plotly** - Interactive visualizations
- **Pandas** - Data processing
- **HTML/CSS** - Professional styling

---

## ✅ Verification Checklist

After regenerating visualizations, verify:

- [ ] 14 donation HTML files exist in `generated_charts/`
- [ ] Summary dashboard loads without errors
- [ ] Party dashboards have time-period dropdowns
- [ ] Charts are interactive (hover tooltips work)
- [ ] Color coding matches donation types
- [ ] Statistics totals are accurate
- [ ] No console errors in browser
- [ ] File sizes are reasonable (30KB - 5MB)

---

## 📚 Related Documentation

- [VISUALIZATION_UPDATE_SUMMARY.txt](../VISUALIZATION_UPDATE_SUMMARY.txt) - Detailed feature documentation
- [README.md](../README.md) - Project overview
- [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md) - Full documentation index
- [DEVELOPER_REFERENCE.md](../DEVELOPER_REFERENCE.md) - Development workflows

---

## 📊 Sample Usage

### Scenario 1: Understand Overall Funding Landscape

1. Open `political_donations_summary_dashboard.html`
2. Review statistics cards
3. Check top donors and party rankings
4. Examine temporal trends

### Scenario 2: Compare Conservative and Labour Funding

1. Open `donations_by_party_conservative_and_unionist_party.html`
2. Note funding patterns
3. Switch to `donations_by_party_labour_party.html`
4. Compare side-by-side in notes/spreadsheet

### Scenario 3: Investigate Donation Type Distribution

1. Open `donations_donor_type_analysis.html`
2. Examine breakdown by party
3. Check which types dominate
4. Identify any unusual patterns

### Scenario 4: Analyze Temporal Trends

1. Open `donations_time_analysis.html`
2. Look for seasonal patterns
3. Identify major funding events
4. Note correlations with political events

---

**Last Generated**: January 16, 2026  
**Data Currency**: Through October 29, 2025  
**Next Update**: Run scripts to refresh with latest Electoral Commission data
