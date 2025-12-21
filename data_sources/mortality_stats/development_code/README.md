# Development Code for Mortality Stats

This folder contains development scripts, utilities, and work-in-progress items used to build and maintain the UK mortality datasets under `data_sources/mortality_stats`.

## Contents
- Key scripts:
  - `add_descriptions_year_aware.py` — Adds ICD code descriptions to datasets with year-aware matching.
  - `build_code_descriptions.py` — Extracts ICD code→description mappings from ONS Excel files.
  - `build_harmonized_categories.py` — Generates 19-category harmonized mapping from descriptions.
  - `add_harmonized_categories_to_mortality.py` — Applies harmonized categories without replacing original ICD codes.
  - `build_comprehensive_mortality_1901_2025.py` — Build pipeline for comprehensive outputs (ICD-2+ improvements pending).
  - Plus supporting scripts (verification, checks, examination utilities).
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

# Run key build steps
cd data_sources/mortality_stats/development_code
H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/python.exe build_code_descriptions.py
H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/python.exe build_harmonized_categories.py
H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/python.exe add_descriptions_year_aware.py
H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/python.exe add_harmonized_categories_to_mortality.py
```

Outputs are written back to `data_sources/mortality_stats/`.

## Cross-Repo References (Checked)
A workspace-wide search found no imports or external references to these scripts outside `data_sources/mortality_stats`. Data files are referenced within this folder's documentation only. If you encounter path errors in future code, update references to the new location `data_sources/mortality_stats/development_code`.

## Notes
- Original ICD codes are preserved in all final datasets; new harmonized columns are additive.
- For ICD-2+ extraction improvements, work continues in `build_comprehensive_mortality_1901_2025.py`.
