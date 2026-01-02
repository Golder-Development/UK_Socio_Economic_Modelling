# Housing Data Collection

This folder contains scripts for fetching housing-related data from the ONS API.

## Overview

The scripts in this folder follow the standard ONS API patterns established in the parent directory. Each script connects to the ONS API, finds the relevant dataset, extracts dimensions and observations, and saves the data to CSV files.

## Available Data Sources

### 1. Index of Private Housing Rental Prices (`fetch_rental_prices.py`)

**Description:** Tracks the prices paid for renting property in the private rental sector in the UK.

**Usage:**

```bash
python fetch_rental_prices.py
```

**Output:** `extract_YYYYMMDD_HHMMSS/rental_prices_data.csv`

**Key Features:**

- Time series data on rental price indices
- Geographic breakdowns (UK, regions, local areas)
- Useful for analyzing rental market trends and affordability

---

### 2. Population Density (`fetch_population_density.py`)

**Description:** Measures the number of people per square kilometer across different geographic areas in the UK. This is Census 2021 data.

**Usage:**

```bash
python fetch_population_density.py
```

**Output:** `extract_YYYYMMDD_HHMMSS/population_density_data.csv`

**Key Features:**

- Census 2021 snapshot data
- Coverage: All 331 Lower Tier Local Authorities in England and Wales
- Direct CSV download (not observations API)
- Population density values range from rural (25.5/km²) to dense urban areas (15,702.9/km²)
- Essential for understanding housing pressure in different regions

**Note:** This script uses direct CSV download as it's Census 2021 data, which is provided as pre-computed tables rather than through the observations API.

---

### 3. Residence Type by Age (`fetch_residence_type_by_age.py`)

**Description:** Provides Census 2021 information classifying usual residents by residence type (household or communal establishment resident) and by age.

**Usage:**

```bash
python fetch_residence_type_by_age.py
```

**Output:** `extract_YYYYMMDD_HHMMSS/residence_type_by_age_data.csv`

**Key Features:**

- Census 2021 snapshot data
- Coverage: All 331 Lower Tier Local Authorities in England and Wales
- Cross-tabulation of residence type (household vs communal establishment) by 6 age categories
- Direct CSV download (not observations API)
- 3,972 records covering all combinations of geography, age, and residence type
- Helps understand household composition and care facility needs by age group

**Note:** This script uses direct CSV download as it's Census 2021 data, which is provided as pre-computed tables rather than through the observations API.

---

### 4. Tenure (`fetch_tenure.py`)

**Description:** Census 2021 housing tenure data showing how households occupy their accommodation (owned outright, owned with mortgage, rented from local authority, private rented, etc.).


**Usage:**
```bash
python fetch_tenure.py
```

**Output:** `extract_YYYYMMDD_HHMMSS/tenure_data.csv`

**Key Features:**

- Census 2021 snapshot data
- Coverage: All 331 Lower Tier Local Authorities in England and Wales
- Breakdown by 9 tenure categories (owned outright, mortgage, shared ownership, social/council rented, private rented, rent free)
- Direct CSV download (not observations API)
- 2,979 records covering all combinations of geography and tenure type
- Critical for understanding housing accessibility and affordability

**Note:** This script uses direct CSV download as it's Census 2021 data, which is provided as pre-computed tables rather than through the observations API.

---

## Common Features

**Census 2021 Datasets** (Population Density, Residence Type by Age, Tenure):
- Use direct CSV download from pre-computed Census tables
- Provide snapshot data from Census Day (21 March 2021)
- Cover all 331 Lower Tier Local Authorities in England and Wales
- No time series available (single point in time)

**Time Series Datasets** (Rental Prices):
- Use the observations API endpoint
- Provide historical time series data
- Support multiple geographic breakdowns

All scripts share these characteristics:

1. **Automatic Dataset Discovery:** Each script searches the ONS API for the relevant dataset by name
2. **Dimension Handling:** Automatically fetches all available dimensions and their options
3. **Smart Defaults:** Uses wildcards (*) for time dimensions to get full time series
4. **Extract Directories:** Creates timestamped extract directories to organize outputs
5. **Comprehensive Logging:** Provides detailed console output showing progress and any issues
6. **Error Handling:** Gracefully handles API errors and missing datasets

## Requirements

All scripts require the following Python packages (install via `pip install -r ../requirements.txt`):
- requests
- pandas
- logging (built-in)
- pathlib (built-in)

## Data Output Format

Each script produces CSV files with:
- An `observation` column containing the measured value
- Dimension columns (e.g., `time`, `geography`, `tenure_type`, `age_group`)
- Flat, denormalized structure ready for analysis

## Troubleshooting

### Dataset Not Found

If a script reports that it cannot find a dataset:
1. Check the ONS API is accessible
2. Run the parent directory's `list_datasets.py` to see all available datasets
3. The dataset name may have changed - check the ONS website
4. Some scripts have fallback search terms built in

### No Observations Returned

If a script finds the dataset but returns no observations:
1. Check the dimension combinations being requested
2. Some datasets may have limited time series or geographic coverage
3. Review the console output to see which dimension values are being used
4. Modify the script to adjust dimension selection if needed

## Integration with Main Project

These housing scripts are part of the UK Socio-Economic Modelling project and can be integrated with:
- Housing pressure models (`apps/housing_pressure/`)
- Economic indicators (`data_sources/economic_indicators.py`)
- Population models (`data_sources/population/`)
- Visualization dashboards

## Further Documentation

For more information on the ONS API and available datasets:
- [ONS API Documentation](https://developer.ons.gov.uk/)
- [ONS API Blog Post](https://digitalblog.ons.gov.uk/2021/07/09/exploring-the-census-api/)
- Parent directory README: `../README.md`

## Contributing

When adding new housing data sources:
1. Follow the existing script patterns
2. Include comprehensive docstrings
3. Add appropriate logging
4. Update this README with the new data source
5. Test the script to ensure it successfully retrieves data

---

*Last updated: December 2025*
