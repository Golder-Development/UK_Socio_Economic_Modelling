# Chart Recreation Guide

This document maps each chart in `generated_charts/` to the script that creates it, ensuring all outputs can be recreated.

## Status: ✅ ALL CHARTS CAN BE RECREATED

Last verified: January 16, 2026
Last updated: Added Political Donations Interactive Suite (13 charts)

---

## Political Donations Analysis

### NEW: Interactive Political Donations Suite

- **Outputs**: 
  - `generated_charts/donations_by_party_summary.html` (all parties comparison)
  - `generated_charts/donations_donor_type_analysis.html` (donor type trends)
  - `generated_charts/donations_time_analysis.html` (temporal patterns)
  - `generated_charts/donations_party_heatmap.html` (comparative metrics)
  - `generated_charts/donations_by_party_<PARTY>.html` (9 party-specific dashboards)
- **Script**: `visuals/political_donations_interactive.py`
- **Command**: `python visuals/political_donations_interactive.py`
- **Features**:
  - Time period filters (by year, quarter, month)
  - Donor type breakdowns (Cash, Non-Cash, Sponsorship, Public Funds, Bequests)
  - Party-specific and comparative views
  - Donor concentration and loyalty metrics
  - Interactive heatmaps and trend analysis
- **Data Source**: `data_sources/dashboard_demo_readonly/source/Donations_accepted_by_political_parties.csv`
- **Status**: ✅ Active (Created: January 16, 2026)

---

## Cabinet & Political Analysis Charts

### 1. Cabinet Churn Report

- **Output**: `generated_charts/cabinet_churn_report.html`
- **Script**: `visuals/build_cabinet_churn_report.py`
- **Command**: `python visuals/build_cabinet_churn_report.py`
- **Status**: ✅ Active

### 2. Individual Cabinet Analysis

- **Output**: `generated_charts/individual_cabinet_analysis.html`
- **Script**: `visuals/analyze_individual_cabinet_tenure.py`
- **Command**: `python visuals/analyze_individual_cabinet_tenure.py`
- **Data Output**: `generated_charts/cabinet_members_tenure_profile.csv`
- **Status**: ✅ Active

### 3. Cabinet Ministers Tenure by Parliament

- **Output**: `generated_charts/cabinet_ministers_tenure_parliament_20260115_132049.html`
- **Script**: `visuals/build_sos_tenure_boxplot.py`
- **Command**: `python visuals/build_sos_tenure_boxplot.py`
- **Status**: ✅ Active

---

## Election & Pension Analysis

### 4. Election Pension Theory Analysis

- **Output**: `generated_charts/election_pension_theory_analysis.html`
- **Script**: `visuals/analyze_election_pension_theory.py`
- **Command**: `python visuals/analyze_election_pension_theory.py`
- **Data Outputs**:
  - `generated_charts/election_cycle_analysis.csv`
  - `generated_charts/months_to_election_analysis.csv`
  - `generated_charts/appointments_detail.csv`
  - `generated_charts/per_election_analysis.csv`
  - `generated_charts/parliamentary_phase_analysis.csv`
- **Status**: ✅ Active

### 5. Final Year Pension Analysis

- **Output**: `generated_charts/final_year_pension_analysis.html`
- **Script**: `visuals/final_year_pension_analysis.py`
- **Command**: `python visuals/final_year_pension_analysis.py`
- **Data Output**: `generated_charts/final_year_analysis.csv`
- **Status**: ✅ Active

### 6. Pension Reform Impact Analysis

- **Output**: `generated_charts/pension_reform_impact.html`
- **Script**: `visuals/pension_reform_impact_analysis.py`
- **Command**: `python visuals/pension_reform_impact_analysis.py`
- **Data Output**: `generated_charts/pension_reform_comparison.csv`
- **Status**: ✅ Active

---

## Political Visualization

### 7. Political Posts Mind Map (2D)

- **Output**: `generated_charts/political_posts_mindmap.html`
- **Script**: `visuals/political_mind_map.py`
- **Command**: `python visuals/political_mind_map.py <path_to_wordpress_export.xml>`
- **Note**: Requires WordPress XML export file
- **Status**: ✅ Active (updated to output to generated_charts)

### 8. Political Posts Mind Map (3D)

- **Output**: `generated_charts/political_posts_mindmap_3d.html`
- **Script**: `data_sources/HysnapsBlog/build_posts_mindmap_3d.py`
- **Command**: `python data_sources/HysnapsBlog/build_posts_mindmap_3d.py`
- **Status**: ✅ Active

---

## Demographic & Economic Analysis

### 9. Lords Membership By Type (1958–Present)

- **Output**: `generated_charts/lords_membership_by_type_1958_present.png`
- **Script**: `visuals/LordsVisuals.py`
- **Command**: `python visuals/LordsVisuals.py`
- **Status**: ✅ Active

### 10. Child Intervention by Tenure

- **Output**: `generated_charts/fig2_child_intervention_by_tenure.png`
- **Script**: `data_sources/HysnapsBlog/rethink_pop_growth_graphs.py`
- **Command**: `python data_sources/HysnapsBlog/rethink_pop_growth_graphs.py`
- **Status**: ✅ Active

### 11. Female Employment vs. Fertility

- **Output**: `generated_charts/fig3_female_employment_vs_fertility.png`
- **Script**: `data_sources/HysnapsBlog/rethink_pop_growth_graphs.py`
- **Command**: `python data_sources/HysnapsBlog/rethink_pop_growth_graphs.py`
- **Status**: ✅ Active

### 12. LGBTQ+ Population vs. Births

- **Output**: `generated_charts/fig4_lgbtq_vs_births.png`
- **Script**: `data_sources/HysnapsBlog/rethink_pop_growth_graphs.py`
- **Command**: `python data_sources/HysnapsBlog/rethink_pop_growth_graphs.py`
- **Status**: ✅ Active

### 13. Change in Cost of Housing vs. Change in Fertility

- **Output**: `generated_charts/Fig5_ChangeInCostOfHousing_vs_ChangeInFertility.png`
- **Script**: `data_sources/HysnapsBlog/rethink_pop_growth_graphs.py`
- **Command**: `python data_sources/HysnapsBlog/rethink_pop_growth_graphs.py`
- **Status**: ✅ Active

---

## Mortality Dashboards

All mortality dashboards are generated by a single script.

### 14. All Mortality Dashboards (13 files)

- **Outputs**:
  - `mortality_dashboard_interactive.html` (main dashboard)
  - `mortality_dashboard_drilldown.html` (cause drill-down)
  - `mortality_dashboard_filtered.html` (age/sex filtered)
  - `mortality_dashboard_by_age_group.html` (by age group)
  - `mortality_dashboard_age_groups.html` (overview)
  - `mortality_dashboard_age_group_by_sex.html` (by age & sex)
  - `mortality_dashboard_age_preschool.html` (≤5)
  - `mortality_dashboard_age_school.html` (6–19)
  - `mortality_dashboard_age_young_adults.html` (20–34)
  - `mortality_dashboard_age_older_adults.html` (35–64)
  - `mortality_dashboard_age_young_oaps.html` (65–84)
  - `mortality_dashboard_age_old_oaps.html` (85+)
  - `icd_code_summary.csv`
- **Script**: `data_sources/mortality_stats/development_code/create_mortality_dashboards.py`
- **Command**: See `data_sources/mortality_stats/SYSTEM_REFERENCE.py` for complete instructions
- **Status**: ✅ Active

---

## Obsolete Scripts (Moved to local_dev)

The following scripts have been moved to `local_dev/` as they are superseded by current versions:

1. **restore_churn_model.py** - Old version of individual analysis
2. **restore_individual_analysis.py** - Old version superseded by v2
3. **restore_individual_analysis_v2.py** - Old version, use analyze_individual_cabinet_tenure.py instead
4. **generate_updated_html.py** - Old temporary script for updating HTML
5. **corrected_pension_analysis.py** - Early iteration, use analyze_election_pension_theory.py
6. **create_q4_analysis.py** - Early iteration, use analyze_election_pension_theory.py
7. **update_pension_theory_html.py** - Old temporary update script
8. **Chatgpt_created.py** - Political donations visualization (unrelated to current outputs)
9. **analyze_post_field.py** - Utility/debug script

---

## Verification Checklist

### All charts in index.md are:

- ✅ Present in generated_charts/
- ✅ Have identified creation scripts
- ✅ Scripts are in active codebase
- ✅ Can be recreated using documented commands

### All scripts in visuals/:

- ✅ Serve active purposes
- ✅ Obsolete scripts moved to local_dev/
- ✅ Output to generated_charts/ directory

---

## Notes

1. **Parliamentary data dependency**: Most cabinet/political analysis scripts depend on:

   - `data_sources/parliament/most recent extract/cabinet_ministers.csv`

2. **Mortality data dependency**: Mortality dashboards require the full data pipeline:

   - See `data_sources/mortality_stats/SYSTEM_REFERENCE.py` for complete setup

3. **Blog content dependency**: Political mind maps require WordPress export files

4. **All active scripts now output to `generated_charts/`** - Confirmed as of this verification

---

## Quick Recreation Commands

To recreate all cabinet/political analysis charts:

```bash
# Cabinet analysis
python visuals/build_cabinet_churn_report.py
python visuals/analyze_individual_cabinet_tenure.py
python visuals/build_sos_tenure_boxplot.py

# Election & pension analysis
python visuals/analyze_election_pension_theory.py
python visuals/final_year_pension_analysis.py
python visuals/pension_reform_impact_analysis.py

# Demographic
python visuals/LordsVisuals.py
python data_sources/HysnapsBlog/rethink_pop_growth_graphs.py
```

To recreate political mind maps (requires WordPress export):

```bash
python visuals/political_mind_map.py <path_to_export.xml>
python data_sources/HysnapsBlog/build_posts_mindmap_3d.py
```
