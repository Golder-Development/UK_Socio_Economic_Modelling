# ICD Socio-Economic Classification Engine

## Overview

This repository contains a **lexicon-driven, explainable classification system** designed to map ICD (International Classification of Diseases) codes and descriptions to a **locked Level-1 Socio-Economic Mortality Taxonomy**.

Although developed using ICD revisions (ICD-1 → ICD-8+), the system is **domain-agnostic** and can be reused to classify any structured or semi-structured textual codes where:

- terminology evolves over time  
- descriptions are inconsistent or abbreviated  
- “unspecified / other” is common but misleading  
- auditability and explainability matter  

This is **not a machine-learning black box**.  
It is a **deterministic, inspectable, and versionable decision system**.

---

## Locked Level-1 Taxonomy

The model classifies each record into exactly one of the following **10 locked categories**:

| Code | Category |
|----|----|
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

These categories are **conceptual**, not clinical — they describe *social and structural drivers of mortality*, not medical specialties.

---

## Design Principles

### 1. Knowledge is separate from logic
- **Lexicons** contain domain knowledge (words, phrases, organisms, patterns)
- **The scoring engine** contains only logic
- Either can evolve independently

### 2. “Unspecified” ≠ “Ill-defined”
Many ICD entries are:
- “Other …”
- “Unspecified …”

These usually mean **unspecified subtype**, not unknown cause.  
The model explicitly avoids collapsing these into L1_10 unless the *cause itself* is unknown.

### 3. Deterministic and explainable
For every classification you can determine:
- which terms matched
- how strongly they contributed
- why one category beat another
- how confident the decision was

### 4. Structural truths override statistics
Certain realities should *never* be out-voted by word frequency:

- Birth-related ≠ accident  
- Congenital ≠ chronic  
- Violence ≠ disease  
- Suicide ≠ poisoning  

These are enforced via **hard overrides**.

---

## System Architecture

project/
│
├── icd_level1_scoring_model.py # Classification engine
├── write_lexicons.py # Auto-generates lexicon CSVs
│
├── lexicons/ # Knowledge layer (editable)
│ ├── L1_01_Infectious_.csv
│ ├── L1_02_Maternal_.csv
│ ├── ...
│ └── L1_10_Ill-Defined_*.csv
│
└── data/
└── icd_codes.csv # Any ICD-like input file

---

## Lexicons (Knowledge Layer)

Each Level-1 category has its own CSV lexicon with the following schema:

| Column | Meaning |
|------|-------|
| term | Word, phrase, stem, or regex |
| weight | Positive or negative integer weight |
| match_type | `token`, `phrase`, `substring`, or `regex` |
| source | `core`, `organism`, `disease`, `environmental`, etc. |
| notes | Optional documentation |

### Positive & Negative Weighting
- Strong indicators (e.g. *variola*, *puerperal*, *homicide*) have high weights
- Generic terms (*other*, *unspecified*) are weak or negatively weighted
- This prevents false assignment to “Ill-defined”

Lexicons are **the primary place to improve accuracy**.

---

## Hard Overrides (Structural Rules)

Before scoring, the engine checks for decisive patterns:

Examples:
- `newborn`, `immaturity`, `delivery` → **Maternal and Early-Life**
- `congenital`, `spina bifida` → **Congenital**
- `homicide`, `execution`, `war` → **Violence and Conflict**
- `suicide` → **Self-Harm**
- organism stems (`streptococc`, `mycobacter`) → **Infectious**

Overrides guarantee **conceptual correctness** even with sparse text.

---

## Classification Process

For each row:

1. **Normalise text**
   - lowercase
   - punctuation stripped
   - hyphens and em-dashes normalised

2. **Apply hard overrides**
   - if triggered → classification locked

3. **Score against all 10 lexicons**
   - weights summed per category

4. **Select highest-scoring category**

5. **Assign confidence**
   - `high` → dominant score or hard override
   - `medium` → clear winner, moderate margin
   - `low` → weak or ambiguous signal

---

## Input Requirements

The engine expects a CSV with at least:

## Optional:

If two description columns exist (as in some ICD revisions), they are automatically concatenated.

Multiple ICD codes on one row (e.g. `165,166`) are automatically split.


## How to Use

### 1. Generate lexicons (once)

python write_lexicons.py
Creates the lexicons/ directory and all 10 lexicon files.

2. Run the classifier
python icd_level1_scoring_model.py \
  --input_csv data/icd_codes.csv \
  --lex_dir lexicons \
  --output_csv output/icd_level1_mapping.csv

3. Output format
icd_version,icd_code,description,level1_code,level1_name,classification_confidence

## Validation & Iteration Workflow

### Recommended approach:

#### Run the model

##### Review low-confidence or unexpected classifications

##### Update the relevant lexicon CSV

#### Re-run the model

##### Confirm improvements via diffs

#### No hand-editing of outputs is required.

## Reuse Beyond ICD

### This framework can be reused for:

public policy classification
legal or regulatory corpora
media analysis
archival datasets
survey free-text coding

Simply replace the lexicons and taxonomy.

## Why Not Machine Learning?

This system was chosen because it is:

explainable
reproducible
auditable
robust to small datasets
stable over time

It is designed for public-facing, policy-relevant analysis, not opaque optimisation.

## Status

Model logic: stable
Lexicons: living documents
Taxonomy: locked

Further ICD revisions (9, 10, 11) can be added without changing the engine.

## License / Attribution

Project-specific.
Intended for research, policy analysis, and historical work.

“If it can survive ICD-1 to ICD-8, it can survive almost anything.”