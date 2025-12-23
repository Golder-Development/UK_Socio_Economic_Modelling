# UK Mortality Statistics — Data Summary

## Current Files (kept in this folder)

1. Yearly totals (long-run)

- File: `uk_mortality_yearly_totals_1901_2025.csv`
- Coverage: 1901–2025 (yearly total deaths)

1. Harmonized cause-of-death dataset

- File: `uk_mortality_by_cause_1901_onwards_harmonized.csv` (stored as `.zip` due to size)
- Columns: year, cause (original ICD code), cause_description, harmonized_category, harmonized_category_name, classification_confidence, sex, age, deaths
- Notes: Harmonization aligns cause categories across ICD versions; year-aware mapping prevents cross-period confusion.

1. Comprehensive harmonized dataset

- File: `uk_mortality_comprehensive_1901_onwards_harmonized.csv` (stored as `.zip` due to size)
- Purpose: Wider coverage variant including harmonized causes; use alongside the main harmonized file for broader analyses.

1. Rates and summaries

- File: `uk_mortality_rates_per_100k_yearly_totals.csv` — Annual deaths per 100k
- File: `uk_mortality_rates_per_100k_by_cause.csv` — Cause-specific rates per 100k
- File: `harmonized_categories_summary.csv` — Category counts and overview

1. Mappings

- File: `icd_code_descriptions.csv` — ICD code→description mappings (with ICD version)
- File: `icd_harmonized_categories.csv` — Code→harmonized category mappings

1. Documentation

- `README.md` — Getting started
- `INDEX.md` — Structure and usage
- `HARMONIZED_CATEGORIES_README.md` — Harmonization approach
- `HARMONIZED_QUICKSTART.md` — Quick usage guide

## Development and Archived Content

- All build scripts and WIP are in `development_code/`.
- Older CSVs have been moved to `development_code/archive_csv/` to reduce confusion.

## Data Sources

Place source files under: `ons_downloads/`

Recommended sources:

- ONS datasets: <https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/deaths/datasets>
- 21st Century Mortality Files (ICD-10)
- Historical ICD files (1901–2000) used for description extraction and harmonization

## What You Can Analyze Now

- Long-run trends in total mortality (1901–2025)
- Harmonized cause-of-death trends across ICD versions (primarily 1901–2000)
- Age and sex breakdowns per harmonized category
- Rates per 100k by year and by harmonized cause

## Important Notes

- Original ICD codes are preserved; harmonized columns are additive.
- Harmonization uses year-aware mapping to avoid mislabeling the same numeric code across different ICD periods.
- Later years may have limited cause detail depending on available sources; totals remain complete.

## Next Steps (Optional)

- Improve extraction for ICD-2+ periods in development scripts (see `development_code/`).
- Incorporate additional recent cause breakdowns when reliable sources are available.
