# UK Mortality Statistics - Complete Dataset Summary

## Historical ICD Imports (1901–2000)

Some historical ONS Excel files spread a single era across multiple worksheets. The importer now merges all relevant worksheets for each ICD era to ensure complete coverage:

- ICD2–IC6: Each era spans 2 worksheets; both are read and concatenated.
- ICD7–IC9: Each era spans 3 worksheets; all three are read and concatenated.

Implementation details:

- The loader in `data_sources/mortality_stats/build_comprehensive_mortality_1901_2025.py` detects header rows even when they vary across sheets, normalizes the `year` column, and filters plausible year ranges before merging.
- Non‑data sheets like `metadata`, `description`, `correction notice`, `contents`, and `readme` are excluded.
- Excel dependencies: `.xls` files require `xlrd` and `.xlsx` files require `openpyxl` (added in `requirements/ons.txt`).

Outputs from the comprehensive builder include consolidated historical rows per era, later standardized and aggregated into yearly totals and cause-level tables for 1901–2025.

## 📊 Mortality Rates per 100,000 — Key Update

Recent improvements now provide **age-group-specific mortality rates** using the harmonized population estimates. This prevents misinterpretation of rates that combine different age cohorts.

### Three complementary datasets

1. **`uk_mortality_rates_per_100k_by_cause.csv`**  
   - **Denominator:** Age-group population (e.g., 0-4 age group only)
   - **Column:** `mortality_rate_per_100k_age_group_population`
   - **Use case:** Compare mortality from different causes *within the same age group*
   - **Example:** "Infectious disease deaths per 100k of the 0-4 age group"

2. **`uk_mortality_rates_per_100k_by_age_group.csv`** *(NEW)*  
   - **Denominator:** Age-group population (all causes combined)
   - **Column:** `mortality_rate_per_100k_age_group_population`
   - **Use case:** Compare mortality *across age groups*
   - **Example:** "Total deaths per 100k in the 85+ age group vs. 0-4 age group"

3. **`uk_mortality_rates_per_100k_yearly_totals.csv`**  
   - **Denominator:** Total population (all ages, all causes)
   - **Column:** `mortality_rate_per_100k_total_population`
   - **Use case:** High-level annual trends in overall population mortality
   - **Example:** "Overall mortality in 2000 was 1,031.6 per 100,000 (all ages)"

**⚠️ Critical:** Each file includes explicit column names (`mortality_rate_per_100k_age_group_population`, `mortality_rate_per_100k_total_population`) to avoid confusion about which denominator was used.

---

## ✅ What You Now Have

### 1. **Total Deaths by Year: 1901-2000** (100 years)

**File:** `uk_mortality_comprehensive_1901_2025_harmonized.csv` (merged with population)

```text
Year Range: 1901 - 2000
Total Records: 37,897 (cause/sex/age breakdown)
Coverage: 100% complete for this period
Data Quality: Historical ICD harmonized + modern harmonization
```

### 2. **Deaths by Age Group & Cause (Harmonized): 1901-2000**

**File:** `uk_mortality_rates_per_100k_by_cause.csv`

- 29,452 records combining cause, sex, and age-group denominators
- Rates calculated using the harmonized 10-age-group system (0-4, 5-14, …, 85+)
- Column: `mortality_rate_per_100k_age_group_population` ← **explicitly labelled**

### 3. **Deaths by Age Group (All Causes): 1901-2000** *(NEW)*

**File:** `uk_mortality_rates_per_100k_by_age_group.csv`

- 2,000 records (1901-2000 × 10 age groups × 2 sexes)
- Aggregated across all causes for each age group
- Column: `mortality_rate_per_100k_age_group_population` ← **explicitly labelled**
- Shows dramatic variation: e.g., 85+ male rate ~18,824 per 100k in 2000 vs. 0-4 males ~4,948

### 4. **Yearly Total Mortality (All Ages, All Causes): 1901-2000**

**File:** `uk_mortality_rates_per_100k_yearly_totals.csv`

- 100 records (1901-2000)
- Column: `mortality_rate_per_100k_total_population` ← **explicitly labelled**
- Shows overall trend: 1691.4 per 100k in 1901 → 1031.6 in 2000 (historical improvement)

---

## 📊 Data Sources Used

| Source | Years | Type | Status |
|--------|-------|------|--------|
| uk_mortality_comprehensive_1901_2025_harmonized.csv | 1901-2000 | Harmonized cause/sex/age | ✅ Local |
| uk_population_harmonized_age_groups.csv | 1901-2016 | Population by age group & sex | ✅ Local |
| ONS API - 2010-19 edition | 2010-2019 | Weekly totals aggregated | ✅ Merged |
| ONS API - COVID-19 edition | 2020-2023 | Weekly totals aggregated | ✅ Merged |
| ONS API - 2024 & 2025 editions | 2024-2025 | Weekly totals aggregated | ✅ Merged |

---

## 📈 Usage Examples

### Compare mortality across age groups (same year)

```python
import pandas as pd

df = pd.read_csv('uk_mortality_rates_per_100k_by_age_group.csv')

# Get 2000 data by age group
year_2000 = df[df['year'] == 2000]
males_by_age = year_2000[year_2000['sex'] == 'Male'].sort_values('mortality_rate_per_100k_age_group_population')

# Clear label: these are per 100k of *each age group*
print("Male mortality rates per 100,000 (of age-group population):")
for _, row in males_by_age.iterrows():
    print(f"  {row['age_group']}: {row['mortality_rate_per_100k_age_group_population']:.1f}")
# Output shows: 0-4 → 4,948; 5-14 → 125; ...; 85+ → 18,824
```

### Compare causes within an age group

```python
by_cause = pd.read_csv('uk_mortality_rates_per_100k_by_cause.csv')

# Infectious disease in 0-4 age group, 2000
subset = by_cause[(by_cause['year'] == 2000) & 
                  (by_cause['age_group'] == '0-4')]
top_causes = subset.nlargest(5, 'mortality_rate_per_100k_age_group_population')

# Again: explicitly per 100k of the 0-4 age group
for _, row in top_causes.iterrows():
    print(f"{row['cause']}: {row['mortality_rate_per_100k_age_group_population']:.1f} per 100k (0-4 population)")
```

### Overall population trend

```python
yearly = pd.read_csv('uk_mortality_rates_per_100k_yearly_totals.csv')

# Plot overall rate over time
# This uses total population as denominator (all ages combined)
print(f"Overall mortality in 1901: {yearly.loc[yearly['year'] == 1901, 'mortality_rate_per_100k_total_population'].values[0]:.1f} per 100k")
print(f"Overall mortality in 2000: {yearly.loc[yearly['year'] == 2000, 'mortality_rate_per_100k_total_population'].values[0]:.1f} per 100k")
print("Note: denominator is total population (all ages combined)")
```

---

## ⚠️ **Denominator Clarity Guide**

To avoid mixing apples and oranges, **always check which rate column you're using**:

| File | Rate Column | Denominator | Use When | Example |
|------|------------|-------------|----------|---------|
| by_cause | `mortality_rate_per_100k_age_group_population` | Population of that age group | Comparing causes within an age group | "Is TB deadlier than malaria in 85+ year-olds?" |
| by_age_group | `mortality_rate_per_100k_age_group_population` | Population of that age group | Comparing age groups to each other | "Are elderly (85+) 5× deadlier than children (0-4)?" |
| yearly_totals | `mortality_rate_per_100k_total_population` | Total population (all ages) | Long-term population-wide trends | "Has population mortality improved since 1901?" |

**Incorrect comparison example:**  
❌ *"In 2000, cause X had rate 500 per 100k (85+ age group) while cause Y had rate 50 per 100k (0-4 age group)"*  
→ These are incomparable denominators!

**Correct comparison:**  
✅ *"In 2000, cause X had rate 500 per 100k of 85+ population, and cause Y had rate 50 per 100k of 0-4 population"*  
→ Now the denominator is explicit and comparison is valid within each age group.

---

## 📈 Usage Examples — Original

### Analyze trends (long-term population mortality)

```python
import pandas as pd

df = pd.read_csv('uk_mortality_rates_per_100k_yearly_totals.csv')

# Year-on-year change in overall population mortality
df['yoy_change'] = df['mortality_rate_per_100k_total_population'].pct_change() * 100

# Pre-2000 vs 2000
pre_2000_avg = df[df['year'] < 2000]['mortality_rate_per_100k_total_population'].mean()
year_2000 = df[df['year'] == 2000]['mortality_rate_per_100k_total_population'].values[0]
print(f"Average (1901-1999): {pre_2000_avg:.1f} per 100,000 (total population)")
print(f"Year 2000: {year_2000:.1f} per 100,000 (total population)")
print(f"Improvement: {(1 - year_2000/pre_2000_avg)*100:.1f}%")
```

### Compare causes of death

```python
causes = pd.read_csv('uk_mortality_by_cause.csv')

# Top causes by year
top_2010 = causes[causes['year'] == 2010].nlargest(10, 'total_deaths')
top_2017 = causes[causes['year'] == 2017].nlargest(10, 'total_deaths')

# Trend for circulatory diseases
circulatory = causes[causes['icd10_chapter'] == 'I'].sort_values('year')
```

---

## 🔍 Data Gaps & Next Steps

### Current Gaps

1. **2018-2019 by cause:** Only have totals (cause breakdown not in API)
2. **Pre-2001 data:** Not included (need manual historical downloads)

### How to fill pre-2001 gap

**Manual Download Option:**

1. Visit: https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/deaths/datasets
2. Look for datasets with coverage back to 1970s or earlier
3. Download Excel/CSV files
4. Save to: `data_sources/mortality_stats/ons_downloads/`
5. Run `analyze_comprehensive_mortality.py` again from `data_sources/mortality_stats/development_code` with updated load functions

**Recommended datasets to look for:**

- "Deaths registered in England and Wales" (annual series - should have 1970+ data)
- "Historical mortality data" (check adhoc releases)
- "Mortality by cause tables" (if available historically)

---

## 📁 Generated Files

| File | Records | Years | Purpose |
|------|---------|-------|---------|
| `uk_mortality_comprehensive.csv` | 25 | 2001-2025 | Yearly death totals |
| `uk_mortality_by_cause.csv` | 402 | 2001-2017 | Deaths by ICD-10 cause |
| `uk_mortality_totals_by_year.csv` | 16 | 2010-2025 | API-fetched raw data |

---

## 🚀 Running the Analysis

### Running the Comprehensive Builder (1901–2025)

This generates consolidated historical + modern outputs:

- `uk_mortality_comprehensive_1901_2025.zip` (contains `uk_mortality_comprehensive_1901_2025.csv`)
- `uk_mortality_by_cause_1901_2025.zip` (contains `uk_mortality_by_cause_1901_2025.csv`)
- `uk_mortality_yearly_totals_1901_2025.csv`

Steps (Windows, PowerShell):

```powershell
# Activate project venv (if present)
& H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/Activate.ps1

# Install dependencies (includes xlrd/openpyxl for Excel)
pip install -r requirements.txt

# Run the comprehensive builder
python data_sources/mortality_stats/build_comprehensive_mortality_1901_2025.py
```

Outputs are saved in `data_sources/mortality_stats/`.
To use the zipped files directly in Python:

```python
import zipfile, pandas as pd
from pathlib import Path

zip_path = Path('data_sources/mortality_stats/uk_mortality_by_cause_1901_2025.zip')
with zipfile.ZipFile(zip_path) as zf:
 with zf.open('uk_mortality_by_cause_1901_2025.csv') as f:
  df = pd.read_csv(f)
```

### Fetch fresh API data (optional)

Use these scripts if newer weekly/annual ONS releases become available for 2001–2025:

```powershell
cd data_sources/mortality_stats/development_code
python fetch_uk_mortality_stats.py
```

---

## Notes

- All data represents **England and Wales** (not UK total - Scotland and Northern Ireland data separate)
- 2025 data is **partial** (only up to week 49/50)
- Cause of death data uses **ICD-10 classification** (standard medical coding)
- Sources de-duplicated to avoid double-counting in overlap years
- Weekly data aggregated to yearly totals for main dataset
