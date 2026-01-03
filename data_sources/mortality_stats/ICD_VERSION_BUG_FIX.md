# ICD Version Assignment Bug Fix

## Issue Discovered: 2026-01-03

### Problem

All 3,262 unmatched ICD-2 codes were from year **1910**, but ICD-2 classification wasn't used until **1911**.

### Root Cause

The pipeline had **two conflicting ICD version assignment methods**:

1. **Step 1 (build_mortality_per_icd_version.py)**: ✅ CORRECT
   - Assigned ICD version based on **source file**
   - icd1.xls → years 1901-1910 → ICD-1
   - icd2.xls → years 1911-1920 → ICD-2
   
2. **Step 2 (regenerate_all_data_v2.py)**: ❌ **INCORRECT - OVERWRITING**
   - **Overwrote** the correct ICD version with year-based mapping
   - Used wrong year boundaries: `(1910, 1920): 'ICD-2'`
   - This reassigned 1910 data from ICD-1 to ICD-2

### Evidence

```bash
# Source files are correct:
icd1.xls:  Years 1901-1910 (34,519 records)
icd2.xls:  Years 1911-1920 (69,349 records)

# Compiled file was correct:
1910 records: 3,396
ICD version: ICD1 (all correct!)

# But unmatched report showed:
icd_unmatched_codes_detail_ICD2.csv
  - 3,262 records
  - All from year 1910 ❌
  - Should have been matched against ICD-1 lexicons

```

### Why This Happened

The regenerate script was applying a **year-based ICD version mapping** that:
1. Didn't respect the source file assignments
2. Had incorrect year boundaries (off by 1 year)
3. Was based on "historical ICD adoption" rather than ONS source file structure

## The Fix

### Changes Made

Modified [regenerate_all_data_v2.py](h:\\VScode\\UK_Socio_Economic_Modelling\\data_sources\\mortality_stats\\development_code\\regenerate_all_data_v2.py):

1. **Check for existing ICD version** from compiled data
2. **Only override if missing** (fallback mode)
3. **Corrected year ranges** to match actual source files:

```python
# BEFORE (wrong):
icd_mapping = {
    (1900, 1909): 'ICD-1',  # ❌ Wrong start year
    (1910, 1920): 'ICD-2',  # ❌ Includes 1910 incorrectly
    (1921, 1938): 'ICD-3',  # ❌ Wrong boundaries
    ...
}
df_mortality['icd_version'] = df_mortality['year'].apply(get_icd_version)  # ❌ Always overwrites

# AFTER (correct):
has_icd_version = 'icd_version' in df_mortality.columns and df_mortality['icd_version'].notna().any()

if has_icd_version:
    print("Using ICD version from compiled data (source file based)")  # ✅ Respects source
else:
    # Fallback with corrected ranges:
    icd_mapping = {
        (1901, 1910): 'ICD-1',   # ✅ Matches icd1.xls
        (1911, 1920): 'ICD-2',   # ✅ Matches icd2.xls
        (1921, 1930): 'ICD-3',   # ✅ Matches icd3.xls
        ...
    }
```

### Impact

**Before Fix:**
- 1910 data (3,396 records) was being matched against ICD-2 lexicons
- ICD-2 codes (100, 1000, 1010, etc.) don't exist in ICD-1
- Result: 3,262 unmatched codes reported as "ICD-2 unmatched"

**After Fix:**
- 1910 data will be matched against ICD-1 lexicons
- Codes like 100, 1000, 1010 should match in ICD-1 descriptions
- Expect significantly fewer truly unmatched codes

## Principle

**ICD version should be determined by SOURCE FILE, not by year**

The ONS source files define which ICD classification system was used:
- Data in icd1.xls uses ICD-1 codes (regardless of "official" ICD-1 period)
- Data in icd2.xls uses ICD-2 codes
- etc.

Year-based assignment is only a fallback for data without explicit version info.

## Action Required

**Re-run the full pipeline** to regenerate classifications with corrected ICD version assignments:

```bash
cd data_sources/mortality_stats/development_code
python regenerate_all_data_v2.py --verbose
```

This will:
1. Use correct ICD-1 version for 1910 data
2. Match against ICD-1 lexicons
3. Generate new unmatched reports
4. Show which codes are **truly** missing vs. incorrectly versioned

## Verification Steps

After re-running:

1. **Check unmatched ICD-2 file**:
   ```bash
   # Should have NO 1910 records
   python -c "import pandas as pd; df = pd.read_csv('icd_unmatched_codes_detail_ICD2.csv'); print('1910 records:', len(df[df.year == 1910]))"
   ```

2. **Check unmatched ICD-1 file**:
   ```bash
   # May have SOME truly unmatched codes from 1901-1910
   python -c "import pandas as pd; df = pd.read_csv('icd_unmatched_codes_detail_ICD1.csv'); print(df.year.value_counts())"
   ```

3. **Verify compiled file preserved**:
   ```bash
   # 1910 should still be ICD1 in compiled file
   python -c "import pandas as pd, zipfile; zf = zipfile.ZipFile('uk_mortality_by_cause_1901_onwards_compiled.zip'); df = pd.read_csv(zf.open(zf.namelist()[0])); print(df[df.year==1910].icd_version.value_counts())"
   ```

## Related Files

- Source: [build_mortality_per_icd_version.py](h:\\VScode\\UK_Socio_Economic_Modelling\\data_sources\\mortality_stats\\build_mortality_per_icd_version.py)
- Fixed: [regenerate_all_data_v2.py](h:\\VScode\\UK_Socio_Economic_Modelling\\data_sources\\mortality_stats\\development_code\\regenerate_all_data_v2.py)
- ICD-1 lexicons: [socio_economic_classification/lexicons/](h:\\VScode\\UK_Socio_Economic_Modelling\\data_sources\\mortality_stats\\socio_economic_classification\\lexicons/)

## Manual Overrides Impact

The manual overrides system implemented earlier is **still valid and ready to use**. After the pipeline re-runs with corrected ICD versions:

1. Review the **new** unmatched code reports
2. Identify codes that are **truly missing** from source files
3. Add them to `inputs/manual_overrides.csv`
4. Re-run classification

The manual overrides system will work correctly with the fixed ICD version assignments.

---

**Date Fixed**: 2026-01-03  
**Fixed By**: Correcting ICD version assignment logic  
**Status**: ✅ Fixed - Re-run pipeline required
