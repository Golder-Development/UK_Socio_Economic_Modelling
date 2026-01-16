# GitHub Pages Compatibility - Quick Reference

## ✅ Fixed Files

### Political Donations (COMPLETE ✅)
- [x] `visuals/political_donations_interactive.py` - All charts now use CDN
- [x] Filenames sanitized (removed dots, parentheses, special characters)
- [x] New files: `donations_by_party_democratic_unionist_party_dup.html`
- [x] Old problematic files deleted

### Pension Analysis (COMPLETE ✅)  
- [x] `visuals/pension_reform_impact_analysis.py` - Uses CDN + Path()
- [x] `visuals/final_year_pension_analysis.py` - Uses CDN + Path()

### Infrastructure (COMPLETE ✅)
- [x] `.nojekyll` file created
- [x] `generated_charts/index.html` navigation page created
- [x] `visuals/check_github_pages_compatibility.py` validation tool created

## ⚠️ Files Needing Regeneration

### Mortality Dashboards
The following files still have embedded Plotly and need regeneration:

**Scripts to update:**
- `data_sources/mortality_stats/development_code/create_interactive_mortality_dashboard.py`
- `data_sources/mortality_stats/development_code/create_mortality_dashboards.py`
- `data_sources/mortality_stats/development_code/create_age_group_mortality_dashboard.py`

**Change needed:** Add `include_plotlyjs='cdn'` to all `fig.write_html()` calls

**Current files affected:**
- mortality_dashboard_interactive.html (~11.8MB with embedded Plotly)
- mortality_dashboard_filtered.html
- mortality_dashboard_drilldown.html
- mortality_dashboard_by_age_group.html
- mortality_dashboard_age_*.html (7 files)

**To fix:**
```python
# OLD (embeds full library)
fig.write_html(output_path)
fig.write_html(path, config={'displayModeBar': True})

# NEW (uses CDN)
fig.write_html(output_path, include_plotlyjs='cdn')
fig.write_html(path, include_plotlyjs='cdn', config={'displayModeBar': True})
```

### Other Files
- `cabinet_ministers_tenure_parliament_20260115_132049.html` - timestamped file, may not need fixing

## 🎯 Priority Actions

### HIGH PRIORITY (Do Now)
1. ✅ Delete old problematic filenames
2. ✅ Add `.nojekyll` to root
3. ✅ Create navigation index.html
4. ✅ Fix political donations scripts
5. ✅ Fix pension analysis scripts

### MEDIUM PRIORITY (When Time Permits)
1. ⚠️ Update mortality dashboard scripts to use CDN
2. ⚠️ Regenerate all mortality dashboards
3. ⚠️ Verify file sizes are under 10MB each

### LOW PRIORITY (Optional)
1. Update cabinet analysis scripts if they're regenerated frequently
2. Add more comprehensive error handling to validation script

## 📊 Current Status

### Compatible Files ✅
- All new political donation charts (5 files)
- pension_reform_impact.html (when regenerated)
- final_year_pension_analysis.html (when regenerated)
- index.html
- All cabinet analysis files (no changes needed, working fine)
- All mind map visualizations (working fine)

### Files to Regenerate ⚠️
- 15 mortality dashboard files

### Validation Results
```
Total HTML files: 33
Compatible: 18
Need regeneration: 15
```

## 🚀 Quick Deploy Checklist

Before pushing to GitHub:
- [x] `.nojekyll` exists in root
- [x] `generated_charts/index.html` exists
- [x] Political donation charts regenerated
- [ ] Mortality dashboards regenerated (optional but recommended)
- [x] Run `python visuals/check_github_pages_compatibility.py`
- [x] Verify no files exceed 90MB
- [x] Test index.html locally

## 📝 Notes

**Why CDN matters:**
- Embedded Plotly = 3MB+ per file
- CDN reference = ~5KB per file
- 600x size reduction!

**GitHub Pages limits:**
- Max file size: 100MB (we target < 90MB)
- Max total repository size: 1GB
- No server-side processing

**Filename best practices:**
- Lowercase only
- Underscores for spaces
- No dots except .html
- No parentheses or special characters

## 🔗 Resources

- Validation script: `visuals/check_github_pages_compatibility.py`
- Full documentation: `GITHUB_PAGES_FIXES.md`
- Navigation page: `generated_charts/index.html`
- Live site (after deploy): https://golder-development.github.io/UK_Socio_Economic_Modelling/generated_charts/
