# Classification Input Files

This directory contains input files for the mortality classification pipeline.

## Files

### `manual_overrides.csv`

Manual classification overrides for ICD codes that are **missing from source data**.

**Purpose**: Fill gaps in the classification pipeline where codes exist in mortality data but have no descriptions or are missing from the official ICD source files.

**Important**: This system is designed to **FILL MISSING DATA ONLY**, not to override or replace existing classifications from the lexicon engine.

See [MANUAL_OVERRIDES_README.md](MANUAL_OVERRIDES_README.md) for detailed documentation on:
- When to use manual overrides
- File format and column specifications
- How to add new overrides
- Integration with the pipeline
- Best practices and audit procedures

## Usage

Manual overrides are automatically loaded when running classification:

```bash
python classify_mortality.py --input_csv data.csv
```

To skip manual overrides:

```bash
python classify_mortality.py --input_csv data.csv --skip_manual_overrides
```

To use a different overrides file:

```bash
python classify_mortality.py --input_csv data.csv --manual_overrides path/to/overrides.csv
```

## Validation

The system automatically validates:
- All required columns are present
- L1 categories are valid
- Confidence levels are valid (high, medium, low)
- Only missing codes are affected (existing data is never overwritten)

---

For questions or issues, see the main project README or SYSTEM_REFERENCE.py
