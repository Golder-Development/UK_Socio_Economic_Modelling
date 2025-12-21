# Development Code for Mortality Stats

This folder contains development scripts, utilities, and work-in-progress items used to build and maintain the UK mortality datasets under `data_sources/mortality_stats`.

## Contents

- Key scripts:
  - `add_descriptions_year_aware.py` — Adds ICD code descriptions to datasets with year-aware matching.
  - `build_code_descriptions.py` — Extracts ICD code→description mappings from ONS Excel files.
  - `build_harmonized_categories.py` — Generates 24-category harmonized mapping from descriptions (includes Suicide, Accident, Homicide, Drugs, and War categories).
  - `rebuild_harmonized_from_archive.py` — Rebuilds harmonized dataset from archived comprehensive file with override support (NEW - primary recommended method).
  - `build_crosstab_icd_harmonization.py` — Generates audit crosswalk table to review code→category mappings (NEW).
  - `create_interactive_mortality_dashboard.py` — Generates three Plotly interactive dashboards with filtering and drill-down (UPDATED).
  - `add_harmonized_categories_to_mortality.py` — Legacy method - applies harmonized categories without replacing original ICD codes.
  - `build_comprehensive_mortality_1901_2025.py` — Build pipeline for comprehensive outputs.
  - Plus supporting scripts (verification, checks, examination utilities).
- Input data:
  - `icd_harmonized_overrides.csv` — User-editable CSV for customizing specific code→category assignments (NEW).
- WIP directories:
  - `downloaded_sourcefiles/` — Raw ONS downloads used during extraction.
  - `extract_20251220_172134/` — Temporary extraction artefacts for debugging/repro.
- Dev docs:
  - `BUILD_SUMMARY.md`, `COMPREHENSIVE_DATABASE_README.md`, `ICD_DESCRIPTIONS_README.md` — Engineering notes and build guidance.

## Outputs & Data Locations

- Scripts read/write CSV files in the parent folder: `data_sources/mortality_stats/`.
- Main artefacts include:
  - `icd_code_descriptions.csv`, `icd_harmonized_categories.csv`
  - `uk_mortality_by_cause_1901_2025_with_descriptions.csv`
  - `uk_mortality_by_cause_1901_2025_harmonized.csv`
  - Comprehensive variants under the same folder.

## How to Run (Windows / PowerShell)

From the repo root or the `mortality_stats` folder:

```powershell
# Activate the virtual environment
& H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/Activate.ps1

# Run key build steps (recommended workflow)
cd data_sources/mortality_stats/development_code

# Step 1: Generate harmonized categories from keywords
H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/python.exe build_harmonized_categories.py

# Step 2: Rebuild harmonized dataset from archive (with override support)
H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/python.exe rebuild_harmonized_from_archive.py

# Step 3: Generate audit crosswalk to review mappings
H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/python.exe build_crosstab_icd_harmonization.py

# Step 4: Create interactive dashboards
H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/python.exe create_interactive_mortality_dashboard.py
```

**Legacy Method** (still supported, not recommended):

```powershell
H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/python.exe add_descriptions_year_aware.py
H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/python.exe add_harmonized_categories_to_mortality.py
```

## Cross-Repo References (Checked)

A workspace-wide search found no imports or external references to these scripts outside `data_sources/mortality_stats`. Data files are referenced within this folder's documentation only. If you encounter path errors in future code, update references to the new location `data_sources/mortality_stats/development_code`.

## Notes

- Original ICD codes are preserved in all final datasets; new harmonized columns are additive.
- For ICD-2+ extraction improvements, work continues in `build_comprehensive_mortality_1901_2025.py`.
