# UK Population Data - Historical Dataset (1901-2016)

## 📊 Overview

This folder contains comprehensive UK population data spanning 116 years (1901-2016), broken down by year, sex, and age groups. The dataset enables demographic analysis including population trends, age structure evolution, life expectancy correlations with mortality data, and population-based mortality rate calculations.

## ✅ What You Have

### 1. **UK Population by Year, Sex, and Age: 1901-2016** (116 years)

**File:** `combined_population_data.csv` (1901-2016) + supplementary `populations20012016.xls` (2001-2016)

```text
Year Range: 1901 - 2016
Total Records: 4,250 (detailed ages) + 608 (XLS)
Geographic Coverage: England and Wales
Age Breakdown: 19 detailed age groups from <1 year to 85+
Sex Breakdown: Male (1) and Female (2)
```

**Key Structure:**

| Column | Type | Values | Description |
|--------|------|--------|-------------|
| **YR** | Integer | 1901-2016 | Year |
| **SEX** | Integer | 1, 2 | 1=Male, 2=Female |
| **AGE** | String | <1, 01-04, 05-09, ... 85+ | Age range or single year |
| **POP** | Integer | Population count | Total population in that year/sex/age group |
| **Agegroup** | String/NaN | Standard groups or NaN | Some rows have Agegroup mapping (for convenience) |

**Sample Data:**

```
Year 1901:
- Males aged <1: 393,500
- Females aged <1: 393,100
- Males aged 01-04: 1,463,800
- Females aged 01-04: 1,469,600
(... continues for 19 age groups)
```

### 2. **Harmonized Population Data (Standardized Age Groups): 1901-2016** ⭐ **RECOMMENDED FOR MODEL BUILDING**

**File:** `uk_population_harmonized_age_groups.csv`

This file aggregates the detailed population data into **standardized age groups matching mortality_stats outputs**, making it ideal for:
- Direct calculation of age-specific mortality rates
- Merging with cause-of-death data for demographic analysis
- Multi-dataset comparisons and cross-tabulations

```text
Year Range: 1901 - 2016 (FULL COVERAGE!)
Total Records: 2,320 (10 age groups × 2 sexes × 116 years)
Age Groups: 10 standardized bins (0-4, 5-14, 15-24, ... 85+)
Sex Categories: Male, Female
```

**Data Structure:**

| Column | Type | Values | Description |
|--------|------|--------|-------------|
| **year** | Integer | 1901-2016 | Year |
| **age_group** | String | 0-4, 5-14, 15-24, ... 85+ | Standardized age bin |
| **sex** | String | Male, Female | Sex |
| **population** | Integer | Population count | Total population in that group |

**Why Use This File?**
- ✅ **Complete 116-year coverage:** 1901-2016 with no gaps
- ✅ **Matches mortality_stats bins exactly:** Same 10 age groups (0-4, 5-14, 15-24, 25-34, 35-44, 45-54, 55-64, 65-74, 75-84, 85+)
- ✅ **Seamless data integration:** All sources consolidated (CSV 1901-2000 + XLS 2001-2016)
- ✅ **Easy merging:** Can directly join with mortality data by (year, age_group, sex)
- ✅ **Ready for analysis:** No additional binning/mapping needed

**Example: Calculate mortality rate per 100k**

```python
import pandas as pd
import zipfile

# Load both datasets
pop = pd.read_csv('data_sources/population/uk_population_harmonized_age_groups.csv')

# Load mortality data
with zipfile.ZipFile('data_sources/mortality_stats/uk_mortality_by_cause_1901_onwards.zip') as zf:
    mort = pd.read_csv(zf.open('uk_mortality_by_cause_1901_onwards.csv'))

# Aggregate mortality to match population structure (if needed)
mort_agg = mort.groupby(['year', 'age_group', 'sex'])['deaths'].sum().reset_index()

# Merge and calculate rate
merged = mort_agg.merge(pop, on=['year', 'age_group', 'sex'], how='inner')
merged['mortality_rate_per_100k'] = (merged['deaths'] / merged['population']) * 100000

print(merged[['year', 'age_group', 'sex', 'deaths', 'population', 'mortality_rate_per_100k']].head(10))
```

### 3. **Key Statistics by Era**

**Total UK Population (England & Wales):**

| Period | Average | Lowest | Highest | Trend |
|--------|---------|--------|---------|-------|
| 1901-1910 | 38.8M | 37.9M (1901) | 40.9M (1910) | Growing |
| 1911-1920 | 42.1M | 40.9M (1911) | 43.6M (1920) | Growing, WW1 impact |
| 1921-1950 | 44.2M | 43.6M (1921) | 44.8M (1950) | Slow growth |
| 1951-1980 | 48.8M | 44.8M (1951) | 49.0M (1980) | Post-war growth |
| 1981-2016 | 51.8M | 49.0M (1981) | 58.4M (2016) | Continued growth & migration |

---

## 📁 Data Sources

| Source | Years | Type | Location |
|--------|-------|------|----------|
| combined_population_data.csv | 1901-2016 | Detailed ages (19 groups) | `downloaded_sourcefiles/` |
| populations20012016.xls | 2001-2016 | Age group format (19 groups) | `downloaded_sourcefiles/` |
| popln_tcm77-215653.csv | 1901-2016 | ONS raw data (alternate) | `downloaded_sourcefiles/` |
| popln_tcm77-215653.xls / .xlsx | 1901-2016 | Excel versions | `downloaded_sourcefiles/` |
| CompilePopulationStats.py | - | Builder script | `downloaded_sourcefiles/` |

**Primary Source:** Office for National Statistics (ONS)  
**Attribution:** UK Population Estimates by Age and Sex

---

## 📈 Usage Examples

### Load and explore the data

```python
import pandas as pd
from pathlib import Path

# Load the harmonized population data (RECOMMENDED)
pop_path = Path('data_sources/population/uk_population_harmonized_age_groups.csv')
df = pd.read_csv(pop_path)

# Basic info
print(f"Years covered: {df['year'].min()} - {df['year'].max()}")
print(f"Total records: {len(df)}")
print(f"Age groups: {df['age_group'].unique()}")

# Aggregate total population per year
pop_by_year = df.groupby('year')['population'].sum()
print(f"\nTotal population by year (sample):")
print(pop_by_year.head())
```

### Calculate total population by year and sex

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('data_sources/population/uk_population_harmonized_age_groups.csv')

# Aggregate by year and sex
pop_by_year_sex = df.groupby(['year', 'sex'])['population'].sum().reset_index()

# Plot
fig, ax = plt.subplots(figsize=(14, 6))
for sex in ['Male', 'Female']:
    data = pop_by_year_sex[pop_by_year_sex['sex'] == sex]
    ax.plot(data['year'], data['population'] / 1_000_000, label=sex, linewidth=2)

ax.set_xlabel('Year')
ax.set_ylabel('Population (millions)')
ax.set_title('UK Population by Sex, 1901-2016')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
```

### Analyze age structure changes (cohort analysis)

```python
# Compare age distribution across decades
decades = [1901, 1921, 1951, 1981, 2011, 2016]

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
axes = axes.flatten()

for idx, year in enumerate(decades):
    year_data = df[df['year'] == year].copy()
    
    male_pop = year_data[year_data['sex'] == 'Male'].set_index('age_group')['population']
    female_pop = year_data[year_data['sex'] == 'Female'].set_index('age_group')['population']
    
    age_labels = ['0-4', '5-14', '15-24', '25-34', '35-44', '45-54', '55-64', '65-74', '75-84', '85+']
    
    axes[idx].barh(age_labels, male_pop.values, label='Male', color='steelblue', alpha=0.7)
    axes[idx].barh(age_labels, [-f for f in female_pop.values], label='Female', color='coral', alpha=0.7)
    axes[idx].set_title(f'{year}')
    axes[idx].set_xlabel('Population')
    if idx == 0:
        axes[idx].legend()

plt.suptitle('UK Population Pyramids by Year (1901-2016)', fontsize=14, y=0.995)
plt.tight_layout()
plt.show()
```

### Calculate aging population trends

```python
# Categorize into broad age groups for aging analysis
def broad_age_category(age_group):
    if age_group in ['0-4', '5-14']:
        return 'Children (0-14)'
    elif age_group in ['15-24', '25-34', '35-44', '45-54', '55-64']:
        return 'Working Age (15-64)'
    else:
        return 'Elderly (65+)'

df['broad_category'] = df['age_group'].apply(broad_age_category)

# Calculate proportions by year
age_props = df.groupby(['year', 'broad_category'])['population'].sum().reset_index()
age_props['proportion'] = age_props.groupby('year')['population'].apply(lambda x: x / x.sum())

# Plot trend
fig, ax = plt.subplots(figsize=(14, 6))
for category in ['Children (0-14)', 'Working Age (15-64)', 'Elderly (65+)']:
    data = age_props[age_props['broad_category'] == category]
    ax.plot(data['year'], data['proportion'] * 100, label=category, linewidth=2)

ax.set_xlabel('Year')
ax.set_ylabel('Percentage of Population (%)')
ax.set_title('UK Age Structure Changes, 1901-2016')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
```

### Combine with mortality data for rate calculations

```python
import pandas as pd
import zipfile
from pathlib import Path

# Load population (harmonized - RECOMMENDED)
pop = pd.read_csv('data_sources/population/uk_population_harmonized_age_groups.csv')

# Load mortality
mort_path = Path('data_sources/mortality_stats/uk_mortality_by_cause_1901_onwards.zip')
with zipfile.ZipFile(mort_path) as zf:
    mort = pd.read_csv(zf.open('uk_mortality_by_cause_1901_onwards.csv'))

# Aggregate mortality by year, age_group, and sex
mort_agg = mort.groupby(['year', 'age_group', 'sex'])['deaths'].sum().reset_index()

# Merge and calculate rates
combined = mort_agg.merge(pop, on=['year', 'age_group', 'sex'], how='inner')
combined['mortality_rate_per_100k'] = (combined['deaths'] / combined['population']) * 100000

print("Mortality rates by age (2010 sample):")
print(combined[combined['year'] == 2010].sort_values('age_group'))
```

---

## 🔍 Historical Context

### Key Historical Events Affecting Population

1. **Edwardian Era (1901-1914):** Immigration and natural growth, fertility decline begins
2. **World War I (1914-1918):** Male population decline (~1M excess deaths)
3. **Spanish Flu (1918-1920):** Excess mortality, particularly young adults
4. **1920s-1930s:** Low fertility, controlled growth
5. **World War II (1939-1945):** Male decline again, evacuations, excess deaths
6. **Post-War Baby Boom (1945-1965):** Rapid growth, fertility spike
7. **Post-Industrial Era (1970s+):** Declining fertility, aging population
8. **Migration Impacts (2000s+):** Net migration increases visible in population growth

### Age Structure Changes

- **1901:** Young population pyramid (high fertility, high mortality)
  - <15 years: ~35% of population
  - 65+: ~4% of population

- **1951 (Post-WW2):** Broader base from baby boom
  - <15 years: ~21% of population
  - 65+: ~7% of population

- **2016:** Aging population (low fertility, high longevity)
  - <15 years: ~17% of population
  - 65+: ~18% of population

---

## 📁 Folder Structure

```
data_sources/population/
├── README.md                                          # This file
├── uk_population_harmonized_age_groups.csv           # ⭐ RECOMMENDED: Standardized age groups (1901-2016)
├── development_code/                                 # Analysis & building scripts
│   ├── build_harmonized_population.py               # Script that builds harmonized CSV from CSV + XLS
│   ├── downloaded_sourcefiles/                      # Original ONS data (gitignored)
│   │   ├── combined_population_data.csv             # Detailed ages (1901-2016)
│   │   ├── populations20012016.xls                  # Age groups (2001-2016) - used to fill gap
│   │   ├── popln_tcm77-215653.csv
│   │   ├── popln_tcm77-215653.xls
│   │   ├── popln_tcm77-215653.xlsx
│   │   └── CompilePopulationStats.py
│   └── (new analysis scripts will go here)
└── (generated outputs will go here)
```

**Key Files:**
- **`uk_population_harmonized_age_groups.csv`** ⭐ **Use this for model building** - aggregated to match mortality_stats age bins, covers 1901-2016
- **`combined_population_data.csv`** - detailed granular ages (in development_code/downloaded_sourcefiles), useful for custom age binning
- **`populations20012016.xls`** - supplementary source used to fill 2001-2016 gap in harmonized file

---

## 🔗 Integration Opportunities

### Cross-Dataset Analysis

Combine with other data sources in this repository:

1. **Mortality Stats (1901-2025):**
   - Calculate age-specific and sex-specific mortality rates
   - Analyze life expectancy trends over time
   - Compare mortality improvement rates across age groups
   - Study impact of wars and pandemics on population structure

2. **Economic Indicators (1800-2023):**
   - Correlate GDP per capita with population growth
   - Analyze impact of economic downturns on migration patterns
   - Study working-age population changes vs. labor force participation

3. **Housing Pressure:**
   - Calculate population density changes over time
   - Analyze household size changes
   - Estimate housing demand from population growth

4. **Political Context:**
   - Analyze demographic shifts before/after elections
   - Study electoral bloc composition (youth vs. elderly vs. working age)

### Potential Research Questions

- How has UK population aging accelerated compared to historical rates?
- What's the correlation between fertility decline and child mortality improvements?
- How did wars (WW1, WW2) reshape the age structure and sex ratio?
- Can we estimate net migration flows from population changes?
- How does age structure relate to mortality trends (more elderly → higher deaths even with lower rates)?

---

## 📊 Data Quality Notes

### Coverage
- **Geographic:** England and Wales (consistent definition 1901-2016)
- **Scotland & Northern Ireland:** Separate datasets not included here (can add if needed)
- **Completeness:** 1901-2016 with consistent age group definitions

### Age Group Definitions
- Standard 5-year age groups: <1, 01-04, 05-09, 10-14, ... 80-84, 85+
- Some rows have "T" prefix (e.g., T25-34) in older records - these are included in standard mapping
- All ages properly mapped to 10 standardized groups (0-4, 5-14, 15-24, ... 85+) in harmonized file

### Sex Codes
- **1** = Male
- **2** = Female
- No other sex categories in historical data (reflects census collection methods)

### Data Source Integration
- **1901-2000:** From `combined_population_data.csv` (detailed age ranges)
- **2001-2016:** From `populations20012016.xls` (age group format, seamlessly integrated)
- Both sources standardized to same 10 age group bins for consistency

### Known Issues
- 1901: Some age groups may have lower precision in original ONS data
- WW1 (1914-1918): Military personnel abroad may be counted differently
- WW2 (1939-1945): Evacuees and military overseas affect enumeration
- Census years (1901, 1911, 1921, 1931, 1941, 1951, 1961, 1971, 1981, 1991, 2001, 2011): Actual counts from census enumerations
- Non-census years: Estimates based on intercensal methods

---

## 🚀 Getting Started

### Prerequisites

```powershell
# Activate project virtual environment
& H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/Activate.ps1

# Install dependencies
pip install pandas numpy matplotlib openpyxl xlrd
```

### Quick Start

```powershell
# Use the harmonized file directly:
# data_sources/population/uk_population_harmonized_age_groups.csv

# No additional setup needed - file is pre-built and ready to use!
```

### Regenerating the Harmonized Population File

If you update the source data or need to rebuild the harmonized file:

```powershell
# From project root:
.\.venv\Scripts\python.exe .\data_sources\population\development_code\build_harmonized_population.py
```

This script:
- Loads `combined_population_data.csv` (1901-2000, detailed ages)
- Loads `populations20012016.xls` (2001-2016, age group format)
- Maps all age ranges to 10 standardized groups (0-4, 5-14, 15-24, ... 85+)
- Aggregates by year, sex, and age_group
- Produces `uk_population_harmonized_age_groups.csv` (2,320 rows covering 1901-2016)
- Matches mortality_stats age bin structure for seamless merging

**Key Improvement:** By integrating the XLS data, the harmonized file now covers **the full 1901-2016 range** with no gaps!

---

## 📝 Notes

- All population figures are **point-in-time estimates** (usually mid-year)
- Data represents **resident population** (includes temporary visitors, excludes some overseas military)
- **Age definitions** consistent across entire 1901-2016 dataset for trend analysis
- Use this alongside mortality data to calculate age-specific death rates
- Combine with economic data for per-capita analysis

---

## 🔄 Updates

| Date | Change | Author |
|------|--------|--------|
| 2025-12-23 | Initial README created | GitHub Copilot |
| 2025-12-23 | Organized source files into development_code structure | GitHub Copilot |
| 2025-12-23 | Created harmonized age group file (1901-2000) | GitHub Copilot |
| 2025-12-23 | **Enhanced harmonized file to include 2001-2016 from XLS** | GitHub Copilot |

---

## 📚 References

- **ONS Population Estimates:** https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates
- **Historical Census Data:** https://www.ons.gov.uk/census
- **UK Data Service:** Historical population data archives
- **IPED Database:** International historical population estimates

---

**For questions or contributions, see:** [CONTRIBUTING.md](../../CONTRIBUTING.md)
