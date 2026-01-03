# Manual Overrides System Implementation Summary

## What Was Implemented

A comprehensive system to handle missing ICD codes in the mortality classification pipeline by providing manual classifications for codes that don't exist in source data.

## Files Created

### 1. Core Handler Module
- **Location**: `classifiers/lexicon_classifier/manual_overrides_handler.py`
- **Purpose**: Core logic for loading and applying manual overrides
- **Key Features**:
  - Validates override file format and content
  - Only fills missing data (never overwrites existing)
  - Tracks application statistics
  - Version and code-specific matching

### 2. Manual Overrides Data File
- **Location**: `data_sources/mortality_stats/socio_economic_classification/inputs/manual_overrides.csv`
- **Format**: CSV with columns: `icd_version`, `icd_code`, `cause_description`, `L1_category`, `confidence`, `reason`, `date_added`
- **Template**: Includes example entry showing proper format

### 3. Documentation
- **`inputs/MANUAL_OVERRIDES_README.md`**: Complete system documentation (purpose, format, workflow, examples)
- **`inputs/QUICKSTART.md`**: Quick reference guide for common tasks
- **`inputs/README.md`**: Directory overview and usage summary

### 4. Test Script
- **Location**: `data_sources/mortality_stats/socio_economic_classification/test_manual_overrides.py`
- **Purpose**: Validates that system works correctly
- **Tests**:
  - Loading overrides
  - Filling missing data
  - NOT overwriting existing data
  - Statistics reporting

## Integration Points

### Modified Files

1. **`classify_mortality.py`**
   - Added CLI arguments for manual overrides
   - Loads handler before classification
   - Applies overrides to fill missing descriptions
   - Applies manual classifications after lexicon scoring
   - Reports statistics

2. **`classifiers/lexicon_classifier/__init__.py`**
   - Exports `ManualOverridesHandler` and helper functions

3. **`settings.py`**
   - Added `manual_overrides` path to `DEFAULT_PATHS`

## System Flow

```
1. Load raw mortality data
   ↓
2. Prepare and normalize dataframe
   ↓
3. Load manual overrides from CSV
   ↓
4. Apply overrides to fill missing descriptions
   (ONLY where description is empty/missing)
   ↓
5. Split multi-codes
   ↓
6. Run lexicon-based classification
   ↓
7. Apply manual classifications
   (For codes that were filled by overrides)
   ↓
8. Output classified results
```

## Key Design Principles

### 1. Fill Missing Only
- **Never** overwrites existing descriptions
- Only applies when description is empty/missing
- Skipped overrides are tracked and reported

### 2. Early Integration
- Applied BEFORE lexicon classification
- Ensures manual fills go through same process
- Maintains consistency

### 3. Full Traceability
- Every override requires `reason` documentation
- `date_added` tracks when entry was created
- Output flags manual classifications
- Statistics reported at completion

### 4. Validation
- Checks required columns
- Validates L1 categories against taxonomy
- Validates confidence levels
- Version-specific matching

### 5. Separation of Concerns
- Raw source data: untouched
- Lexicon knowledge: in lexicon CSVs
- Manual fills: in separate override file
- Settings: in settings.py

## Usage Examples

### Standard Classification
```bash
python classify_mortality.py --input_csv data.csv
```
Auto-loads manual overrides

### Skip Manual Overrides
```bash
python classify_mortality.py --input_csv data.csv --skip_manual_overrides
```

### Custom Overrides File
```bash
python classify_mortality.py --input_csv data.csv --manual_overrides custom.csv
```

### From Python
```python
from classifiers.lexicon_classifier.manual_overrides_handler import ManualOverridesHandler
import settings

handler = ManualOverridesHandler("inputs/manual_overrides.csv", settings)
df = handler.apply_to_dataframe(df, fill_missing_only=True)
# ... continue with classification
result = handler.apply_classifications(classified_df)
handler.print_summary()
```

## Testing

Run the test script to verify functionality:

```bash
cd data_sources/mortality_stats/socio_economic_classification
python test_manual_overrides.py
```

Expected output:
- ✓ Existing descriptions NOT overwritten
- ✓ Missing descriptions filled with overrides
- Statistics summary

## Adding New Manual Overrides

### Workflow

1. **Identify Missing Codes**
   - Run pipeline, review unmatched reports
   - Verify codes are truly missing from source

2. **Research the Code**
   - Find historical documentation
   - Determine appropriate L1 category

3. **Add to CSV**
   ```csv
   ICD-3,178,Malignant neoplasm unspecified,L1_05,high,Missing from icd3.xls. WHO docs.,2026-01-03
   ```

4. **Re-run Classification**
   ```bash
   python classify_mortality.py --input_csv data.csv
   ```

5. **Verify**
   - Check override was applied
   - Review statistics in output

## Configuration

### Default Override File Location
Configured in `settings.py`:
```python
DEFAULT_PATHS = {
    "manual_overrides": os.path.join(
        os.path.dirname(__file__), "inputs", "manual_overrides.csv"
    ),
}
```

### CLI Override
```bash
--manual_overrides path/to/file.csv
```

## Error Handling

The system validates:
- File exists (gracefully handles missing file)
- Required columns present
- Valid L1 categories
- Valid confidence levels
- Proper CSV format

Errors are reported clearly with specific issues identified.

## Performance

- Efficient: Loads once, applies via DataFrame merge
- Minimal overhead: Only processes codes in input data
- Scales well: No performance impact from large override files

## Maintenance

### Regular Reviews
- Periodically review overrides for accuracy
- Update descriptions if better documentation found
- Remove overrides if codes added to source data

### Version Control
- Keep `manual_overrides.csv` in git
- Track changes via commits
- Document major changes in commit messages

### Audit Trail
- `reason` column documents justification
- `date_added` tracks entry age
- Can filter/sort by date for recent additions

## Future Enhancements (Optional)

Potential additions:
- Confidence score adjustment based on source quality
- Multi-file override support (per ICD version)
- Override validation against external ICD databases
- Web interface for managing overrides
- Automated suggestions from unmatched code analysis

## Documentation Structure

```
inputs/
├── manual_overrides.csv           # The override data
├── MANUAL_OVERRIDES_README.md     # Complete documentation
├── QUICKSTART.md                  # Quick reference
└── README.md                      # Directory overview
```

## Related Documentation

- Main classifier: `README.md`
- Engine documentation: `classifiers/lexicon_classifier/README.md`
- System reference: `data_sources/mortality_stats/SYSTEM_REFERENCE.py`
- Settings: `settings.py`

---

**Implementation Date**: 2026-01-03
**Status**: Complete and ready for use
**Testing**: Test script provided and functional
