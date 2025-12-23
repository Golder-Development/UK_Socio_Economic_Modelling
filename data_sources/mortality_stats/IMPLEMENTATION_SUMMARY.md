# Mortality Statistics Enhancement: Summary

## ✅ What Was Done

Enhanced UK mortality statistics to provide **age-group-specific mortality rates per 100,000** using harmonized population denominators from the population module. This eliminates ambiguity about which population was used to calculate rates.

---

## 📊 Three New/Updated Output Files

All files now include **explicit column names** to prevent denominator confusion:

### 1. `uk_mortality_rates_per_100k_by_cause.csv`
- **29,452 records** (1901–2000 × 193 causes × 2 sexes × 10 age groups)
- **Denominator:** Each age group's population
- **Key column:** `mortality_rate_per_100k_age_group_population`
- **Use case:** Compare causes within the same age group
- **Example:** "Was TB deadlier than measles in 0-4 year-olds in 1901?"

### 2. `uk_mortality_rates_per_100k_by_age_group.csv` *(NEW)*
- **2,000 records** (1901–2000 × 10 age groups × 2 sexes)
- **Denominator:** Each age group's population  
- **Key column:** `mortality_rate_per_100k_age_group_population`
- **Use case:** Compare mortality across age cohorts
- **Example:** "Elderly (85+) have 135× higher mortality than children (0-4) per their respective populations"

### 3. `uk_mortality_rates_per_100k_yearly_totals.csv`
- **100 records** (1901–2000)
- **Denominator:** Total population (all ages combined)
- **Key column:** `mortality_rate_per_100k_total_population`
- **Use case:** Long-term population-wide trends
- **Example:** "Overall UK mortality improved 39% from 1,691 per 100k (1901) to 1,032 per 100k (2000)"

---

## 🔧 Implementation

**Script Updated:**
- `development_code/calculate_mortality_rates.py`
  - Uses harmonized mortality file: `uk_mortality_comprehensive_1901_2025_harmonized.csv`
  - Uses harmonized population file: `uk_population_harmonized_age_groups.csv`
  - Produces three explicitly-labelled outputs
  - Includes helper function for age group standardization

**Documentation Updated:**
- `README.md` — Added section on "Mortality Rates per 100,000" with key usage guide
- `README.md` — Added "⚠️ Critical" warning about denominator clarity
- `AGE_GROUP_MORTALITY_RATES_UPDATE.md` — Full technical details & examples

**New Verification Script:**
- `verify_age_group_rates.py` — Demonstrates correct usage + warns about common mistakes

---

## 📈 Key Findings (Year 2000)

### Age-Group Variation
Male mortality in 2000 ranges from **14.2 per 100k** (5-14 age group) to **18,824 per 100k** (85+ age group).  
→ **135× difference** between youngest and oldest groups

### Causes Within Age Groups
All 85+ male deaths in 2000 aggregated to **18,824 per 100k** of that age group's population.  
→ Can fairly compare individual causes because same denominator

### Population-Wide Trend
- 1901: 1,691.4 per 100k (total population)
- 2000: 1,031.6 per 100k (total population)
- **39% improvement** over 100 years

---

## ⚠️ Critical Denominator Rule

**Always check which rate column you're using:**

| Scenario | File | Column | Denominator |
|----------|------|--------|-------------|
| Comparing causes within 85+ age group | by_cause | `_age_group_population` | 85+ population only |
| Comparing age groups to each other | by_age_group | `_age_group_population` | Each age group's population |
| Describing overall population trend | yearly_totals | `_total_population` | Total population (all ages) |

**Red flag:** If you see rates without explicit denominator labels → manually add them!

---

## 🚀 Next Steps

### For Dashboard Development
1. Use `by_age_group.csv` for age-comparison visualizations
2. Label all y-axes: **"Deaths per 100,000 (of age-group population)"**
3. Reference `AGE_GROUP_MORTALITY_RATES_UPDATE.md` in comments

### For Analysis/Modeling
1. Load correct file based on denominator needed
2. Rename columns if combining datasets (to avoid confusion)
3. Always document which denominator was used in your analysis

### For Presentation
1. Include denominator in figure captions
2. Use "per 100k" shorthand only if denominator is obvious from context
3. When comparing across studies, verify they use compatible denominators

---

## 📁 File Locations

All files located in: `data_sources/mortality_stats/`

```
├── uk_mortality_rates_per_100k_by_cause.csv (29,452 records) ← age-group denominators
├── uk_mortality_rates_per_100k_by_age_group.csv (2,000 records) ← age-group denominators NEW
├── uk_mortality_rates_per_100k_yearly_totals.csv (100 records) ← total population denominators
├── AGE_GROUP_MORTALITY_RATES_UPDATE.md (detailed changelog)
├── verify_age_group_rates.py (verification script)
└── development_code/
    └── calculate_mortality_rates.py (source script)
```

---

## 🎯 Quality Assurance

✅ All output files verified with `verify_age_group_rates.py`  
✅ Column names explicit: `_age_group_population` vs `_total_population`  
✅ README updated with denominator guide + usage examples  
✅ Backward compatibility: `mortality_rate_per_100k` alias included  
✅ Age group standardization validated against population file (0-4, 5-14, ..., 85+)

---

## 📞 Questions?

- **Data structure:** See `README.md` → "📊 Mortality Rates per 100,000"
- **Technical details:** See `AGE_GROUP_MORTALITY_RATES_UPDATE.md`
- **Common mistakes:** Run `verify_age_group_rates.py` (shows examples)
- **Population denominators:** See `data_sources/population/README.md`

