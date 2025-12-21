# Quick Start: Using Harmonized Mortality Data

## The Complete Data File

**File**: `uk_mortality_by_cause_1901_2025_harmonized.csv`

**Columns**:
- `year` - Year of death (1901-2000)
- `cause` - Original ICD code
- `cause_description` - Human-readable disease name (year-aware)
- `harmonized_category` - Standardized category code (e.g., "infectious_diseases")
- `harmonized_category_name` - Full category name (e.g., "Infectious and Parasitic Diseases")
- `classification_confidence` - How confident the classification is (high/medium/low)
- `sex` - Male/Female
- `age` - Age group
- `deaths` - Number of deaths

## 3-Minute Start

```python
import pandas as pd

# Load the data
df = pd.read_csv('uk_mortality_by_cause_1901_2025_harmonized.csv')

# Example 1: Total deaths by category
category_totals = df.groupby('harmonized_category_name')['deaths'].sum()
print(category_totals.sort_values(ascending=False))

# Example 2: Trend over time for infectious diseases
infectious = df[df['harmonized_category'] == 'infectious_diseases']
yearly = infectious.groupby('year')['deaths'].sum()
yearly.plot(title='Infectious Disease Deaths 1901-2000')

# Example 3: Compare categories in specific year
year_2000 = df[df['year'] == 2000]
year_2000.groupby('harmonized_category_name')['deaths'].sum().plot(kind='bar')
```

## Key Features

### ✅ Use harmonized categories when you want to:
- Track disease trends across the full 1901-2000 period
- Compare broad disease categories
- Create visualizations without ICD complexity
- Perform statistical analyses across time periods

### ⚠️ Use original cause codes when you need:
- Specific disease detail
- Medical accuracy for clinical research
- Granular condition tracking

## Quick Reference: 19 Categories

| Short Code | Category Name |
|------------|---------------|
| infectious_diseases | Infectious and Parasitic Diseases |
| neoplasms | Neoplasms (Cancers and Tumors) |
| blood_immune | Blood and Immune System Disorders |
| endocrine_metabolic | Endocrine, Nutritional and Metabolic Diseases |
| mental_behavioral | Mental and Behavioral Disorders |
| nervous_system | Diseases of the Nervous System |
| eye_ear | Diseases of Eye and Ear |
| circulatory | Diseases of the Circulatory System |
| respiratory | Diseases of the Respiratory System |
| digestive | Diseases of the Digestive System |
| skin | Diseases of the Skin |
| musculoskeletal | Diseases of Musculoskeletal System |
| genitourinary | Diseases of the Genitourinary System |
| pregnancy_childbirth | Pregnancy, Childbirth and Puerperium |
| perinatal | Conditions Originating in Perinatal Period |
| congenital | Congenital Malformations |
| injury_poisoning | Injury, Poisoning and External Causes |
| ill_defined | Symptoms, Signs and Ill-Defined Conditions |
| other | Other and Unclassified |

## Common Analyses

### Track Disease Burden Shifts
```python
# See how top causes changed over time
for year in [1901, 1925, 1950, 1975, 2000]:
    top = df[df['year']==year].groupby('harmonized_category_name')['deaths'].sum().nlargest(3)
    print(f"\n{year}:")
    print(top)
```

### Age Pattern Analysis
```python
# Which categories affect which age groups?
age_patterns = df.groupby(['harmonized_category_name', 'age'])['deaths'].sum()
age_patterns.unstack().plot(kind='bar', stacked=True)
```

### Sex Differences
```python
# Compare male vs female deaths by category
by_sex = df.groupby(['harmonized_category_name', 'sex'])['deaths'].sum().unstack()
by_sex.plot(kind='barh', title='Deaths by Category and Sex')
```

## Data Quality Notes

- **91.1% matched** to harmonized categories
- **82.2% confidence** (high or medium)
- Unmatched rows are mostly "Unknown" cause codes
- Year-aware: Code meanings don't cross periods

## Need More Detail?

- **Full documentation**: See `HARMONIZED_CATEGORIES_README.md`
- **Technical details**: See `ICD_DESCRIPTIONS_README.md`  
- **Examples**: Run `demonstrate_harmonized_system.py` (in `development_code`)

## Rebuild the System

If you need to adjust categories:

```bash
cd data_sources/mortality_stats/development_code
# 1. Edit keyword lists in build_harmonized_categories.py
# 2. Rebuild mappings
python build_harmonized_categories.py

# 3. Apply to mortality data
python add_harmonized_categories_to_mortality.py

# 4. Verify results
python demonstrate_harmonized_system.py
```

---

**Ready to analyze!** The harmonized data makes 100 years of mortality data analysis straightforward and consistent.
