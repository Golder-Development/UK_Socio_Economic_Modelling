# Methods: ICD Harmonisation Approach

## Purpose

This system is designed to support **longitudinal population-level analysis** of mortality data across the full history of ICD revisions (1901–2000), where direct comparison of raw ICD codes is not possible.

The goal is **analytical consistency**, not clinical precision.

To achieve this, individual ICD codes are mapped into a small number of **stable, conceptually broad disease categories** that retain meaning across classification regimes while accepting a deliberate loss of diagnostic granularity.

---

## Overview of the Harmonisation Process

Each ICD code is assigned to **one of 19 harmonized disease categories** using a structured, transparent, and reproducible process:

1. **Year-aware code interpretation**  
   ICD codes are interpreted strictly within the ICD version valid for the year of observation.  
   Code meanings are never carried across periods.

2. **Keyword-based category matching**  
   Each harmonized category is defined by a curated list of disease-related keywords.  
   Code descriptions are scanned and matched against these lists.

3. **Category assignment**  
   - The category with the highest number of keyword matches is selected.  
   - Where no keywords are matched, the code is assigned to a catch-all category.

4. **Confidence classification**  
   Each assignment is labelled to reflect the strength of the match.

This approach prioritises **interpretability and auditability** over opaque optimisation.

---

## Keyword Matching: Scope and Limitations

Keyword matching operates on **historical disease descriptions**, not clinical ontologies or semantic embeddings.

- It is **not natural language understanding**
- It does **not infer latent clinical meaning**
- It reflects the terminology actually used in each historical ICD revision

This design makes the system robust to ICD structural changes, but means that:
- historically vague terminology remains vague
- some rare or poorly described conditions cannot be confidently classified

This is an intentional trade-off.

---

## Classification Confidence Levels

Each ICD code receives a `classification_confidence` label:

- **High** – two or more category-specific keyword matches  
- **Medium** – one keyword match  
- **Low** – no keyword matches (fallback assignment)

Across the full ICD corpus:
- **82.2%** of codes are classified with **high or medium confidence**
- **17.8%** are classified with **low confidence**

Confidence labels are retained in all downstream datasets and should be respected in analysis.

---

## Output Scope and Coverage

- **Total ICD codes mapped**: 24,561  
- **Mortality rows classified**: 91.1%

The difference between code counts and mortality row counts reflects the structure of the mortality data (codes repeated across years, age groups, and sexes), not classification gaps.

---

## Analytical Implications

This harmonisation enables:
- comparison of disease burden across ICD transitions
- long-run trend analysis
- demographic pattern analysis within stable categories

It does **not** preserve:
- disease subtypes
- evolving clinical distinctions
- diagnostic or reimbursement-level detail

All analyses should be interpreted accordingly.
