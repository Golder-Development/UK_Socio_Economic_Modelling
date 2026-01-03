# Manual Overrides System - Quick Start

## Overview

The Manual Overrides System fills missing ICD codes in your mortality data pipeline. It does **NOT** replace existing classifications.

## Quick Usage

### 1. Standard Classification (with manual overrides)

```bash
python classify_mortality.py --input_csv your_data.csv --output_csv results.csv
```

### 2. Skip Manual Overrides

```bash
python classify_mortality.py --input_csv your_data.csv --skip_manual_overrides
```

### 3. Use Custom Overrides File

```bash
python classify_mortality.py --input_csv your_data.csv --manual_overrides path/to/custom_overrides.csv
```

## Adding Manual Overrides

### Step 1: Identify Missing Codes

Run the full pipeline to find unmatched codes:

```bash
python development_code/regenerate_all_data_clean.py
```

Check the unmatched reports in the outputs directory.

### Step 2: Edit manual_overrides.csv

Add rows for codes that are truly missing from source data:

```csv
icd_version,icd_code,cause_description,L1_category,confidence,reason,date_added
ICD-3,178,Malignant neoplasm unspecified,L1_05,high,Code missing from icd3.xls,2026-01-03
ICD-7,245,Thyroid disorder variant,L1_05,medium,Historical code not documented,2026-01-03
```

### Step 3: Re-run Classification

```bash
python classify_mortality.py --input_csv your_data.csv
```

The system will:
- ✓ Load manual overrides
- ✓ Fill missing descriptions ONLY (never overwrites existing data)
- ✓ Apply pre-defined classifications
- ✓ Report statistics

## Example Output

```
Loading input from: data/icd3_compiled.csv
Loaded 66,132 records

Preparing input data...
Applying manual overrides for missing codes...
  → 3 missing code(s) filled with manual overrides
  → 2 override(s) skipped (code exists in source data)

Classifying against 10 categories...
[OK] Classification complete

Manual classifications applied: 3
```

## Testing

Test the system before running on real data:

```bash
python test_manual_overrides.py
```

## Important Rules

1. **Only fills missing data** - Existing descriptions are NEVER overwritten
2. **Applied before classification** - Manual overrides integrate early in pipeline
3. **Fully documented** - Every override requires a `reason` explaining why it's needed
4. **Version-specific** - Same code number in different ICD versions is handled separately
5. **Validated** - System checks all categories and confidence levels are valid

## File Format

Required columns (all must be present):

- `icd_version`: ICD version (e.g., ICD-1, ICD-2, ICD-10)
- `icd_code`: The code identifier
- `cause_description`: Description of the cause of death
- `L1_category`: Category code (L1_01 through L1_10)
- `confidence`: high, medium, or low
- `reason`: Why this manual entry is needed
- `date_added`: When added (YYYY-MM-DD)

## Common Scenarios

### Scenario 1: Code Missing from Source File

**Problem**: ICD-3 code 178 appears in mortality data but not in icd3.xls

**Solution**:
```csv
ICD-3,178,Malignant neoplasm unspecified,L1_05,high,Code missing from icd3.xls source. Classification from WHO historical docs.,2026-01-03
```

### Scenario 2: Historical Code Lost

**Problem**: Old ICD-2 code has no description available anywhere

**Solution**:
```csv
ICD-2,99,Cause unknown,L1_10,low,Historical code from 1915 with no available documentation.,2026-01-03
```

### Scenario 3: Administrative Code

**Problem**: Non-medical administrative code needs classification

**Solution**:
```csv
ICD-7,999,Administrative entry,L1_10,high,Administrative code for data quality issues.,2026-01-03
```

## Full Documentation

See [MANUAL_OVERRIDES_README.md](MANUAL_OVERRIDES_README.md) for complete documentation including:
- Detailed workflow
- Validation rules
- Audit procedures
- Best practices

---

**Questions?** See the main README or SYSTEM_REFERENCE.py
