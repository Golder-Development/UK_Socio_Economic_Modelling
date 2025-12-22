# How NOT to Use This Dataset

This dataset is designed for **population-level, longitudinal analysis** across changing ICD systems.

It is **not** suitable for all analytical purposes.

The cases below describe common misuses and why they should be avoided.

---

## ❌ Do NOT Use This Dataset for Clinical Analysis

This dataset:
- does not preserve diagnostic subtypes
- collapses clinically distinct conditions
- is not validated for patient-level interpretation

Do not use it for:
- clinical decision-making
- treatment effectiveness analysis
- diagnostic accuracy assessment
- individual risk modelling

Use original ICD codes for any clinical or medical analysis.

---

## ❌ Do NOT Treat Harmonized Categories as Medical Truth

The harmonized categories are **analytical groupings**, not medical entities.

They are designed to be:
- stable across time
- comparable across ICD versions

They are **not**:
- equivalent to ICD-10 chapters
- clinically exhaustive
- immune to historical terminology bias

---

## ❌ Do NOT Ignore Classification Confidence

Every row includes a `classification_confidence` label.

Ignoring it risks:
- overstating precision
- treating ambiguous mappings as equally reliable

For high-stakes analysis:
- filter to **high** and **medium** confidence rows
- or test sensitivity to excluding low-confidence rows

---

## ❌ Do NOT Use “Other and Unclassified” as a Substantive Category

The **Other and Unclassified** category is a methodological necessity, not a disease group.

It should:
- not be treated as a medical trend
- not be compared directly with specific disease categories
- be analysed separately or excluded from headline findings

---

## ❌ Do NOT Use Harmonized Categories for Rare Disease Analysis

Rare diseases often:
- lack consistent historical naming
- appear only in later ICD revisions
- are under-represented in keyword-based matching

This dataset is not suitable for rare disease prevalence studies.

---

## ❌ Do NOT Assume Absence Equals Non-Existence

Zero values in early years reflect:
- historical classification practices
- diagnostic capability
- reporting norms

They do **not** imply conditions did not exist.

---

## ✔️ Appropriate Uses

This dataset works well for:
- long-run mortality trend analysis
- structural shifts in disease burden
- demographic pattern comparisons
- historical and policy-oriented research
