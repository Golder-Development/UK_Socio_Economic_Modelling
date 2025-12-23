# Contributing / Development Demarcation

This repository distinguishes between two areas of work:

- Core, tracked regeneration pipeline (versioned in Git)
- Local-only development sandbox (ignored by Git)

## Core (Tracked) Pipeline
These files are kept under version control and should remain reproducible from a clean clone:
- data_sources/mortality_stats/development_code/regenerate_all_data.py
- data_sources/mortality_stats/development_code/create_interactive_mortality_dashboard.py
- data_sources/mortality_stats/development_code/build_code_descriptions.py
- data_sources/mortality_stats/development_code/build_harmonized_categories.py
- data_sources/mortality_stats/development_code/rebuild_harmonized_from_archive.py
- data_sources/mortality_stats/development_code/build_crosstab_icd_harmonization.py
- data_sources/mortality_stats/development_code/validate_harmonized_categories.py
- data_sources/mortality_stats/development_code/mortality_source_config.json

Pipeline usage (Windows + venv):
```powershell
H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/python.exe data_sources/mortality_stats/development_code/regenerate_all_data.py --verbose
```
- `--skip-rebuild`: Skip harmonized dataset rebuild for faster iterations
- `--skip-dashboards`: Skip dashboard generation entirely

## Local Dev Sandbox (Ignored)
Local development helpers, ad‑hoc analysis, and experimentation live in:
- local_dev/
- local_dev/tools/

Examples moved here:
- Debug/verify/check/examine scripts (e.g., debug_dashboard_data.py, verify_*.py, check_*.py, examine_*.py)
- Convenience runners (e.g., regenerate_dashboards_and_docs.py)
- Documentation updaters (e.g., update_category_documentation.py, update_data_statistics.py, update_dashboard_list.py)

These scripts are intentionally ignored by Git via `.gitignore` so they never pollute the repository history. Keep them self‑contained and avoid adding hard dependencies back into the tracked pipeline.

## .gitignore Policy
To keep the repository clean:
- Entire local_dev/ is ignored.
- Most of data_sources/mortality_stats/development_code/ is ignored, with a whitelist for essential pipeline scripts listed above.
- Temporary/extracted inputs and Python caches are ignored.

## Adding New Workflows or Tools
- If it’s part of the reproducible pipeline, add it under development_code and whitelist it in .gitignore (only if needed).
- If it’s a helper, prototype, or doc updater, place it under local_dev/tools.
- Prefer no side effects except reading/writing clearly documented outputs.

## Documentation updates
- Documentation auto‑update scripts (stats/category lists) are local‑only. If you want automation in CI, consider promoting a script from local_dev/tools into the tracked pipeline after review.

## Pull Requests / Commits
- Do not commit local_dev content.
- Ensure the regeneration pipeline runs from a clean clone (venv setup + data sources) before pushing.
- Keep changes focused and avoid unrelated refactors.

## Quick Commands
Rebuild dashboards only:
```powershell
H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/python.exe data_sources/mortality_stats/development_code/create_interactive_mortality_dashboard.py
```
Update index links (tracked util):
```powershell
H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/python.exe sl_core/utils/update_generated_charts_section.py
```

For local‑only convenience (ignored):
```powershell
H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/python.exe local_dev/tools/regenerate_dashboards_and_docs.py
```
