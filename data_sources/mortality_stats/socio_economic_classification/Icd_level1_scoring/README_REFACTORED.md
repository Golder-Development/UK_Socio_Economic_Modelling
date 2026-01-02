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

## Key Architectural Change: Settings-Driven Design

**All domain-specific knowledge has been externalized to `settings.py`.**

This means:

- The core engine (`classification_engine.py`) contains **zero hardcoded taxonomy or domain logic**
- You can adapt this system to any classification problem by editing **only the settings file**
- The engine itself never needs to change

---

## System Architecture

project/
│
├── classification_engine.py    # Core classification logic (domain-agnostic)
├── settings.py                 # All domain-specific configuration
│
├── lexicons/                   # Knowledge layer (editable CSV files)
│   ├── CATEGORY_01_*.csv
│   ├── CATEGORY_02_*.csv
│   └── ...
│
└── data/
    ├── input.csv              # Your data to classify
    └── output/
        └── classified.csv     # Classification results

## Configuration via Settings

The `settings.py` file controls **everything**:

### 1. Taxonomy Definition

Define your classification categories:

```python
TAXONOMY: Dict[str, str] = {
    "L1_01": "Infectious and Communicable Diseases",
    "L1_02": "Maternal and Early-Life Mortality",
    # ... add your categories
}
```

### 2. Hard Override Rules

Set structural rules that guarantee classification regardless of scores:

```python
HARD_OVERRIDES: Dict[str, List[Tuple[str, str]]] = {
    "L1_02": [
        ("pregnancy", "token"),
        ("newborn", "token"),
    ],
    # ... define your override patterns
}
```

### 3. Confidence Thresholds

Control when classifications are high/medium/low confidence:

```python
CONFIDENCE_THRESHOLDS = {
    "hard_override_score": 999,
    "high_min_score": 18,
    "high_min_margin": 6,
    "medium_min_score": 10,
    "medium_min_margin": 3,
}
```

### 4. Input/Output Mappings

Define expected column names and output format:

```python
INPUT_COLUMNS = {
    "code": ["code", "icd_code", "id"],
    "description": ["description", "text", "label"],
    "version": ["version", "source"],
}

OUTPUT_COLUMNS = {
    "category_code": "category_code",
    "category_name": "category_name",
    "confidence": "classification_confidence",
}
```

### 5. File Paths and Patterns

Set default locations and naming conventions:

```python
DEFAULT_PATHS = {
    "lexicon_dir": "lexicons",
    "input_csv": "data/input.csv",
    "output_csv": "output/classified.csv",
}

LEXICON_FILE_PATTERN = r"(L1_\d{2})"  # Regex to extract category code from filenames
```

## Lexicons (Knowledge Layer)

Each category has a CSV lexicon with this schema:

| Column | Type | Description |
|--------|------|-------------|
| `term` | string | Word, phrase, or regex pattern |
| `weight` | integer | Positive or negative scoring weight |
| `match_type` | enum | `token`, `phrase`, `substring`, or `regex` |
| `source` | string | Optional: origin of term (e.g., "core", "organism") |
| `notes` | string | Optional: documentation |

### Match Types Explained

- **token**: Exact word match (after normalization)
- **phrase**: Multi-word sequence must appear
- **substring**: Characters must appear anywhere
- **regex**: Full regular expression matching

### Positive & Negative Weighting

- Strong indicators get high weights (e.g., `variola: +10`)
- Generic terms get low/negative weights (e.g., `other: -2`)
- This prevents generic terms from dominating classification

**Lexicons are the primary place to improve accuracy.**

## Classification Process

For each input row:

1. **Normalize text**
   - Lowercase, remove punctuation, collapse whitespace
   - (Configurable in `TEXT_NORMALIZATION` settings)

2. **Check hard overrides**
   - If any pattern matches → classification locked
   - Overrides are checked in priority order

3. **Score against all category lexicons**
   - For each lexicon, sum weights of matching terms
   - Calculate score for every category

4. **Select highest-scoring category**

5. **Assign confidence level**
   - Based on score magnitude and margin over second-best

## Input Requirements

The engine expects a CSV with at least:
- A **code/ID column** (identifies the record)
- A **description/text column** (content to classify)

Optional:
- A **version/source column** (preserved in output)

### Flexible Column Detection

The engine automatically detects columns based on the `INPUT_COLUMNS` mapping in settings:

```python
INPUT_COLUMNS = {
    "code": ["code", "icd_code", "id", "classification_code"],
    "description": ["description", "desc", "text", "label"],
}
```

If multiple text columns exist, they're automatically concatenated.

### Multi-Code Support

If a row contains comma-separated codes (e.g., `165,166`), it's automatically split into multiple rows.

---

## How to Use

### 1. Configure Your Domain

Edit `settings.py`:

- Define your taxonomy categories
- Set hard override rules
- Adjust confidence thresholds
- Map your column names

### 2. Generate/Edit Lexicons

Create lexicon CSV files matching your categories:

- Filename must contain the category code (matching `LEXICON_FILE_PATTERN`)
- Example: `L1_01_Infectious_Diseases.csv`

### 3. Run the Classifier

```bash
python classification_engine.py \
  --input_csv data/my_data.csv \
  --lex_dir lexicons \
  --output_csv output/classified.csv
```

Or use the defaults from settings:

```bash
python classification_engine.py
```

### 4. Output Format

```csv
version,code,description,category_code,category_name,classification_confidence
ICD-8,001,"Cholera",L1_01,"Infectious and Communicable Diseases",high
```

---

## Validation & Iteration Workflow

### Recommended approach:

1. **Run the classifier** with initial lexicons
2. **Review results** – especially low-confidence classifications
3. **Update lexicons** – add terms, adjust weights
4. **Re-run and compare** – check improvements
5. **Commit changes** – version control lexicons and settings

No hand-editing of outputs is required. All improvements happen in lexicons and settings.

---

## Reuse for Other Domains

### This engine can classify:

- Medical/clinical codes (any classification system)
- Public policy categories
- Legal or regulatory corpora  
- Media/news article topics
- Survey free-text responses
- Customer feedback sentiment
- Historical document types
- **Any text where you can define categories and write matching rules**

### To adapt to a new domain:

1. **Define taxonomy** in `settings.TAXONOMY`
2. **Create lexicons** for each category
3. **Add hard overrides** for critical patterns
4. **Adjust thresholds** based on your data
5. **Run and iterate**

The core engine never needs modification.

---

## Why Not Machine Learning?

This system was chosen because it is:

- ✅ **Explainable**: Every decision can be traced
- ✅ **Reproducible**: Same input always gives same output
- ✅ **Auditable**: All rules are visible and versionable
- ✅ **Robust to small datasets**: Works with 10 or 10,000 records
- ✅ **Stable over time**: No model drift
- ✅ **Transparent**: Stakeholders can review and validate logic

It is designed for **policy-relevant, public-facing analysis** where trust and accountability matter more than optimization metrics.

---

## Settings Validation

The `settings.py` file includes a `validate_settings()` function that runs on import:

- Checks taxonomy is not empty
- Verifies all override categories exist in taxonomy
- Validates confidence thresholds are positive
- Ensures match types are valid

This prevents configuration errors before runtime.

---

## Extending the Engine

### Common extensions:

1. **Multi-category assignment**: Modify `score_description()` to return top N categories
2. **Weighted overrides**: Add priority scores to override rules
3. **Context-aware scoring**: Pass metadata to scoring function
4. **Batch processing**: Add parallel processing for large datasets
5. **API wrapper**: Expose classification as a web service
6. **Active learning**: Export low-confidence cases for review

All extensions can be added without breaking existing functionality.

---

## File Inventory

| File | Purpose | Edit Frequency |
|------|---------|----------------|
| `classification_engine.py` | Core logic | Rarely (only for features) |
| `settings.py` | Domain configuration | Often (per domain) |
| `lexicons/*.csv` | Category knowledge | Often (continuous improvement) |
| `README.md` | Documentation | Occasionally |

---

## Status

- **Engine**: Production-ready, domain-agnostic
- **Settings**: Template for ICD classification (example)
- **Lexicons**: Living documents, improve iteratively
- **Taxonomy**: User-defined, stable per project

---

## Example Use Cases

### ICD Mortality Codes (included)

- Maps ICD-1 through ICD-11 to socio-economic mortality categories
- Handles evolution of medical terminology over 150+ years

### Policy Document Classification

```python
TAXONOMY = {
    "POL_01": "Economic Policy",
    "POL_02": "Social Welfare",
    "POL_03": "Environmental Regulation",
}
```

### Customer Feedback Routing

```python
TAXONOMY = {
    "FBK_01": "Product Quality",
    "FBK_02": "Customer Service",
    "FBK_03": "Billing Issues",
}
```

### Historical Archive Cataloging

```python
TAXONOMY = {
    "DOC_01": "Parliamentary Records",
    "DOC_02": "Court Proceedings",
    "DOC_03": "Administrative Correspondence",
}
```

---

## Philosophy

> "Knowledge and logic should be separate.  
> Domain experts maintain lexicons.  
> Engineers maintain the engine.  
> Neither blocks the other."

This design emerged from the realization that:

- Classification rules **are** domain knowledge
- Domain knowledge **changes** over time
- Code changes **require** developer involvement
- CSV changes **do not**

By separating concerns, we enable:

- Domain experts to improve classification without coding
- Developers to improve the engine without domain expertise
- Version control and review for both layers independently

---

## License / Attribution

Project-specific.  
Intended for research, policy analysis, and historical work.

---

## Migration Note

If you have existing code using `icd_level1_scoring_model.py`:

1. Move to `classification_engine.py`
2. Create a `settings.py` with your current configuration
3. Update import statements
4. Test with existing data to verify consistency

The classification logic is identical; only the structure has changed.

---

**"If it can handle ICD-1 through ICD-11, it can handle almost anything."**
