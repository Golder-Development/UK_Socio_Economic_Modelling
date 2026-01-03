# Manual Overrides System

## Purpose

This system fills **missing data gaps** in the mortality classification pipeline by providing manual classifications for ICD codes that do not exist in the source data or cannot be matched through the lexicon-based classification engine.

**CRITICAL**: This system is designed to **FILL MISSING DATA ONLY**, not to replace or override existing classifications.

## File Location

`inputs/manual_overrides.csv`

## When to Use Manual Overrides

Use manual overrides when:
- An ICD code is referenced in mortality data but missing from the source ICD description files
- A code exists but has no description text available for lexicon matching
- Historical codes have been lost or are incomplete in the ONS source data

**DO NOT** use manual overrides to:
- Override lexicon classifications for existing codes
- Correct what you perceive as "wrong" classifications
- Replace low-confidence classifications with manual ones

## File Format

```csv
icd_version,icd_code,cause_description,L1_category,confidence,reason,date_added
ICD-3,123,Missing cardiac condition,L1_05,high,Code missing from source data,2026-01-03
ICD-7,456,Respiratory disease variant,L1_06,medium,Historical code not in ONS files,2026-01-03
```

### Column Specifications

| Column | Required | Description |
|--------|----------|-------------|
| `icd_version` | Yes | ICD version identifier (e.g., ICD-1, ICD-2, ICD-10) |
| `icd_code` | Yes | The ICD code number/identifier |
| `cause_description` | Yes | Human-readable description of the cause of death |
| `L1_category` | Yes | Level 1 category code (e.g., L1_01, L1_02, etc.) |
| `confidence` | Yes | Confidence level: `high`, `medium`, or `low` |
| `reason` | Yes | Documentation of why this manual entry was needed |
| `date_added` | Yes | Date when this entry was added (YYYY-MM-DD) |

### Valid L1 Categories

- `L1_01`: Infectious and Communicable Diseases
- `L1_02`: Maternal and Early-Life Mortality
- `L1_03`: Congenital and Developmental Conditions
- `L1_04`: Later-Life Mortality
- `L1_05`: Chronic Non-Communicable Diseases
- `L1_06`: Respiratory and Environmental Disease
- `L1_07`: Injury and Accidental Harm
- `L1_08`: Violence and Conflict
- `L1_09`: Self-Harm and Substance Use
- `L1_10`: Ill-Defined, Administrative, and Other Causes

## Pipeline Integration

Manual overrides are applied **BEFORE** lexicon classification in the pipeline:

```
1. Load raw mortality data
2. Load manual overrides
3. Apply manual overrides to fill missing codes
4. Run lexicon-based classification
5. Generate harmonized output
```

This ensures:
- Missing codes get filled with manual classifications
- Existing codes are never overwritten
- The lexicon engine processes all available data

## Workflow for Adding Manual Overrides

1. **Identify Missing Codes**: Run the pipeline and review unmatched code reports
   ```bash
   python development_code/regenerate_all_data_clean.py
   # Check: icd_unmatched_codes_detail_*.csv
   ```

2. **Verify Code is Actually Missing**: Confirm the code doesn't exist in source data
   - Check the original ICD Excel files
   - Review the compiled per-ICD-version data

3. **Research the Code**: Find documentation for what the code represents
   - Historical ICD documentation
   - Medical literature
   - Alternative sources (WHO, medical archives)

4. **Add Entry**: Add a row to `manual_overrides.csv` with:
   - Accurate version and code
   - Best available description
   - Appropriate L1 category
   - Clear reason documenting the source of classification
   - Today's date

5. **Test**: Re-run the pipeline and verify the override is applied correctly

## Audit and Review

- Regular review of manual overrides is recommended
- The `reason` column provides audit trail
- Keep this file under version control
- Document any sources used for classification decisions

## Examples

### Example 1: Code Missing from Source Data
```csv
icd_version,icd_code,cause_description,L1_category,confidence,reason,date_added
ICD-3,178,Malignant neoplasm of unspecified site,L1_05,high,Code present in mortality data but missing from icd3.xls source file. Classification from WHO historical records.,2026-01-03
```

### Example 2: Historical Code with No Description
```csv
icd_version,icd_code,cause_description,L1_category,confidence,reason,date_added
ICD-2,99,Unknown cause,L1_10,low,Code appears in 1912 data but has no description in source files. Unable to determine actual cause.,2026-01-03
```

## Important Notes

- **Validation**: The system validates that manual overrides only apply to truly missing codes
- **Conflicts**: If a code exists in both source data AND manual overrides, source data wins
- **Performance**: Manual overrides are efficient - loaded once and merged before classification
- **Transparency**: All manual classifications are flagged in output for traceability

## Related Files

- `classifiers/lexicon_classifier/manual_overrides_handler.py` - Implementation
- `classify_mortality.py` - Integration point
- `settings.py` - Configuration

---

**Last Updated**: 2026-01-03
