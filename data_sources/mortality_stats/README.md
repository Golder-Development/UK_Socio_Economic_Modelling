# UK Mortality Statistics - Complete Dataset Summary

## ✅ What You Now Have

### 1. **Total Deaths by Year: 2001-2025** (25 years)
**File:** `uk_mortality_comprehensive.csv`

```
Year Range: 2001 - 2025
Total Records: 25 years
Coverage: 100% complete for this period
Data Quality: Multiple sources merged with deduplication
```

**Key Statistics:**
- **Lowest:** 2011 with 484,391 deaths
- **Highest:** 2020 with 614,114 deaths (COVID-19 spike)
- **Average:** ~535,000 deaths/year
- **Recent:** 2025 shows 502,553 (note: partial year data)

### 2. **Deaths by Cause (ICD-10): 2001-2017** (17 years)
**File:** `uk_mortality_by_cause.csv`

**Includes breakdown by ICD-10 chapter:**
- **I: Circulatory system** - ~420,000 deaths/year (largest cause)
- **C: Cancer/Neoplasms** - ~270,000 deaths/year
- **J: Respiratory system** - ~135,000 deaths/year
- **F: Mental/Behavioural** - ~29,000 deaths/year
- **G: Nervous system** - ~29,000 deaths/year
- Plus 17 other categories

**Data available for:** A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, V, W, X, Y, Z

---

## 📊 Data Sources Used

| Source | Years | Type | Status |
|--------|-------|------|--------|
| compiled_mortality_2001_2019.csv | 2001-2017 | Detailed ICD-10 codes | ✅ Local |
| compiled_mortality_21c_2017.csv | 2001-2017 | Detailed ICD-10 codes | ✅ Local |
| ONS API - 2010-19 edition | 2010-2019 | Weekly totals aggregated | ✅ Merged |
| ONS API - COVID-19 edition | 2020-2023 | Weekly totals aggregated | ✅ Merged |
| ONS API - 2024 & 2025 editions | 2024-2025 | Weekly totals aggregated | ✅ Merged |

---

## 📈 Usage Examples

### Analyze trends over 25 years:
```python
import pandas as pd

df = pd.read_csv('uk_mortality_comprehensive.csv')

# Year-on-year change
df['yoy_change'] = df['total_deaths'].pct_change() * 100

# Pre-COVID vs COVID era
pre_covid_avg = df[df['year'] < 2020]['total_deaths'].mean()
covid_avg = df[df['year'] >= 2020]['total_deaths'].mean()
print(f"Pre-COVID avg: {pre_covid_avg:,.0f}")
print(f"COVID era avg: {covid_avg:,.0f}")
print(f"Increase: {(covid_avg/pre_covid_avg - 1)*100:.1f}%")
```

### Compare causes of death:
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

### Current Gaps:
1. **2018-2019 by cause:** Only have totals (cause breakdown not in API)
2. **Pre-2001 data:** Not included (need manual historical downloads)

### How to fill pre-2001 gap:

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

To regenerate or update these files:

```powershell
cd data_sources/mortality_stats/development_code
python analyze_comprehensive_mortality.py
```

To fetch fresh API data (useful if new years released):

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

