# Age-Group Mortality Rates Update

**Date:** December 23, 2025  
**Status:** ✅ Complete

## Overview

Enhanced mortality statistics to provide **age-group-specific rates** using harmonized population denominators from the population module. This prevents misinterpretation of overall rates that conflate different age cohorts.

## Problem Solved

Previous mortality rates sometimes used aggregate population estimates or were unclear about denominators:
- **Rate ambiguity**: When comparing 85+ mortality (very high) to 0-4 mortality (lower), unclear if using same denominator
- **Age-blind totals**: Yearly rates mixed all age groups, obscuring age-specific patterns
- **Cause comparison issues**: Difficult to fairly compare diseases that disproportionately affect different age groups

## Solution

Three complementary datasets, each with **explicitly labelled rate columns**:

### 1️⃣ By Cause & Age Group  
**File:** `uk_mortality_rates_per_100k_by_cause.csv`

```
Columns:
- year, cause, sex, age_group
- deaths (count)
- population_age_group (denominator)
- mortality_rate_per_100k_age_group_population ← explicit!
```

**Use:** Compare causes within the same age group  
**Example:** "Are infectious diseases deadlier than circulatory disease in 0-4 year-olds?"

---

### 2️⃣ By Age Group (All Causes)  
**File:** `uk_mortality_rates_per_100k_by_age_group.csv` *(NEW)*

```
Columns:
- year, sex, age_group
- deaths (total across all causes)
- population_age_group (denominator)
- mortality_rate_per_100k_age_group_population ← explicit!
- denominator_label = "age group population"
```

**Use:** Compare mortality across age cohorts  
**Example:** "85+ males have a mortality rate of 18,824 per 100k vs. 0-4 males at 4,948 per 100k"

**Key insight:** Shows ~3.8× difference in age group rates, validating age as strong mortality determinant

---

### 3️⃣ Yearly Totals (Population-Wide)  
**File:** `uk_mortality_rates_per_100k_yearly_totals.csv`

```
Columns:
- year
- deaths (all causes, all ages)
- population_total (denominator)
- mortality_rate_per_100k_total_population ← explicit!
- denominator_label = "total population"
```

**Use:** Long-term population-wide trends  
**Example:** "UK mortality improved from 1,691 per 100k (1901) to 1,032 per 100k (2000)"

---

## Data Quality

| Metric | Value |
|--------|-------|
| Time Period | 1901–2000 (100 years) |
| Age Groups | 10 (0-4, 5-14, 15-24, 25-34, 35-44, 45-54, 55-64, 65-74, 75-84, 85+) |
| Sexes | 2 (Male, Female) |
| Causes | 193 distinct causes |
| By-Cause Records | 29,452 |
| By-Age Records | 2,000 |
| Yearly Records | 100 |

## Implementation Details

**Source Files Used:**
- Mortality: `uk_mortality_comprehensive_1901_2025_harmonized.csv` (37,897 records)
- Population: `uk_population_harmonized_age_groups.csv` (2,320 records, 1901–2016)
- **Time overlap:** 1901–2000 (100 years complete)

**Calculation:**
```
mortality_rate_per_100k = (deaths / population_age_group) × 100,000
```

**Age group assignment:**  
Mortality age ranges (e.g., "01-04", "T25-34") harmonized to demographic bins (0-4, 25-34, etc.)

## Key Statistics (2000 snapshot)

### By Age Group (Per 100k of that age group)
| Age Group | Male | Female |
|-----------|------|--------|
| 0-4 | 4,948.0 | 4,229.6 |
| 5-14 | 124.9 | 113.3 |
| 15-24 | 180.9 | 89.9 |
| ... | ... | ... |
| 85+ | 18,824.2 | 15,569.5 |

**Observation:** Elderly mortality ~3–4× higher than working-age adults

### Yearly Trend
```
1901: 1,691.4 per 100k (total population)
1950: 1,107.7 per 100k (total population)
2000: 1,031.6 per 100k (total population)
```

**Observation:** ~39% decline in population-wide mortality over 100 years

## Files Created/Modified

### New Files
- `uk_mortality_rates_per_100k_by_age_group.csv` (2,000 records)
- `AGE_GROUP_MORTALITY_RATES_UPDATE.md` (this document)

### Modified Files
- `uk_mortality_rates_per_100k_by_cause.csv` (refreshed with explicit column names)
- `uk_mortality_rates_per_100k_yearly_totals.csv` (refreshed with explicit column names)
- `README.md` (added denominator clarification + usage guide)
- `development_code/calculate_mortality_rates.py` (enhanced with age-group helpers)

## Usage Recommendations

### For Dashboard Builders
Use `uk_mortality_rates_per_100k_by_age_group.csv` for:
- Age-group comparison charts (line/bar plots)
- Heatmaps (age × year)
- Stacked bar charts showing contribution of each age group

Use explicit y-axis labels:
- ✅ "Deaths per 100,000 [age-group population]"
- ❌ "Mortality rate" (too vague)

### For Statistical Analysis
Always include denominator in aggregations:
```python
df['rate'] = (df['deaths'] / df['population_age_group']) * 100000
df.columns = ['..._age_group_population']  # Explicit!
```

### For Comparative Studies
Document denominator in every figure:
```
"Figure 2: Male mortality rates (per 100,000 of each age group)
shows peaks at ages 85+ (18.8k) and 75-84 (7.6k) in 2000."
```

## Future Enhancements

- [ ] Extend population data to 2025 (currently ends 2016)
- [ ] Add cause-of-death breakdown by age group (ICD harmonization)
- [ ] Confidence intervals for small denominators (age × rare cause × year)
- [ ] Age-standardized rates (for fair trend comparison across decades)

## Questions?

Refer to:
- README.md: Overview and structure
- uk_population_harmonized_age_groups.csv: Population denominators
- develop_code/calculate_mortality_rates.py: Source code + logic
