# ICD Mortality Classification

This directory contains **domain-specific configuration** for classifying ICD mortality codes using the centralized lexicon classification engine.

## Structure

```
socio_economic_classification/
├── settings.py                # ICD-specific taxonomy and rules
├── classify_mortality.py      # Convenience script for classification
└── lexicons/                  # Category-specific term lexicons
    ├── L1_01_Infectious_and_Communicable_Diseases.csv
    ├── L1_02_Maternal_and_Early-Life_Mortality.csv
    ├── L1_03_Congenital_and_Developmental_Conditions.csv
    ├── L1_04_Later-Life_Mortality.csv
    ├── L1_05_Chronic_Non-Communicable_Diseases.csv
    ├── L1_06_Respiratory_and_Environmental_Disease.csv
    ├── L1_07_Injury_and_Accidental_Harm.csv
    ├── L1_08_Violence_and_Conflict.csv
    ├── L1_09_Self-Harm_and_Substance_Use.csv
    └── L1_10_Ill-Defined_Administrative_and_Other_Causes.csv
```

## Classification Engine

The classification logic lives in the centralized, reusable engine:

```
UK_Socio_Economic_Modelling/
└── classifiers/
    └── lexicon_classifier/
        ├── engine.py       # Domain-agnostic classification engine
        └── README.md       # Full engine documentation
```

See [classifiers/lexicon_classifier/README.md](../../../../classifiers/lexicon_classifier/README.md) for complete engine documentation.

## Quick Start

### Classify ICD Codes

```bash
# Using all defaults from settings.py
python classify_mortality.py

# Specify input and output files
python classify_mortality.py --input_csv your_data.csv --output_csv results.csv

# Override version for all records
python classify_mortality.py --input_csv inputs/icd1codes.csv --output_csv outputs/icd1results.csv --version ICD-1

# Specify custom lexicon directory
python classify_mortality.py --input_csv data.csv --lex_dir custom_lexicons/
```

**Command-line options:**
- `--input_csv`: Path to input CSV (default: from settings.py)
- `--output_csv`: Path to output CSV (default: from settings.py)
- `--version`: Override version for all records (e.g., `ICD-1`, `ICD-8`, `ICD-10`)
  - Overrides any version column in the input file
  - If not specified, uses version from input CSV or defaults to `UNK`
- `--lex_dir`: Path to lexicon directory (default: `lexicons/`)

### From Python

```python
import pandas as pd
from classifiers.lexicon_classifier import engine
import settings

# Load your ICD data
df = pd.read_csv("icd_codes.csv")

# Optional: Add version column if missing
# df['version'] = 'ICD-1'  # or 'ICD-8', 'ICD-9', 'ICD-10', etc.

# Prepare and classify
df = engine.prepare_input_dataframe(df, settings)
df = engine.split_multi_codes(df, settings)
result = engine.classify_dataframe(df, "lexicons", settings)

# Save results
result.to_csv("classified.csv", index=False)
```

## Configuration

### Taxonomy

ICD codes are mapped to 10 socio-economic mortality categories:

| Code | Category |
|------|----------|
| L1_01 | Infectious and Communicable Diseases |
| L1_02 | Maternal and Early-Life Mortality |
| L1_03 | Congenital and Developmental Conditions |
| L1_04 | Later-Life Mortality |
| L1_05 | Chronic Non-Communicable Diseases |
| L1_06 | Respiratory and Environmental Disease |
| L1_07 | Injury and Accidental Harm |
| L1_08 | Violence and Conflict |
| L1_09 | Self-Harm and Substance Use |
| L1_10 | Ill-Defined, Administrative, and Other Causes |

### Hard Override Rules

Certain terms **guarantee** classification regardless of lexicon scores:

- **L1_02**: pregnancy, newborn, childbirth, puerperal, etc.
- **L1_03**: congenital, malformation, deformity, etc.
- **L1_08**: homicide, murder, war, assault, etc.
- **L1_09**: suicide, self-harm
- **L1_01**: infectious organisms (streptococcus, tuberculosis, etc.)
- **L1_10**: cause unknown, found dead, etc.

See [settings.py](settings.py) for complete rule definitions.

### Lexicons

Each category has a weighted term lexicon stored in `lexicons/`.

**Lexicon schema:**

| Column | Description |
|--------|-------------|
| term | Word, phrase, substring, or regex pattern |
| weight | Positive or negative scoring weight |
| match_type | `token`, `phrase`, `substring`, or `regex` |
| source | Optional: term origin (e.g., "core", "organism") |
| notes | Optional: documentation |

**To improve accuracy:** Edit lexicons to add terms or adjust weights.

**Token matching options:** The classifier can auto-match simple plural/singular variants for token terms. Controlled via `TOKEN_MATCH_OPTIONS` in `settings.py`:

```python
TOKEN_MATCH_OPTIONS = {
  "enable_plural_variants": True,  # Match term, terms, termes, y→ies, and strip trailing s
}
```
Set to `False` for strict token equality.

**Lexicon normalization:** At load time, all lexicon terms are normalized with the same `TEXT_NORMALIZATION` rules applied to input text (lowercasing, punctuation removal, whitespace collapse). This removes punctuation/parenthesis mismatches between lexicon entries and the cleaned input descriptions.

## Input Requirements

Your CSV must contain:
- **Code column**: ICD code or identifier (recognized column names: `code`, `icd_code`, `icdcode`, `id`, `classification_code`)
- **Description column**: Text description to classify (recognized column names: `description`, `desc`, `text`, `label`, `name`)

Optional:
- **Version column**: ICD version identifier (recognized column names: `version`, `icd_version`, `revision`, `source`)
  - If missing, all records will be labeled as `UNK`
  - Recommended values: `ICD-1`, `ICD-8`, `ICD-9`, `ICD-10`, etc.

**Example input CSV with version:**
```csv
VERSION,CODE,DESCRIPTION
ICD-1,10,Small pox - vaccinated
ICD-1,20,Small pox - not vaccinated
```

**Example input CSV without version (will default to UNK):**
```csv
CODE,DESCRIPTION
10,Small pox - vaccinated
20,Small pox - not vaccinated
```

The engine automatically detects column names (case-insensitive). See `settings.INPUT_COLUMNS` for all supported variations.

### Multi-Code Support

If codes are comma-separated (e.g., `165,166`), they're automatically split into separate rows.

## Output Format

```csv
version,code,description,category_code,category_name,classification_confidence
ICD-8,001,"Cholera",L1_01,"Infectious and Communicable Diseases",high
ICD-9,042,"HIV disease",L1_01,"Infectious and Communicable Diseases",high
ICD-10,O00,"Ectopic pregnancy",L1_02,"Maternal and Early-Life Mortality",high
```

## Confidence Levels

- **High**: Strong lexicon score with clear margin, or hard override triggered
- **Medium**: Good score with moderate margin
- **Low**: Weak scores or close competition between categories

Low-confidence results indicate lexicon improvement opportunities.

## Workflow: Improving Accuracy

1. **Run classification**
2. **Review low-confidence results**
3. **Update lexicons** - Add missing terms or adjust weights
4. **Re-run and compare**
5. **Commit changes** to version control

No hand-editing of outputs needed. All improvements happen in lexicons and settings.

## ICD Version Support

The system handles ICD codes from **ICD-1 (1893) through ICD-11 (2022+)**, accommodating:

- Evolving medical terminology
- Inconsistent abbreviations
- Historical naming conventions
- Ambiguous or incomplete descriptions

This wide coverage demonstrates the engine's robustness across temporal and linguistic variation.

## Files

| File | Purpose | Edit Frequency |
|------|---------|----------------|
| `settings.py` | Taxonomy, rules, thresholds | Occasional (tune performance) |
| `lexicons/*.csv` | Category term weights | Often (continuous improvement) |
| `classify_mortality.py` | Convenience script | Rare (add features only) |

## Legacy Files

The `Icd_level1_scoring/` subdirectory contains the original monolithic implementation. It has been superseded by the modular architecture:

- **Old**: `Icd_level1_scoring/classification_engine.py` (hardcoded for ICD)
- **New**: `classifiers/lexicon_classifier/engine.py` (reusable)

The old files are preserved for reference but should not be used going forward.

## Related Documentation

- [Classification Engine Documentation](../../../../classifiers/lexicon_classifier/README.md) - Full engine guide
- [Settings Reference](settings.py) - ICD-specific configuration
- [Lexicon Schema](lexicons/) - Term weighting examples

## Status

- ✅ Production-ready for ICD classification
- ✅ Handles ICD-1 through ICD-11
- 📝 Lexicons are living documents - improve iteratively

## Philosophy

This is an **explainable, deterministic classification system** designed for research and policy analysis where:

- Decisions must be traceable
- Rules must be reviewable
- Results must be reproducible
- Stakeholders need transparency

It prioritizes **trust and accountability** over optimization metrics.

---

**Questions or improvements? See the main engine documentation or update lexicons.**
