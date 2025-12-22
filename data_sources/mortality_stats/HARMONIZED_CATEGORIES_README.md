# Harmonized Disease Classification System

## Overview

This system creates **standardized disease categories** that work consistently across all ICD versions (1901-2000), enabling longitudinal analysis without worrying about changing classification systems.

## The Problem We're Solving

### Why Harmonization is Needed

ICD codes changed dramatically over time:

- **ICD-1 (1901-1910)**: 192 codes

- **ICD-9c (1994-2000)**: 5,292 codes  

The same code number meant different things:

- Code `10.0` in 1901 = "Small pox - vaccinated"
- Code `10.0` in 1935 = "Diphtheria"

Specific conditions were classified differently:

- Tuberculosis had 1 code in ICD-1, but 10+ codes in ICD-9
- New diseases appeared in later periods (HIV, new cancers, etc.)

### The Solution: Harmonized Categories

We create **24 broad disease categories** that:

- ✅ Work consistently across all time periods
- ✅ Map to similar concepts in medical classification
- ✅ Enable meaningful longitudinal trend analysis
- ⚠️ Accept some loss of granularity for comparability

## Harmonized Categories

### The 24 Standard Categories

1. **Infectious and Parasitic Diseases** - All infections, fevers, parasitic diseases
2. **Neoplasms (Cancers and Tumors)** - All malignant and benign growths
3. **Blood and Immune System Disorders** - Anemia, hemophilia, immune conditions
4. **Endocrine, Nutritional and Metabolic Diseases** - Diabetes, malnutrition, thyroid
5. **Mental and Behavioral Disorders** - Mental illness, alcoholism, drug dependence
6. **Diseases of the Nervous System** - Brain, epilepsy, paralysis, stroke effects
7. **Diseases of Eye and Ear** - Vision, hearing, related conditions
8. **Diseases of the Circulatory System** - Heart, blood vessels, stroke
9. **Diseases of the Respiratory System** - Lungs, bronchitis, pneumonia
10. **Diseases of the Digestive System** - Stomach, intestines, liver
11. **Diseases of the Skin** - Dermatological conditions
12. **Diseases of Musculoskeletal System and Connective Tissue** - Bones, joints, arthritis
13. **Diseases of the Genitourinary System** - Kidneys, reproductive organs
14. **Pregnancy, Childbirth and Puerperium** - Maternal health conditions
15. **Conditions Originating in Perinatal Period** - Newborn conditions
16. **Congenital Malformations and Chromosomal Abnormalities** - Birth defects
17. **Injury, Poisoning and External Causes** - Accidents, poisoning (general)
18. **Suicide and Self-Inflicted Injury** - Suicide deaths
19. **Accidental Death** - Accidents (specific category)
20. **Homicide and Assault** - Violence, homicide
21. **Drug-Related Deaths** - Overdose, drug dependence deaths
22. **War and War-Related Deaths** - Wartime deaths and related impacts
23. **Symptoms, Signs and Ill-Defined Conditions** - Unknown or unclear causes
24. **Other and Unclassified** - Catch-all for unmatched codes
25. **Legal Drug-Related Deaths** - Tobacco and Alcohol related deaths

## Files Generated

### Core Classification Files

1. **`icd_harmonized_categories.csv`** - Complete mapping
   - Columns: `code`, `icd_version`, `original_description`, `harmonized_category`, `harmonized_category_name`, `classification_confidence`
   - 24,561 rows (one per ICD code)
   - Shows which harmonized category each specific ICD code maps to

2. **`harmonized_categories_summary.csv`** - Category reference
   - Columns: `category_id`, `category_name`, `code_count`, `example_keywords`
   - 24 rows (one per harmonized category)
   - Quick reference guide

### Mortality Data with Harmonized Categories

3. **`uk_mortality_by_cause_1901_2025_harmonized.csv`** - Main analysis file

   - Original columns: `year`, `cause`, `cause_description`, `sex`, `age`, `deaths`
   - **Added columns**:
     - `harmonized_category` - short code (e.g., "infectious_diseases")
     - `harmonized_category_name` - full name (e.g., "Infectious and Parasitic Diseases")
     - `classification_confidence` - high/medium/low confidence in classification

4. **`uk_mortality_comprehensive_1901_2025_harmonized.csv`** - Same structure

## How Classification Works

### Keyword-Based Matching

Each category has a list of keywords that identify relevant diseases:

```python
'infectious_diseases': ['fever', 'pox', 'tuberculosis', 'diphtheria', ...]
'neoplasms': ['cancer', 'carcinoma', 'tumor', 'malignant', ...]
'circulatory': ['heart', 'cardiac', 'stroke', 'artery', ...]
```

The system:

1. Looks at the disease description
2. Counts keyword matches for each category
3. Assigns to category with most matches
4. Reports confidence level

### Confidence Levels

- **High**: 2+ keyword matches (30.5% of codes)
- **Medium**: 1 keyword match (51.7% of codes)
- **Low**: No matches, used catch-all (17.8% of codes)

### Year-Aware Matching Preserved

The harmonized system maintains year-aware matching:

- Codes are matched based on ICD version and year
- No risk of cross-period contamination
- Each code gets correct harmonized category for its period

## Usage Examples

### Example 1: Longitudinal Trend Analysis

```python
import pandas as pd

df = pd.read_csv('uk_mortality_by_cause_1901_2025_harmonized.csv')

# Compare infectious diseases vs cancer over 100 years
trends = df.groupby(['year', 'harmonized_category_name'])['deaths'].sum()

infectious = trends.loc[:, 'Infectious and Parasitic Diseases']
cancer = trends.loc[:, 'Neoplasms (Cancers and Tumors)']

# Plot the trends
import matplotlib.pyplot as plt
plt.plot(infectious.index, infectious.values, label='Infectious Diseases')
plt.plot(cancer.index, cancer.values, label='Cancer')
plt.legend()
plt.title('Disease Category Trends 1901-2000')
plt.show()
```

### Example 2: Category Distribution by Year

```python
# See how disease burden shifted over time
for year in [1901, 1950, 2000]:
    year_data = df[df['year'] == year]
    distribution = year_data.groupby('harmonized_category_name')['deaths'].sum()
    distribution = distribution.sort_values(ascending=False)
    
    print(f"\n{year} Top 5 Causes:")
    for cat, deaths in distribution.head(5).items():
        print(f"  {cat}: {deaths:,.0f}")
```

### Example 3: Age Patterns Within Categories

```python
# Analyze age distribution for respiratory diseases
respiratory = df[df['harmonized_category_name'] == 'Diseases of the Respiratory System']
age_pattern = respiratory.groupby('age')['deaths'].sum().sort_values(ascending=False)
print(age_pattern)
```

## Classification Results

### Overall Statistics

- **Total codes classified**: 24,561
- **Match rate**: 91.1% (34,519 / 37,897 mortality rows)
- **Time period covered**: 1901-2000
- **Confidence**: 82.2% high or medium confidence

### Top Categories by Death Count (1901-2000)

1. **Infectious and Parasitic Diseases**: 1,008,994 deaths
2. **Diseases of the Respiratory System**: 911,215 deaths
3. **Other and Unclassified**: 560,339 deaths
4. **Symptoms, Signs and Ill-Defined**: 487,784 deaths
5. **Diseases of the Nervous System**: 399,796 deaths

### Cross-Period Consistency Examples

**Infectious Diseases Category includes:**

- ICD-1 (1901): "Small pox - vaccinated", "Diphtheria", "Measles"
- ICD-5 (1945): "Typhoid fever", "Plague", "Malaria"
- ICD-9 (1995): "Cholera - Due to Vibrio cholerae", "HIV disease"

**Cancer Category includes:**

- ICD-1 (1901): "Carcinoma", "Sarcoma", "Cancer, malignant disease"
- ICD-9 (1995): "Malignant neoplasm of stomach", "Leukemia", etc.

## What You Gain

### ✅ Benefits

1. **Longitudinal Analysis** - Track trends from 1901-2000 consistently
2. **Simple Comparisons** - Compare disease burdens across categories
3. **Demographic Analysis** - Analyze age/sex patterns within stable categories
4. **Visualization Ready** - Create charts without ICD version complexity
5. **Research Friendly** - Standard categories aid in hypothesis testing

### ⚠️ Trade-offs

1. **Lost Granularity** - Specific diseases grouped together
   - Example: All tuberculosis types → "Infectious Diseases"
   - Can't distinguish between TB subtypes across time

2. **Later Period Specificity** - Some conditions only exist in later ICDs
   - Example: HIV only appears in ICD-9 (1980s+)
   - Shows as zero in earlier periods (correct, but might be misleading)

3. **Keyword Limitations** - Some classifications might be imperfect
   - 17.8% of codes had low confidence (no keyword matches)
   - Manual review recommended for critical analyses

## Customizing Classifications

### Override Mechanism

For fine-grained control over specific code assignments, use `icd_harmonized_overrides.csv`:

**File**: `icd_harmonized_overrides.csv`
**Location**: `data_sources/mortality_stats/`
**Columns**: `code, icd_version, harmonized_category, harmonized_category_name, classification_confidence`

Overrides take **highest precedence** when harmonization is rebuilt. Use this when:

- A code is misclassified by the keyword system
- You need year-specific handling (same code, different category by ICD version)
- You're auditing/correcting the automatic mapping

**Example override row:**

```csv
100A,ICD-2 (1911-1920),digestive,Diseases of the Digestive System,override
```

### Review Crosswalk

Generate an audit table showing all old→new mappings:

```bash
cd data_sources/mortality_stats/development_code
python build_crosstab_icd_harmonization.py
```

Outputs: `icd_harmonization_crosswalk.csv`

- Shows `icd_version`, `cause`, `cause_description` → harmonized category mappings
- Useful for spotting systematic errors or patterns

## Script Reference

Note: Development scripts are located in `data_sources/mortality_stats/development_code`. Run the following commands from that folder, or prefix paths accordingly.

### 1. Build the Harmonized System

```bash
cd data_sources/mortality_stats/development_code
python build_harmonized_categories.py
```

**What it does:**

- Loads all ICD code descriptions
- Applies keyword-based classification
- Assigns harmonized categories
- Reports statistics and confidence levels

**Creates:**

- `icd_harmonized_categories.csv` (24,561 mappings)
- `harmonized_categories_summary.csv` (24 categories)

### 2. Apply to Mortality Data

```bash
cd data_sources/mortality_stats/development_code
python add_harmonized_categories_to_mortality.py
```

**What it does:**

- Loads harmonized mapping
- Matches codes with year-awareness
- Adds category columns to mortality data
- Reports match rates and distributions

**Creates:**

- `uk_mortality_by_cause_1901_2025_harmonized.csv`
- `uk_mortality_comprehensive_1901_2025_harmonized.csv`

### 3. Demonstration

```bash
cd data_sources/mortality_stats/development_code
python demonstrate_harmonized_system.py
```

Shows example analyses and validates the system works correctly.

## Improving Classifications

If you need to adjust the harmonization:

1. **Edit `build_harmonized_categories.py`**
   - Modify `HARMONIZED_CATEGORIES` dictionary
   - Add/remove keywords for each category
   - Create new categories if needed

2. **Re-run the build process:**

   ```bash
   cd data_sources/mortality_stats/development_code
   python build_harmonized_categories.py
   python add_harmonized_categories_to_mortality.py
   ```

3. **Review results:**
   - Check `icd_harmonized_categories.csv`
   - Look for low-confidence classifications
   - Validate with domain experts

## Validation and Quality

### Recommend Manual Review For

1. **Low confidence classifications** (17.8% of codes)
2. **Critical analyses** requiring high accuracy
3. **Rare diseases** that might be misclassified
4. **New disease categories** (HIV, modern conditions)

### Quality Checks

- ✅ Year-aware matching prevents cross-period contamination
- ✅ 82.2% high or medium confidence classifications
- ✅ Categories align with modern ICD-10 chapters
- ✅ Validated against known historical disease patterns

## Future Enhancements

1. **Machine Learning Classification** - Use NLP for better categorization
2. **ICD-10 Integration** - Extend to 2001-2025 data
3. **Subcategories** - Add second-level detail within major categories
4. **Expert Validation** - Medical historian review of mappings
5. **Cross-ICD Equivalence Tables** - Track specific disease evolution

## References

- WHO ICD Classifications: https://www.who.int/classifications/icd/
- Historical Disease Classification Research
- ONS Mortality Data Documentation

## Contact

For questions about the harmonized classification system, see the main mortality_stats documentation or ICD_DESCRIPTIONS_README.md.
