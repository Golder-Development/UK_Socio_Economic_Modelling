# Cabinet Ministers Tenure vs Parliament Duration - Interactive Visualization

## Overview

This interactive Plotly visualization analyzes the relationship between ministerial tenure duration and parliament session length across all UK government appointments from 1945 to present.

## Generated File

**Location**: `generated_charts/cabinet_ministers_tenure_parliament_YYYYMMDD_HHMMSS.html`

**Size**: ~5.8 MB (standalone HTML, no external dependencies required)

**Type**: Interactive scatter plot with dropdown filtering

## Visualization Features

### Scatter Plot

- **X-Axis**: Parliament Duration (in days)
- **Y-Axis**: Ministerial Tenure (in days)
- **Data Points**: Each dot represents one ministerial appointment
- **Total Points**: 3,658 appointments across 1,156 unique ministers

### Color Coding by Political Party

| Party            | Color                | Count | %     |
| ---------------- | -------------------- | ----- | ----- |
| Conservative     | Blue (#0087DC)       | 2,294 | 61.3% |
| Labour           | Red (#E4003B)        | 1,329 | 35.5% |
| Liberal Democrat | Orange (#FAA61A)     | 77    | 2.1%  |
| Crossbench       | Grey (#999999)       | 2     | 0.1%  |
| Other            | Light Grey (#CCCCCC) | 4     | 0.1%  |

### Parliament Filter (Dropdown Menu)

Located at the top-left of the visualization, allowing you to:

- **"All Parliaments"**: View all data points simultaneously
- **Individual Sessions**: Select specific parliament sessions (1945-2019) to focus on:
  - 1945, 1950, 1951, 1955, 1959, 1964, 1966, 1970, 1974 (Feb), 1974 (Oct), 1979, 1983, 1987, 1992, 1997, 2001, 2005, 2010, 2015, 2017, 2019

Each parliament is labeled with its year and exact start date.

### Interactive Hover Tooltips

When you hover over a data point, you see:

- Minister's name (first and last name)
- Government post/position held
- Tenure duration (in days and months)
- Parliament year
- Parliament duration (in days and years)
- Prime Minister in office
- Political party affiliation

### Legend Controls

Click on party names in the legend (right side) to:

- Hide/show specific parties
- Isolate data for party-specific analysis
- Compare patterns between parties

### Plotly Toolbar Features (Top-Right)

- **Zoom**: Click and drag to zoom into specific regions
- **Pan**: Move around after zooming
- **Box/Lasso Select**: Select specific data points
- **Reset Axes**: Return to original view
- **Download**: Save the chart as a PNG image

## Key Statistics

### Tenure Analysis

| Metric          | Value                    |
| --------------- | ------------------------ |
| Average Tenure  | 615 days (~20.5 months)  |
| Median Tenure   | 484 days                 |
| Shortest Tenure | 1 day                    |
| Longest Tenure  | 5,388 days (~14.8 years) |

### Parliament Analysis

| Metric            | Value                    |
| ----------------- | ------------------------ |
| Average Duration  | 1,586 days (~4.34 years) |
| Median Duration   | 1,740 days               |
| Shortest Duration | 204 days                 |
| Longest Duration  | 2,226 days (~6.10 years) |

### Dataset Coverage

- **Total Appointments**: 3,658
- **Unique Ministers**: 1,156
- **Parliament Sessions**: 21
- **Time Span**: 1945 to 2025

## Use Cases & Insights

### 1. **Correlation Analysis**

Observe whether ministerial tenure relates to parliament length. Do shorter parliaments lead to higher ministerial turnover?

### 2. **Party Comparisons**

Compare color clusters to see if Conservative or Labour ministers serve longer/shorter terms on average.

### 3. **Parliamentary Cycles**

Use the dropdown to examine specific parliament periods and identify which had the highest ministerial stability.

### 4. **Outlier Detection**

Spot ministers with unusually long (e.g., 14+ years) or short (1 day) tenures and investigate specific cases.

### 5. **Historical Trends**

Compare ministerial appointment patterns across different prime ministers and party governments.

### 6. **Post-Specific Analysis**

Identify which government posts have longer/shorter average tenures.

## How to Use

### Opening the File

1. Locate the HTML file in `generated_charts/` folder
2. Double-click to open in your default web browser
3. Or right-click → "Open with" → Choose your preferred browser

### Exploring the Data

1. **Start with All Parliaments**: Default view shows all 3,658 appointments
2. **Select a Parliament**: Use the dropdown to focus on a specific session
3. **Hover to Inspect**: Move mouse over dots to see detailed information
4. **Filter by Party**: Click legend items to show/hide parties
5. **Zoom & Pan**: Drag to zoom into areas of interest
6. **Export**: Use the download icon to save the chart as an image

## Technical Details

- **Library**: Plotly (Python)
- **Format**: Standalone HTML (no server/internet required)
- **Browser Compatibility**: Chrome, Firefox, Safari, Edge (modern versions)
- **Data Source**: Parliament API via `pdpy` package
- **Data Processing**: Python pandas

## Regenerating the Visualization

To create a fresh visualization with updated data:

```bash
python data_sources/parliament/create_tenure_visualization.py
```

This will:

- Load the latest `cabinet_ministers.csv` dataset
- Generate a new interactive visualization
- Save it with a new timestamp to `generated_charts/`
- Display summary statistics in the console

## Data Quality Notes

- Some party affiliations are missing (NaN) where historical records are incomplete
- All government roles are included (not just Cabinet-level positions)
- Posts range from senior ministerial roles to Parliamentary Whips
- Multiple roles held simultaneously are recorded as separate entries
- Tenure is calculated as days between start_date and end_date

## Related Files

- **Data Source**: `data_sources/parliament/extract_*/cabinet_ministers.csv`
- **Script**: `data_sources/parliament/create_tenure_visualization.py`
- **Documentation**: `data_sources/parliament/CABINET_MINISTERS_README.md`

## Questions & Analysis Ideas

This visualization can help answer:

- How does parliament length affect ministerial turnover?
- Do certain parties keep ministers in post longer?
- Which parliaments had the most ministerial instability?
- How have appointment patterns changed over time?
- What's the typical tenure for different types of posts?
- Are there party-specific patterns in tenure length?
