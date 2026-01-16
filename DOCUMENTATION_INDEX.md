# Documentation Index

## Quick Navigation

### For Understanding Project Structure

**Start Here**: [REPOSITORY_ARCHITECTURE.md](REPOSITORY_ARCHITECTURE.md)

- Overview of this project vs related project
- Data independence principles
- Integration guidelines
- Quick links to all resources

### For Daily Development Work

**Start Here**: [DEVELOPER_REFERENCE.md](DEVELOPER_REFERENCE.md)

- Quick setup instructions
- Running scripts
- Code reuse patterns
- Troubleshooting
- One-line commands

### For Parliament Data Specifics

**Start Here**: [data_sources/parliament/QUICK_REFERENCE.md](data_sources/parliament/QUICK_REFERENCE.md)

- How to run parliament scripts
- Output file locations
- Sample data
- Using outputs in other scripts

### For Related Project Information

**Start Here**: [data_sources/parliament/RELATED_REPOSITORIES.md](data_sources/parliament/RELATED_REPOSITORIES.md)

- Details about dashboard_demo repository
- How projects relate
- What each project focuses on
- Maintaining separately while referencing

---

## Project Documents by Topic

### Cabinet Ministers Data

- [data_sources/parliament/CABINET_MINISTERS_README.md](data_sources/parliament/CABINET_MINISTERS_README.md) - Dataset schema and statistics
- [cabinet_ministers.py](data_sources/parliament/cabinet_ministers.py) - Data extraction script

### Parliament Analysis

- [data_sources/parliament/QUICK_REFERENCE.md](data_sources/parliament/QUICK_REFERENCE.md) - Parliament script usage
- [build_sos_churn_by_parliament.py](visuals/build_sos_churn_by_parliament.py) - SoS turnover analysis
- [data_sources/parliament/most recent output/README.md](data_sources/parliament/most recent output/README.md) - Output file descriptions

### Political Donations Analysis

- [political_donations_interactive.py](visuals/political_donations_interactive.py) - Party-specific dashboards and aggregate analyses
- [political_donations_summary_dashboard.py](visuals/political_donations_summary_dashboard.py) - Comprehensive overview dashboard
- **Generated Files** (in `generated_charts/`):
  - `political_donations_summary_dashboard.html` - Main overview with 6-panel analytics
  - `donations_by_party_*.html` - Individual dashboards for 9 major parties
  - `donations_by_party_summary.html` - Cross-party comparison
  - `donations_donor_type_analysis.html` - Breakdown by donation type
  - `donations_time_analysis.html` - Temporal trend analysis
  - `donations_party_heatmap.html` - Comparative heatmap

### Visualizations

- [create_tenure_visualization.py](data_sources/parliament/create_tenure_visualization.py) - Interactive Plotly visualization
- [generated_charts/README.md](generated_charts/README.md) - Chart documentation

### Repository Coordination

- [REPOSITORY_ARCHITECTURE.md](REPOSITORY_ARCHITECTURE.md) - Both projects structure
- [DEVELOPER_REFERENCE.md](DEVELOPER_REFERENCE.md) - Working with both projects
- [data_sources/parliament/RELATED_REPOSITORIES.md](data_sources/parliament/RELATED_REPOSITORIES.md) - Related project details

---

## Key External Reference

**Dashboard Demo Repository**

- URL: https://github.com/Golder-Development/dashboard_demo
- Purpose: Broader parliamentary analysis, member utilities
- Relationship: Separate project with shared patterns
- How to Use: Reference patterns, copy code when helpful

---

## Common Tasks

### I want to...

**Understand the overall project architecture**
→ Read [REPOSITORY_ARCHITECTURE.md](REPOSITORY_ARCHITECTURE.md)

**Extract latest cabinet minister data**
→ Run: `python data_sources/parliament/cabinet_ministers.py`
→ Then: Check [CABINET_MINISTERS_README.md](data_sources/parliament/CABINET_MINISTERS_README.md)

**Analyze Secretary of State churn**
→ Run: `python visuals/build_sos_churn_by_parliament.py`
→ Then: Check [QUICK_REFERENCE.md](data_sources/parliament/QUICK_REFERENCE.md)

**Create visualization**
→ Run: `python data_sources/parliament/create_tenure_visualization.py`
→ Output: `generated_charts/cabinet_ministers_tenure_parliament_*.html`

**Generate political donations dashboards**
→ Run: `python visuals/political_donations_interactive.py` (party-specific)
→ Run: `python visuals/political_donations_summary_dashboard.py` (overview)
→ Output: `generated_charts/political_donations_*.html` (multiple files)

**Find parliament periods data**
→ Location: `data_sources/parliament/most recent output/parliaments_periods.json`
→ Docs: [most recent output/README.md](data_sources/parliament/most recent output/README.md)

**Reference code from dashboard_demo**
→ Guide: [DEVELOPER_REFERENCE.md](DEVELOPER_REFERENCE.md) - Code Reuse section
→ Details: [RELATED_REPOSITORIES.md](data_sources/parliament/RELATED_REPOSITORIES.md)

**Coordinate changes with dashboard_demo**
→ See: [REPOSITORY_ARCHITECTURE.md](REPOSITORY_ARCHITECTURE.md) - Coordination section
→ Details: [RELATED_REPOSITORIES.md](data_sources/parliament/RELATED_REPOSITORIES.md)

---

## File Locations Summary

### Root Documentation

```
REPOSITORY_ARCHITECTURE.md         ← Project structure & both repos
DEVELOPER_REFERENCE.md              ← Daily work guide
SCRIPT_UPDATE_SUMMARY.md            ← Recent script updates
VISUALIZATION_UPDATE_SUMMARY.txt    ← Visualization features (Cabinet + Political Donations)
```

### Parliament Data Folder

```
data_sources/parliament/
├── README.md                       ← pdpy basics + related repo link
├── QUICK_REFERENCE.md              ← Parliament scripts guide
├── RELATED_REPOSITORIES.md         ← dashboard_demo details
├── CABINET_MINISTERS_README.md     ← Dataset documentation
├── cabinet_ministers.py            ← Extract script
├── build_sos_churn_by_parliament.py ← Churn analysis
├── create_tenure_visualization.py  ← Visualization
├── most recent extract/
│   └── cabinet_ministers.csv       ← Latest data
└── most recent output/
    ├── README.md
    ├── parliamentary_churn_summary.csv
    ├── parliaments_periods.json    ← Cached parliament dates
    └── sos_churn_bar.jpg           ← Churn chart
```

### Generated Outputs

```
generated_charts/
├── cabinet_ministers_tenure_parliament_*.html ← Interactive viz
├── political_donations_summary_dashboard.html  ← Donations overview
├── donations_by_party_*.html                   ← Party-specific dashboards
├── donations_by_party_summary.html             ← Party comparison
├── donations_donor_type_analysis.html          ← Type breakdown
├── donations_time_analysis.html                ← Temporal trends
├── donations_party_heatmap.html                ← Comparative heatmap
└── README.md
```

---

## Documentation Status

| Document                     | Purpose              | Status      | Last Updated |
| ---------------------------- | -------------------- | ----------- | ------------ |
| REPOSITORY_ARCHITECTURE.md   | Project overview     | ✅ Complete | 2026-01-15   |
| DEVELOPER_REFERENCE.md       | Daily workflows      | ✅ Complete | 2026-01-15   |
| RELATED_REPOSITORIES.md      | Related project info | ✅ Complete | 2026-01-15   |
| QUICK_REFERENCE.md           | Parliament scripts   | ✅ Complete | Previously   |
| CABINET_MINISTERS_README.md  | Cabinet dataset      | ✅ Complete | Previously   |
| most recent output/README.md | Output files         | ✅ Complete | Previously   |
| political_donations_interactive.py | Donations script | ✅ Complete | 2026-01-16   |
| political_donations_summary_dashboard.py | Dashboard script | ✅ Complete | 2026-01-16   |

---

## Quick Links

**This Project**:

- Cabinet Ministers: `data_sources/parliament/most recent extract/cabinet_ministers.csv`
- Parliament Periods: `data_sources/parliament/most recent output/parliaments_periods.json`
- Churn Summary: `data_sources/parliament/most recent output/parliamentary_churn_summary.csv`
- Cabinet Visualization: `generated_charts/cabinet_ministers_tenure_parliament_*.html`
- Donations Summary: `generated_charts/political_donations_summary_dashboard.html`
- Party Donations: `generated_charts/donations_by_party_*.html`
- Donations Data: `data_sources/dashboard_demo_readonly/output/cleaned_donations.csv`

**Related Project**:

- Repository: https://github.com/Golder-Development/dashboard_demo
- Documentation: Check repo directly

---

## Getting Help

### Understanding a Document

Each document has:

- Clear purpose statement at the top
- Table of contents (if long)
- Examples where helpful
- Links to related documents

### Finding Specific Information

Use the **"I want to..."** section above to find the right document

### Documentation Principles

- ✅ Each document has a specific purpose
- ✅ Documents link to related resources
- ✅ Examples provided for technical content
- ✅ Clear file locations and commands
- ✅ Separate projects documented as independent

---

**Last Updated**: January 16, 2026  
**Status**: Complete with Political Donations visualizations  
**Audience**: Developers, analysts, data engineers
