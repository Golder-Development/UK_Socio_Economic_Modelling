# ICD Code Descriptions for UK Mortality Data

## Overview

This directory contains tools to add human-readable cause-of-death descriptions to UK mortality statistics. The descriptions are extracted from ONS historical mortality Excel files and matched to mortality data using **year-aware** code matching.

## ⚠️ Why Year-Aware Matching is Critical

ICD (International Classification of Diseases) codes changed significantly across different time periods. **The same code number can mean completely different causes of death in different years.**

### Example: Code 10.0 Means Different Things

- Code `10.0` in ICD-1 (1901-1910) = **"Small pox - vaccinated"**
- Code `10.0` in ICD-4 (1931-1939) = **"Diphtheria"**

Therefore, descriptions **must** be matched based on **both the code AND the year** to ensure accuracy.

## ICD Version Timeline

| ICD Version | Year Range | Source File | Codes |
|-------------|------------|-------------|-------|
| ICD-1 | 1901-1910 | icd1.xls | 192 |
| ICD-2 | 1911-1920 | icd2.xls | 317 |
| ICD-3 | 1921-1930 | icd3.xls | 301 |
| ICD-4 | 1931-1939 | icd4.xls | 327 |
| ICD-5 | 1940-1949 | icd5.xls | 454 |
| ICD-6 | 1950-1957 | icd6.xls | 2,060 |
| ICD-7 | 1958-1967 | icd7.xlsx | 2,184 |
| ICD-8 | 1968-1978 | icd8.xls | 2,850 |
| ICD-9a | 1979-1984 | icd9_a.xlsx | 5,292 |
| ICD-9b | 1985-1993 | icd9_b.xls | 5,292 |
| ICD-9c | 1994-2000 | icd9_c.xls | 5,292 |

**Total: 24,561 code-description mappings across 7,879 unique codes**

## Files Generated

### 1. Code Description Files

- **`icd_code_descriptions.csv`** ✅ **USE THIS**
  - Complete mapping with ICD version and year ranges
  - Columns: `code`, `description`, `source_file`, `icd_version`
  - Contains all 24,561 mappings with full context

- **`icd_code_descriptions_simplified.csv`** ⚠️ **DEPRECATED**
  - Single description per code (uses most recent)
  - Columns: `code`, `description`
  - **DO NOT USE** for historical data - can assign wrong descriptions!

### 2. Mortality Data with Descriptions

- **`uk_mortality_by_cause_1901_2025_with_descriptions.csv`**
  - Original: `year`, `cause`, `sex`, `age`, `deaths`
  - **Added**: `cause_description` (inserted after `cause`)
  - Uses year-aware matching

- **`uk_mortality_comprehensive_1901_2025_with_descriptions.csv`**
  - Same structure and year-aware matching

## Usage Guide

### Step 1: Build Code Descriptions (One-time)

```bash
python build_code_descriptions.py
```

**What it does:**
- Extracts code descriptions from all ONS Excel files in `ons_downloads/extracted/`
- Reads the "description" sheet from each ICD file
- Preserves ICD version information for year-aware matching

**Creates:**
- `icd_code_descriptions.csv` (complete with versions - **recommended**)
- `icd_code_descriptions_simplified.csv` (legacy format)

### Step 2: Add Descriptions to Mortality Data

```bash
python add_descriptions_year_aware.py
```

**What it does:**
- Loads the complete descriptions with ICD version info
- Determines which ICD version applies to each row based on year
- Matches codes using **both** code AND ICD version
- Reports detailed match statistics by ICD version

**Creates:**
- `*_with_descriptions.csv` files with proper year-aware descriptions

## Scripts Reference

### Primary Scripts

1. **`build_code_descriptions.py`**
   - Extracts descriptions from ONS Excel files
   - Creates the master description mapping
   - Run this first

2. **`add_descriptions_year_aware.py`** ✅ **RECOMMENDED**
   - Year-aware description matching
   - Prevents incorrect cross-period assignments
   - Provides ICD version breakdown in logs

### Deprecated Scripts

- **`add_descriptions_to_mortality_data.py`** ⚠️ **DO NOT USE**
  - Uses simplified mapping without year awareness
  - Can assign wrong descriptions to historical data
  - Replaced by `add_descriptions_year_aware.py`

### Utility Scripts

- **`examine_with_xlrd.py`** - Inspects .xls file structure
- **`extract_all_descriptions.py`** - Tests extraction from all ICD files
- **`check_causes.py`** - Compares data codes with available descriptions
- **`verify_descriptions.py`** - Validates year-aware matching results

## Data Quality Report

### Current Match Rates

For `uk_mortality_by_cause_1901_2025.csv`:

```
ICD-1 (1901-1910):  100.0% matched ✅
ICD-2 (1911-1920):    0.0% matched (data contains only "Unknown")
ICD-3 (1921-1930):    0.0% matched (data contains only "Unknown")
ICD-4 (1931-1939):    0.0% matched (data contains only "Unknown")
...remaining periods similar...
```

**Overall**: 34,519 / 37,897 rows matched (91.1%)

### Why Low Match Rates After 1910?

The historical data extraction process (`build_comprehensive_mortality_1901_2025.py`) currently only properly captures cause codes from ICD-1 (1901-1910). For later periods, the data contains placeholder "Unknown" values instead of actual cause codes.

This indicates the extraction logic needs improvement for ICD-2 through ICD-9c files.

### Unmatched Code Examples

- `"Unknown"` - Placeholder when actual cause code missing from source
- Years 2001+ - ICD-10 period not yet mapped

## Example Output

### Year-Aware Descriptions Working Correctly

```csv
year,cause,cause_description,sex,age,deaths
1901,10.0,Small pox - vaccinated,Female,01-04,1
1901,100.0,Plague,Male,20-24,2
1901,1000.0,Pericarditis,Female,05-09,43
```

If code `10.0` appeared in 1935 data, it would correctly show "Diphtheria" instead.

## Technical Implementation

### Year-to-ICD Version Mapping

```python
ICD_YEAR_RANGES = {
    'ICD-1 (1901-1910)': (1901, 1910),
    'ICD-2 (1911-1920)': (1911, 1920),
    ...
}
```

### Matching Logic

1. Load mortality data with `year` and `cause` columns
2. Determine ICD version for each row: `icd_version = get_icd_version_for_year(year)`
3. Merge on **both** `cause` AND `icd_version`
4. Result: Each code gets its correct period-specific description

### Dependencies

Required packages:
```bash
pip install pandas xlrd openpyxl
```

- **pandas** - Data processing
- **xlrd** - Reading old .xls files (ICD-1 through ICD-9c except ICD-7)
- **openpyxl** - Reading .xlsx files (ICD-7, ICD-9a)

## Future Improvements

### High Priority

1. **Fix Historical Data Extraction**
   - Update `build_comprehensive_mortality_1901_2025.py`
   - Properly extract cause codes from ICD-2 through ICD-9c Excel files
   - Currently only ICD-1 codes are captured

2. **Add ICD-10 Support**
   - Map modern codes for 2001-2025 data
   - Extract from ONS modern mortality datasets

### Medium Priority

3. **Automated Pipeline**
   - Integrate description adding into main build script
   - Auto-generate `*_with_descriptions.csv` during data builds

4. **Code Hierarchy**
   - Add ICD chapter/category groupings
   - Create parent-child code relationships

### Low Priority

5. **Cross-ICD Mapping**
   - Create equivalence table across ICD versions
   - Enable longitudinal cause-of-death tracking

## References

- [ONS Historical Mortality Data](https://www.ons.gov.uk/)
- [WHO ICD Classifications](https://www.who.int/classifications/icd/)

## Contact

For questions or issues with the description matching system, refer to the main project documentation or check the mortality_stats directory README files.
