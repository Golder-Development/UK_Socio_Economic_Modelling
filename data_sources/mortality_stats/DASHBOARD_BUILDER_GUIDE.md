# Generic Mortality Dashboard Builder

## Overview

The `create_mortality_dashboards.py` script is a flexible, reusable command-line tool that generates interactive Plotly dashboards from any UK mortality CSV file.

**Key benefits:**
- Single codebase handles multiple data sources (L1-classified, compiled, by-cause, etc.)
- Command-line arguments specify input file, output directory, category column, and dashboard types
- Significantly reduces code duplication and increases maintainability
- Easy to extend with new dashboard types

---

## Usage

```bash
python create_mortality_dashboards.py <input_csv> [options]
```

### Basic Examples

**Generate all dashboards from L1-classified data:**
```bash
python create_mortality_dashboards.py uk_mortality_by_cause_1901_onwards_L1.csv
```

**Create specific dashboards to custom directory:**
```bash
python create_mortality_dashboards.py uk_mortality_by_cause_1901_onwards_L1.csv \
    --output-dir ./generated_charts \
    --dashboards interactive,age_groups
```

**Create dashboards from compiled (pre-classification) data:**
```bash
python create_mortality_dashboards.py uk_mortality_by_cause_1901_onwards_compiled.csv \
    --category-column cause_description \
    --dashboards drilldown,subset
```

**Create from by-cause data with custom categorization:**
```bash
python create_mortality_dashboards.py mortality_by_cause_raw.csv \
    --category-column icd_description \
    --output-dir ./analysis/dashboards
```

---

## Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `input_csv` | positional | required | Path to input CSV file |
| `--output-dir` | string | `generated_charts` | Output directory for dashboard HTML files |
| `--category-column` | string | `L1_category` | Column name for category grouping |
| `--dashboards` | string | all | Comma-separated list of dashboards to generate |

### Category Column

Automatically detects and uses specified column for grouping data:
- **L1-classified**: `L1_category` (default) - 10 socio-economic categories
- **Compiled data**: `cause_description` - Original ICD descriptions
- **By-cause data**: `icd_code`, `cause_name`, or any custom column

### Available Dashboards

| Type | Description | Best For |
|------|-------------|----------|
| `interactive` | Main category-filtered dashboard with time series | Overview and trend analysis |
| `drilldown` | Top panel: categories, bottom: top 10 sub-categories | Exploring cause hierarchies |
| `filtered` | Age/sex filtered with stacked/unstacked toggle | Demographic breakdowns |
| `age_groups` | Mortality by age group (0-4, 5-14, ... 85+) | Age-specific mortality patterns |
| `subset` | 6 age-based subset dashboards (preschool, school, adults, OAPs) | Specific age cohort analysis |

---

## Data Requirements

Input CSV must contain (minimum):
- `year` - Year of death (numeric)
- `deaths` - Count of deaths (numeric)
- `age` - Age or age range (string)
- `sex` - Male/Female/All (string)
- **Plus one grouping column** (specified by `--category-column`)

Optional columns:
- `cause` - ICD code or cause identifier
- `cause_description` - Descriptive text for causes
- `icd_version` - ICD version (ICD-1 through ICD-10)
- `population` - Population for rate calculations (auto-interpolated if missing)

---

## Example Workflows

### Workflow 1: Generate L1 Classification Dashboards

```bash
# Full L1-classified pipeline
python regenerate_all_data_clean.py

# Or manually:
python create_mortality_dashboards.py uk_mortality_by_cause_1901_onwards_L1.csv \
    --category-column L1_category \
    --output-dir ./generated_charts \
    --dashboards interactive,drilldown,age_groups
```

### Workflow 2: Quick Analysis of Compiled Data

```bash
# Explore raw compiled data before classification
python create_mortality_dashboards.py uk_mortality_by_cause_1901_onwards_compiled.csv \
    --category-column cause_description \
    --dashboards drilldown,subset
```

### Workflow 3: Age-Specific Mortality Analysis

```bash
# Focus only on age group patterns
python create_mortality_dashboards.py uk_mortality_by_cause_1901_onwards_L1.csv \
    --output-dir ./age_analysis \
    --dashboards age_groups,subset
```

---

## Integration in Pipeline

The `regenerate_all_data_clean.py` script automatically calls this builder in Step 4:

```python
# Step 4: Generate dashboards from L1-classified data
result = subprocess.run([
    sys.executable, 'create_mortality_dashboards.py',
    'uk_mortality_by_cause_1901_onwards_L1.csv',
    '--output-dir', 'generated_charts',
    '--category-column', 'L1_category',
    '--dashboards', 'interactive,drilldown,filtered,age_groups,subset'
])
```

To customize, edit the `step_4_generate_dashboards()` function in `regenerate_all_data_clean.py`.

---

## Output Files

All dashboards are generated as standalone HTML files:

```
generated_charts/
├── mortality_dashboard_interactive.html          # Main interactive dashboard
├── mortality_dashboard_drilldown.html             # Drill-down by cause
├── mortality_dashboard_filtered.html              # Age/sex filtered view
├── mortality_dashboard_age_groups.html            # By age group
├── mortality_dashboard_age_preschool.html         # Preschool cohort
├── mortality_dashboard_age_school.html            # School age cohort
├── mortality_dashboard_age_young_adults.html      # 20-34 cohort
├── mortality_dashboard_age_older_adults.html      # 35-64 cohort
├── mortality_dashboard_age_young_oaps.html        # 65-84 cohort
└── mortality_dashboard_age_old_oaps.html          # 85+ cohort
```

---

## Technical Details

### Population Estimates

Death rates are calculated using UK population estimates for:
- Census years: 1901, 1911, 1921, ..., 2021
- Other years: Linearly interpolated between census points

Estimates source: ONS historical population data

### Performance

- **Interactive**: ~10 seconds
- **Drilldown**: ~5 seconds
- **Age Groups**: ~8 seconds
- **Subsets** (6 dashboards): ~30 seconds total

Total time: ~1 minute for all 11 dashboards

### Reusability

Same script can be applied to:
- Different ICD versions
- Different time periods
- Different categorization schemes
- New socio-economic classification schemes
- Custom mortality datasets

---

## Troubleshooting

### "Column not found" error

Ensure the `--category-column` value matches exactly (case-sensitive) an actual column in your CSV.

```bash
# Check available columns:
python -c "import pandas as pd; print(pd.read_csv('your_file.csv').columns.tolist())"
```

### Empty dashboards

Check that your CSV contains data with the expected columns. Verify:
```bash
python -c "import pandas as pd; df = pd.read_csv('your_file.csv'); print(f'Records: {len(df)}'); print(f'Columns: {df.columns.tolist()}')"
```

### Missing population estimates

If your data spans years outside 1901-2021, population will be extrapolated from nearest census year. Provide custom estimates by editing `POPULATION_ESTIMATES` dict in script.

---

## Future Enhancements

- Add `--population-file` argument for custom population data
- Support multiple grouping columns (e.g., `--categories L1_category,icd_version`)
- Add export to static image formats (PNG, PDF)
- Support for streaming large datasets (>10M rows)
