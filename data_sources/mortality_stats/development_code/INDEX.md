# Development Scripts Index

This folder contains the development and maintenance scripts for the mortality database. Outputs are written to the parent folder `data_sources/mortality_stats/`.

## Scripts

- `build_code_descriptions.py` — Extract ICD code→description mappings from ONS Excel files.
- `add_descriptions_year_aware.py` — Add year-aware descriptions to mortality data.
- `build_harmonized_categories.py` — Create 19 harmonized disease categories from descriptions.
- `add_harmonized_categories_to_mortality.py` — Apply harmonized categories to datasets.
- `build_mortality_1901_2019.py` — Build historical dataset (ICD-1 period complete).
- `build_comprehensive_mortality_1901_2025.py` — Extended builder (ICD-2+ improvements pending).
- `analyze_comprehensive_mortality.py` — Analysis runner for comprehensive outputs.
- `fetch_uk_mortality_stats.py` — Fetch recent data from ONS APIs.
- Inspection/validation: `check_structure.py`, `check_recent_data.py`, `verify_output.py`, `examine_ons_data.py`.
- Demonstration: `demonstrate_harmonized_system.py`, `show_side_by_side.py`, `verify_columns_preserved.py`.

## How to Run (Windows / PowerShell)

```powershell
# From repo root
cd data_sources/mortality_stats/development_code

# Use the project's virtual environment
& H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/Activate.ps1

# Examples
python build_code_descriptions.py
python build_harmonized_categories.py
python add_descriptions_year_aware.py
python add_harmonized_categories_to_mortality.py
```

## Notes

- Scripts write outputs back to `data_sources/mortality_stats/`.
- Original ICD codes remain intact; harmonized columns are additive.
