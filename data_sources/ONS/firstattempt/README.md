# First Attempt Snapshot (ONS Identity Extracts)

This folder contains a snapshot of the initial implementation for pulling identity-related splits from ONS datasets:

- `build_population_identity_model.py` — combined builder to aggregate multiple identity splits.
- `identity_utils.py` — shared utilities for dataset selection, dimension queries, and labelling.
- `identity_extract.py` — CLI to pull each domain separately (religion, ethnicity, sexual orientation, heritage origin) with options for national vs detailed datasets and geography overrides.
- `fetch_ons_data.py` — helper utilities to list dimensions and pull observations.
- `list_datasets.py` — generator for `ons_datasets.csv`.

Use this folder as a reference while researching dataset availability and geography coverage.
