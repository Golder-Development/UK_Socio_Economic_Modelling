# Script Updates - Secretary of State Churn Analysis

## Summary of Changes

### Updated Script: `visuals/build_sos_churn_by_parliament.py`

#### 1. **Data Source Configuration (Most Recent Extract)**

- Changed from hardcoded timestamped path to automatic detection of "most recent extract"
- Script now checks `data_sources/parliament/most recent extract/` first
- Falls back to timestamped extract if needed
- **Benefit**: No manual path updates needed when new data is generated

```python
# Old:
INPUT_CSV = Path("data_sources/parliament/extract_20260115_125959/cabinet_ministers.csv")

# New:
EXTRACT_BASE_DIR = Path("data_sources/parliament/most recent extract")
if EXTRACT_BASE_DIR.exists():
    INPUT_CSV = EXTRACT_BASE_DIR / "cabinet_ministers.csv"
else:
    INPUT_CSV = Path("data_sources/parliament/extract_20260115_125959/cabinet_ministers.csv")
```

#### 2. **Output Directory Structure**

- Changed output location from `data/` and `outputs/` to `data_sources/parliament/most recent output/`
- Centralizes all parliament-related outputs in one location
- Easier for other scripts to reference and find outputs

```python
# Old:
DATA_DIR = Path("data")
OUTPUT_DIR = Path("outputs")

# New:
OUTPUT_DIR = Path("data_sources/parliament/most recent output")
```

#### 3. **Parliament Periods Caching (NEW)**

- Implemented local JSON cache for parliament periods data
- Fetches from Parliament API only once, then caches locally
- Subsequent runs load from cache (much faster, no API calls)
- **File**: `data_sources/parliament/most recent output/parliaments_periods.json`

```python
# New feature:
PARLIAMENTS_CACHE = OUTPUT_DIR / "parliaments_periods.json"

def fetch_parliament_periods() -> pd.DataFrame:
    if PARLIAMENTS_CACHE.exists():
        # Load cached data
    else:
        # Fetch from API and cache
```

#### 4. **HTML Table Column Mapping Fix**

- Updated to handle parliament periods table column naming variations
- Now handles both old and new Parliament API response formats:
  - `start_date` / `summoned_on`
  - `end_date` / `dissolved_on`
- More robust for future API changes

#### 5. **Improved Console Output**

- Added informative logging showing which files are being loaded
- Better status messages for caching operations
- Summary statistics with ✓ checkmarks

---

## New File Locations

### Generated Outputs

```
data_sources/parliament/most recent output/
├── parliamentary_churn_summary.csv      (SoS churn statistics by parliament)
├── parliaments_periods.json             (cached parliament periods data)
├── sos_churn_bar.png                    (visualization)
└── README.md                            (documentation)
```

### Shared Data Source

```
data_sources/parliament/most recent extract/
└── cabinet_ministers.csv                (points to latest extract via symlink)
```

---

## Benefits of These Changes

1. **Reduced Data Redundancy**: Single copy of cabinet ministers data referenced by all scripts
2. **Faster Execution**: Parliament periods cached locally after first fetch
3. **Easier Maintenance**: No need to update file paths when new data is extracted
4. **Centralized Outputs**: All parliament-related outputs in one folder
5. **Better Documentation**: README.md explains how to use outputs in other scripts
6. **More Robust**: Handles API response variations

---

## How to Use Outputs in Other Scripts

### Example: Loading Parliament Periods Cache

```python
from pathlib import Path
import json
import pandas as pd

parls_cache = Path("data_sources/parliament/most recent output/parliaments_periods.json")
with open(parls_cache, "r") as f:
    parls = pd.DataFrame(json.load(f))
parls["parliament_start_date"] = pd.to_datetime(parls["parliament_start_date"])
parls["parliament_end_date"] = pd.to_datetime(parls["parliament_end_date"])
```

### Example: Loading Churn Summary

```python
import pandas as pd

churn_summary = pd.read_csv(
    "data_sources/parliament/most recent output/parliamentary_churn_summary.csv"
)
```

---

## Testing & Validation

✅ Script execution: **SUCCESS**
✅ Cabinet ministers loaded: 3,745 records
✅ Parliament periods fetched: 5 records (2010-2026)
✅ Parliament cache created: `parliaments_periods.json` (1 KB)
✅ Churn summary generated: 5 parliament rows
✅ Visualization created: `sos_churn_bar.png` (100 KB)

### Sample Output:

```
Loading cabinet ministers from: data_sources\parliament\most recent extract\cabinet_ministers.csv
Fetching parliament periods from API...
Caching parliament periods to: data_sources\parliament\most recent output\parliaments_periods.json

✓ Wrote: data_sources\parliament\most recent output\parliamentary_churn_summary.csv
✓ Wrote: data_sources\parliament\most recent output\sos_churn_bar.png

Rows (parliaments): 5
```

---

## Data Extraction Details

| Item                           | Value                      |
| ------------------------------ | -------------------------- |
| Cabinet Ministers CSV          | extract_20260115_125959    |
| Data Extract Date              | January 15, 2026           |
| Total Cabinet Minister Records | 3,745                      |
| Parliaments Analyzed           | 5 (55th-59th, 2010-2026)   |
| Most Recent Parliament         | 59th (July 2024 - Present) |

---

**Updated**: January 15, 2026
**Script File**: `visuals/build_sos_churn_by_parliament.py`
