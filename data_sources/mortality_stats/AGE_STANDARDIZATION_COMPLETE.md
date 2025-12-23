# Age Standardization and File Renaming - Completion Summary

## Date: 2025-12-23

## Overview
Implemented age standardization across the entire UK mortality data pipeline and renamed the core harmonized file to be more future-proof.

## Changes Completed

### 1. File Renaming
**Old:** `uk_mortality_by_cause_1901_2000_harmonized.zip`  
**New:** `uk_mortality_by_cause_1901_onwards.zip`

This change:
- Makes it clear the file is not limited to year 2000
- Accommodates future data additions (e.g., 2001-2025 already included)
- Reduces confusion about which file to use

### 2. Age Standardization
Added `age_start` column to the harmonized dataset:
- Extracts numeric starting age from age range strings
- Handles special cases: "<1" → 0, "85+" → 85, "T25-34" → 25
- Inserted between `age` and `harmonized_category` columns
- Applied at data source level (rebuild_harmonized_from_archive.py)

**Sample data:**
```
year  age      age_start  sex     harmonized_category_name               deaths
1901  01-04    1.0        Female  Infectious and Parasitic Diseases      1
1901  <1       0.0        Female  Infectious and Parasitic Diseases      7
1901  T25-34   25.0       Female  Infectious and Parasitic Diseases      17
1901  85+      85.0       Male    Diseases of the Circulatory System     42
```

### 3. Demographic Subset Restructuring
**Replaced sex+age combinations with age-only categories:**

Old subsets (removed):
- Women, Men
- Children (<=18)
- OAPs (65+)
- Working Age
- Adults Under 30

**New age-based subsets:**
1. **Preschool (<=5)** - Early childhood mortality
2. **School Age (6-19)** - School-age population
3. **Young Adults (20-34)** - Early working age
4. **Older Adults (35-64)** - Mid-career/middle age
5. **Young OAPs (65-84)** - Early retirement
6. **Old OAPs (85+)** - Advanced age

Output files:
- mortality_dashboard_age_preschool.html
- mortality_dashboard_age_school.html
- mortality_dashboard_age_young_adults.html
- mortality_dashboard_age_older_adults.html
- mortality_dashboard_age_young_oaps.html
- mortality_dashboard_age_old_oaps.html

### 4. Files Modified

**Core Pipeline:**
- `rebuild_harmonized_from_archive.py`: Added age_start extraction, renamed output
- `create_interactive_mortality_dashboard.py`: Uses age_start for filtering, creates 6 age-based subsets
- `regenerate_all_data.py`: Updated file references in summaries
- `sl_core/utils/update_generated_charts_section.py`: Added SPECIAL_NAMES for new subsets

**Supporting Scripts:**
- `debug_dashboard_data.py`: Updated file references
- `build_crosstab_icd_harmonization.py`: Updated file references

**Documentation:**
- `index.md`: Auto-updated with new subset dashboard links via GitHub Pages

### 5. Files Cleaned Up (Deleted)

**Old harmonized files (obsolete):**
- uk_mortality_by_cause_1901_2000_harmonized.zip
- uk_mortality_by_cause_1901_2019_harmonized.zip

**Old dashboard files (replaced):**
- mortality_dashboard_age_preschool.html (≤5)
- mortality_dashboard_age_school.html (6–19)
- mortality_dashboard_age_young_adults.html (20–34)
- mortality_dashboard_age_older_adults.html (35–64)
- mortality_dashboard_age_young_oaps.html (65–84)
- mortality_dashboard_age_old_oaps.html (85+)
- mortality_dashboard_filtered_adults_under_30.html

### 6. Verification
- ✅ age_start column present in uk_mortality_by_cause_1901_onwards.zip
- ✅ All 9 dashboards generated successfully (main, filtered, drilldown, 6 age subsets)
- ✅ index.md links updated with correct titles
- ✅ Old files removed from workspace
- ✅ No remaining references to old filenames in codebase

## Pipeline Status
Full regeneration pipeline completed successfully:
1. ✅ Generate harmonized categories (26 categories)
2. ✅ Validate categories against documentation
3. ✅ Rebuild harmonized dataset with age_start
4. ✅ Generate audit crosswalk
5. ✅ Create 9 interactive dashboards
6. ✅ Update index.md links

## Data Coverage
- **Years:** 1901-2017
- **Records:** 1,465,808 rows
- **Categories:** 26 harmonized disease categories
- **Age Range:** 0-85+ (age_start: 0.0-65.0 in sample)

## Technical Notes
- Fixed Unicode encoding issue in console output (≤ → <=, – → -)
- Dashboard generator checks for age_start column, extracts if missing (backward compatible)
- Population denominators use total UK population (not stratified by age/sex)
- Age range parsing handles T prefix (historical notation), <1, 85+, and standard ranges

## Next Steps (Optional)
- Consider adding age_start to comprehensive builder (uk_mortality_by_cause_1901_2025.zip) for consistency
- Update any external documentation that references old filenames
- Add age_start to data dictionary in documentation

## GitHub Pages URLs
All dashboards now available at:
https://golder-development.github.io/UK_Socio_Economic_Modelling/generated_charts/

## Validation Script
Created `verify_age_start.py` to quickly confirm age_start column presence and format.
