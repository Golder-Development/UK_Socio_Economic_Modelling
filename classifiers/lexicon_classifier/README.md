# Generic Lexicon-Based Classification Engine

## Overview

This is a **domain-agnostic, explainable classification system** that maps text descriptions to a configurable taxonomy using weighted lexicons and deterministic rules.

Originally designed for ICD mortality codes, this engine is now **completely generic** and can classify any structured or semi-structured text where:

- Terminology evolves or varies over time
- Descriptions are inconsistent or abbreviated  
- Categories require both statistical scoring and logical rules
- Auditability and explainability are critical

This is **not a machine-learning black box**.  
It is a **deterministic, inspectable, and fully configurable decision system**.

## Key Architectural Principle: Separation of Concerns

**The classification engine is centralized and reusable.**  
**Domain knowledge lives with the data sources.**

```
UK_Socio_Economic_Modelling/
│
├── classifiers/                           # Centralized reusable tools
│   └── lexicon_classifier/
│       ├── __init__.py
│       ├── engine.py                      # Domain-agnostic classification engine
│       └── README.md                      # This file
│
└── data_sources/
    ├── mortality_stats/
    │   └── socio_economic_classification/
    │       ├── settings.py                # ICD-specific configuration
    │       ├── classify_mortality.py      # Convenience script
    │       └── lexicons/                  # ICD category lexicons
    │           ├── L1_01_Infectious_and_Communicable_Diseases.csv
    │           ├── L1_02_Maternal_and_Early-Life_Mortality.csv
    │           └── ...
    │
    └── [future_dataset]/
        └── classification/
            ├── settings.py                # Different taxonomy
            ├── classify_[dataset].py
            └── lexicons/
                └── ...
```

This structure ensures:
- ✅ **Single source of truth** - One engine implementation
- ✅ **Domain isolation** - Each dataset has its own settings and lexicons
- ✅ **Easy reuse** - Import the engine, provide your settings
- ✅ **Independent maintenance** - Update engine logic or domain knowledge separately

---

## How It Works

### Core Classification Engine (`engine.py`)

The engine is **completely domain-agnostic**. It accepts:

1. **Input data** (DataFrame with text to classify)
2. **Lexicon directory** (CSV files with weighted terms)
3. **Settings module** (taxonomy, rules, thresholds)

And returns a classified DataFrame with:
- Original data
- Assigned category
- Confidence level
- Full traceability

### Settings Module (`settings.py`)

Each data source has its own `settings.py` defining:

```python
# 1. Taxonomy - your classification categories
TAXONOMY: Dict[str, str] = {
    "CAT_01": "Category One",
    "CAT_02": "Category Two",
    # ...
}

# 2. Hard Overrides - deterministic rules that force classification
HARD_OVERRIDES: Dict[str, List[Tuple[str, str]]] = {
    "CAT_01": [
        ("specific_term", "token"),
        ("exact phrase", "phrase"),
    ],
}

# 3. Confidence Thresholds - when to trust the classification
CONFIDENCE_THRESHOLDS = {
    "hard_override_score": 999,
    "high_min_score": 18,
    "high_min_margin": 6,
    "medium_min_score": 10,
    "medium_min_margin": 3,
}

# 4. Column Mappings - how to find data in your CSV
INPUT_COLUMNS = {
    "code": ["code", "id", "classification_code"],
    "description": ["description", "text", "label"],
}

# 5. File Configuration
DEFAULT_PATHS = {
    "lexicon_dir": "lexicons",
    "input_csv": "data/input.csv",
    "output_csv": "output/classified.csv",
}
```

### Lexicons (Knowledge Layer)

Each category has a CSV lexicon:

| term | weight | match_type | source | notes |
|------|--------|------------|--------|-------|
| pneumonia | 8 | token | core | Primary indicator |
| respiratory | 3 | token | context | Supporting term |
| other | -2 | token | negative | Too generic |

**Match Types:**
- `token` - Exact word match (after normalization)
- `phrase` - Multi-word sequence
- `substring` - Characters anywhere in text
- `regex` - Regular expression pattern

**Lexicon normalization:** All lexicon terms are normalized with the same `TEXT_NORMALIZATION` rules applied to input text (lowercasing, punctuation removal, whitespace collapse). This prevents mismatches like parenthesized phrases in the lexicon vs. punctuation-stripped input.

**Token matching options:**
- `TOKEN_MATCH_OPTIONS = {"enable_plural_variants": True}` (in settings) enables simple plural/singular variants for token terms (`term`, `term`s, `term`es, `y`→`ies`, stripping trailing `s`).
- Disable by setting `enable_plural_variants` to `False` if you prefer strict token equality.

**Weights:**
- Positive weights boost category score
- Negative weights reduce generic matches
- Higher magnitude = stronger signal

---

## Classification Process

For each text description:

1. **Normalize text** → lowercase, remove punctuation, clean whitespace
2. **Check hard overrides** → If matched, classification locked
3. **Score all categories** → Sum lexicon weights for matching terms
4. **Select best category** → Highest score wins
5. **Assign confidence** → Based on score and margin over runner-up

```
Input: "Cholera infection reported"
│
├─ Normalize: "cholera infection reported"
├─ Check overrides: None triggered
├─ Score categories:
│   ├─ L1_01 (Infectious): cholera(10) + infection(5) = 15
│   ├─ L1_05 (Chronic NCD): 0
│   └─ ...
├─ Best: L1_01 (score=15, margin=15)
└─ Confidence: high
```

---

## Using the Engine

### From Python Code

```python
import pandas as pd
from classifiers.lexicon_classifier import engine

# Import your domain-specific settings
from your_module import settings

# Load your data
df = pd.read_csv("input.csv")

# Prepare and classify
df = engine.prepare_input_dataframe(df, settings)
df = engine.split_multi_codes(df, settings)  # Optional: handle comma-separated codes
result = engine.classify_dataframe(df, "path/to/lexicons", settings)

# Save results
result.to_csv("output.csv", index=False)
```

### Validating Lexicons

Before running classification, validate your lexicons for conflicts:

```bash
# From the project root
python classifiers/lexicon_classifier/validate_lexicons.py \
  --lex_dir data_sources/mortality_stats/socio_economic_classification/lexicons \
  --settings_module data_sources.mortality_stats.socio_economic_classification.settings
```

**Or from Python:**

```python
from classifiers.lexicon_classifier.validate_lexicons import validate_lexicons
import settings

issues = validate_lexicons("path/to/lexicons", settings)
if issues["critical"]:
    print("Critical issues found - fix before using!")
```

**Validation checks:**
- Duplicate terms within the same lexicon
- Cross-lexicon term conflicts (same term in multiple categories)
- Substring/token overlaps that may double-count
- Positive/negative weight conflicts
- Regex pattern warnings

#### Version Override Pattern

If you need to override the version column (e.g., from command-line arguments), do it **after** `prepare_input_dataframe()` but **before** classification:

```python
# Prepare input (creates standardized columns including version)
df = engine.prepare_input_dataframe(df, settings)

# Override version if needed (wrapper-level convenience feature)
if version_override:
    df[settings.DEFAULT_COLUMNS["version"]] = version_override

# Continue with classification
df = engine.split_multi_codes(df, settings)
result = engine.classify_dataframe(df, "path/to/lexicons", settings)
```

**Command-line example:**
```python
parser.add_argument("--version", help="Override version for all records")
args = parser.parse_args()

df = engine.prepare_input_dataframe(df, settings)
if args.version:
    df[settings.DEFAULT_COLUMNS["version"]] = args.version
```

This pattern keeps the engine generic while allowing domain-specific wrappers to add convenience features.

### From Command Line

Each data source can have a convenience script:

```bash
# From mortality_stats directory
python classify_mortality.py --input_csv data.csv --output_csv results.csv

# Or use defaults from settings
python classify_mortality.py
```

---

## Configuration Reference

### Taxonomy Definition

Maps category codes to human-readable names.

```python
TAXONOMY: Dict[str, str] = {
    "L1_01": "Infectious and Communicable Diseases",
    "L1_02": "Maternal and Early-Life Mortality",
}
```

### Hard Override Rules

Structural rules that **guarantee** classification regardless of lexicon scores.

```python
HARD_OVERRIDES: Dict[str, List[Tuple[str, str]]] = {
    "L1_02": [
        ("pregnancy", "token"),      # Word must appear
        ("at birth", "phrase"),       # Exact phrase
        ("neonat", "substring"),      # Partial match
        (r"born \d{4}", "regex"),    # Pattern match
    ],
}

# Priority order for checking overrides
OVERRIDE_PRIORITY: List[str] = [
    "L1_02",  # Check maternal/early-life first
    "L1_08",  # Then violence
    # ...
]
```

### Confidence Thresholds

```python
CONFIDENCE_THRESHOLDS = {
    "hard_override_score": 999,    # Score when override triggers
    "high_min_score": 18,          # Minimum score for high confidence
    "high_min_margin": 6,          # Minimum lead over second place
    "medium_min_score": 10,        # Medium confidence threshold
    "medium_min_margin": 3,        # Medium confidence margin
}
```

**Confidence Logic:**
- **High**: Top score ≥ 18 AND margin ≥ 6 (or hard override)
- **Medium**: Top score ≥ 10 AND margin ≥ 3
- **Low**: Everything else

### Input Column Mappings

```python
INPUT_COLUMNS = {
    "code": ["code", "icd_code", "id"],
    "description": ["description", "desc", "text", "label"],
    "version": ["version", "icd_version", "source"],
}

DEFAULT_COLUMNS = {
    "code": "code",
    "description": "description",
    "version": "version",
}

DEFAULT_VERSION = "UNK"  # If no version column exists
```

### Output Configuration

```python
OUTPUT_COLUMNS = {
    "version": "version",
    "code": "code",
    "description": "description",
    "category_code": "category_code",
    "category_name": "category_name",
    "confidence": "classification_confidence",
}
```

### Lexicon Schema

```python
LEXICON_SCHEMA = {
    "term_column": "term",
    "weight_column": "weight",
    "match_type_column": "match_type",
    "source_column": "source",      # Optional
    "notes_column": "notes",        # Optional
}

LEXICON_FILE_PATTERN = r"(L1_\d{2})"  # Regex to extract category code
VALID_MATCH_TYPES = ["token", "phrase", "substring", "regex"]
```

### Text Processing

```python
TEXT_NORMALIZATION = {
    "lowercase": True,
    "replace_dash": True,          # Replace dashes with space
    "remove_punctuation": True,
    "collapse_whitespace": True,
}
```

---

## Workflow: Adapting to a New Domain

### 1. Create Your Settings

Copy and adapt `settings.py` template:

```python
# In data_sources/your_dataset/classification/settings.py

TAXONOMY = {
    "POLICY_01": "Economic Policy",
    "POLICY_02": "Social Welfare",
    "POLICY_03": "Environmental",
}

HARD_OVERRIDES = {
    "POLICY_01": [
        ("gdp", "token"),
        ("fiscal policy", "phrase"),
    ],
}

# ... configure thresholds, columns, etc.
```

### 2. Create Lexicons

For each category, create `{CATEGORY_CODE}_Description.csv`:

```csv
term,weight,match_type,source,notes
taxation,10,token,core,Primary indicator
budget,8,token,core,Strong signal
economy,3,token,context,Supporting term
```

### 3. Write Convenience Script

```python
# In data_sources/your_dataset/classification/classify_your_data.py

import sys, os
sys.path.insert(0, os.path.abspath('../../../../'))

from classifiers.lexicon_classifier import engine
import settings

# Your custom classification logic here
```

### 4. Run and Iterate

```bash
python classify_your_data.py --input_csv data.csv
```

Review results → Update lexicons → Re-run → Repeat

---

## Why This Architecture?

### Before: Monolithic

```
└── data_sources/mortality_stats/Icd_level1_scoring/
    ├── classification_engine.py  # Hardcoded for ICD
    ├── settings.py               # Mixed with engine
    └── lexicons/
```

**Problems:**
- Can't reuse engine for other datasets
- Domain logic mixed with algorithm
- Hard to maintain multiple classification tasks

### After: Modular

```
├── classifiers/lexicon_classifier/  # Reusable engine
│   └── engine.py
│
└── data_sources/
    ├── mortality_stats/
    │   └── socio_economic_classification/
    │       ├── settings.py      # ICD-specific
    │       └── lexicons/
    └── economic_indicators/
        └── classification/
            ├── settings.py      # Economics-specific
            └── lexicons/
```

**Benefits:**
- ✅ One engine, many applications
- ✅ Clear separation of concerns
- ✅ Independent versioning
- ✅ Easier testing and maintenance

---

## Validation & Quality Control

### Settings Validation

The settings module includes automatic validation:

```python
def validate_settings():
    """Check configuration integrity."""
    # Taxonomy not empty
    # Override categories exist in taxonomy
    # Thresholds are positive
    # Match types are valid
```

Runs automatically on import, catches errors early.

### Classification Review

Low-confidence results indicate:
- Missing lexicon terms
- Ambiguous descriptions
- Competing categories

**Workflow:**
1. Filter for `confidence == "low"`
2. Review assigned categories
3. Update lexicons with missing terms
4. Re-classify and compare

### Lexicon Management

Treat lexicons as **living documents**:
- Version control with git
- Document term sources in CSV
- Review and prune periodically
- Measure before/after accuracy

---

## Example Use Cases

### ICD Mortality Codes (Included)

Maps ICD-1 through ICD-11 codes to socio-economic mortality categories.

**Challenges solved:**
- 150+ years of terminology evolution
- Inconsistent abbreviations
- Missing or ambiguous descriptions

### Policy Document Classification

```python
TAXONOMY = {
    "POL_ECO": "Economic Policy",
    "POL_SOC": "Social Welfare",
    "POL_ENV": "Environmental",
}
```

### Customer Feedback Routing

```python
TAXONOMY = {
    "PRODUCT": "Product Quality",
    "SERVICE": "Customer Service",
    "BILLING": "Billing Issues",
}
```

### Historical Archive Cataloging

```python
TAXONOMY = {
    "PARL": "Parliamentary Records",
    "LEGAL": "Court Proceedings",
    "ADMIN": "Administrative Docs",
}
```

**Any domain where:**
- Categories can be defined
- Terms indicate categories
- Explainability matters

---

## Why Not Machine Learning?

This system prioritizes:

- ✅ **Explainability**: Every decision is traceable
- ✅ **Reproducibility**: Same input → same output
- ✅ **Auditability**: Rules are visible and reviewable
- ✅ **Small data friendly**: Works with 10 or 10,000 records
- ✅ **No model drift**: Stable over time
- ✅ **Stakeholder trust**: Non-technical review possible

**When to choose this over ML:**
- Policy or regulatory work
- Historical analysis
- Public-facing research
- Limited training data
- Need full transparency

**When ML might be better:**
- Massive datasets
- Complex feature interactions
- Optimization over interpretability
- Tolerance for probabilistic errors

---

## API Reference

### Core Functions

#### `classify_dataframe(df, lex_dir, settings)`

Main classification function.

**Args:**
- `df`: Input DataFrame with standardized columns
- `lex_dir`: Path to lexicon directory
- `settings`: Settings module

**Returns:** DataFrame with classification results

---

#### `score_description(description, lexicons, settings)`

Score a single description against all categories.

**Args:**
- `description`: Text to classify
- `lexicons`: Loaded lexicon data
- `settings`: Settings module

**Returns:** `(best_category_code, scores_dict)`

---

#### `load_lexicons(lex_dir, settings)`

Load all lexicon CSV files.

**Args:**
- `lex_dir`: Path to lexicon directory
- `settings`: Settings module

**Returns:** Dictionary mapping category codes to term lists

---

### Utility Functions

#### `prepare_input_dataframe(df, settings)`

Standardize column names and handle missing columns.

#### `split_multi_codes(df, settings)`

Split rows with comma-separated codes.

#### `normalise(text, text_normalization)`

Normalize text according to configuration.

#### `apply_hard_override(text, settings)`

Check if text triggers hard override rules.

#### `confidence_from_scores(scores, settings)`

Determine confidence level from score distribution.

---

## Extending the Engine

### Common Extensions

1. **Multi-label classification** - Return top N categories
2. **Hierarchical taxonomy** - Parent/child relationships
3. **Context-aware scoring** - Use metadata in scoring
4. **Batch processing** - Parallel processing for scale
5. **Web API** - REST endpoint for classification
6. **Active learning** - Export uncertain cases for review

All extensions preserve backward compatibility.

---

## Status & Roadmap

**Current Status:**
- ✅ Engine: Production-ready, domain-agnostic
- ✅ Architecture: Centralized and reusable
- ✅ ICD Example: Fully implemented
- ✅ Documentation: Complete

**Future Enhancements:**
- Multi-label classification
- Confidence calibration tools
- Performance profiling
- Example datasets for other domains

---

## Philosophy

> "Knowledge and logic should be separate.  
> Domain experts maintain lexicons.  
> Engineers maintain the engine.  
> Neither blocks the other."

This design enables:
- Domain experts to improve classification without coding
- Developers to enhance engine without domain expertise
- Independent review and version control
- Scalable knowledge management

---

## Migration Guide

### If You Have Existing Code

1. **Keep your lexicons and settings** - They work as-is
2. **Update import statements**:
   ```python
   # Old
   from classification_engine import classify_dataframe
   
   # New
   from classifiers.lexicon_classifier import engine
   result = engine.classify_dataframe(df, lex_dir, settings)
   ```
3. **Update function calls** - Pass `settings` as parameter
4. **Test** - Results should be identical

### Creating New Classifications

1. Copy `settings.py` template
2. Define your taxonomy
3. Create lexicons
4. Write convenience script
5. Run and iterate

---

## Support & Contribution

This is a research tool for policy and historical analysis.

**To improve accuracy:**
- Update lexicons (no code changes needed)
- Adjust confidence thresholds
- Add hard override rules

**To enhance engine:**
- Submit pull requests
- Document changes
- Preserve backward compatibility

---

## License

Project-specific. Intended for research and policy analysis.

---

## Credits

**Author:** Paul Golder (Hysnap)  
**Project:** UK Socio-Economic Modelling  
**Purpose:** Transparent, explainable classification for public policy research

---

**"If it can handle ICD-1 through ICD-11, it can handle almost anything."**
