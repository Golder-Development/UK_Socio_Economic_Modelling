# Quick Reference - Secretary of State Churn Script

## 📊 What This Script Does

Analyzes Secretary of State appointments and turnover across UK Parliaments (1945-2026), generating:

- Summary statistics by parliament
- Churn rate analysis (appointments per year)
- Visualization comparing tenures to parliament duration

## 🚀 How to Run

```bash
# From workspace root:
python visuals/build_sos_churn_by_parliament.py
```

**Execution Time**:

- First run: ~5 seconds (fetches parliament data from API)
- Subsequent runs: <1 second (loads from cache)

## 📍 File Locations

| Purpose              | Path                                                                         |
| -------------------- | ---------------------------------------------------------------------------- |
| **Script**           | `visuals/build_sos_churn_by_parliament.py`                                   |
| **Input Data**       | `data_sources/parliament/most recent extract/cabinet_ministers.csv`          |
| **Output Folder**    | `data_sources/parliament/most recent output/`                                |
| **Parliament Cache** | `data_sources/parliament/most recent output/parliaments_periods.json`        |
| **Summary CSV**      | `data_sources/parliament/most recent output/parliamentary_churn_summary.csv` |
| **Chart**            | `data_sources/parliament/most recent output/sos_churn_bar.png`               |

## 📋 Generated Outputs

### 1. `parliamentary_churn_summary.csv`

One row per parliament with:

- Parliament number & dates
- Count of distinct Secretaries of State
- Tenure statistics (median, min, max days)
- **Churn rate** (appointments per year) ← Key metric
- Media era classification

**Rows**: 5 parliaments (55th-59th, 2010-2026)

### 2. `parliaments_periods.json` (CACHED)

Parliament session dates and durations - cached locally to avoid repeated API calls.

**Used by**: Other analysis scripts
**Update**: Automatic (re-fetched only when manually deleted)

### 3. `sos_churn_bar.png`

Bar chart showing SoS churn by parliament with media era annotations (radio, TV, rolling news, social media).

## 🔄 Data Flow

```
Cabinet Ministers Dataset
    ↓
Filter: Secretary of State posts only
    ↓
Match: Appointments to Parliament sessions
    ↓
Calculate: Tenure lengths & churn rates
    ↓
Generate: Summary statistics & visualization
    ↓
Output: CSV + PNG + Cached JSON
```

## 💡 Using Outputs in Other Scripts

### Load Parliament Cache (NO API CALL NEEDED)

```python
from pathlib import Path
import json
import pandas as pd

cache = Path("data_sources/parliament/most recent output/parliaments_periods.json")
with open(cache, "r") as f:
    parls = pd.DataFrame(json.load(f))
    parls["parliament_start_date"] = pd.to_datetime(parls["parliament_start_date"])
    parls["parliament_end_date"] = pd.to_datetime(parls["parliament_end_date"])
```

### Load Churn Summary

```python
churn = pd.read_csv("data_sources/parliament/most recent output/parliamentary_churn_summary.csv")
print(churn[["parliament_number", "appointments_per_year", "num_secretaries_of_state"]])
```

## 🔧 Key Updates Made

| Issue                | Solution                        | Benefit                  |
| -------------------- | ------------------------------- | ------------------------ |
| Hardcoded data paths | Auto-detect most recent extract | No manual updates needed |
| Scattered outputs    | Centralized to one folder       | Easy to find & use       |
| Repeated API calls   | Local JSON cache                | 5x faster on repeat runs |
| Rigid API parsing    | Flexible column matching        | Future-proof             |

## 📊 Sample Data

**Recent Parliament (59th - July 2024 to present)**

- Distinct Secretaries of State: 26
- Appointments per year: 17.1
- Median tenure: 426 days (~14 months)
- Shortest appointment: 1 day
- Longest appointment: 556 days (~18 months)

## ⚙️ Technical Details

**Dependencies**: pandas, matplotlib, requests, pathlib, json

**Data Source**:

- Cabinet ministers from `pdpy` Parliament API
- Parliament periods from Parliament elections endpoint

**Parliament Periods Covered**:

- 55th Parliament: 2010-2015 (Coalition)
- 56th Parliament: 2015-2017 (Conservative)
- 57th Parliament: 2017-2019 (Conservative)
- 58th Parliament: 2019-2024 (Conservative)
- 59th Parliament: 2024-present (Labour)

## 🆘 Troubleshooting

**"File not found" error**
→ Ensure `most recent extract/cabinet_ministers.csv` exists

**Cache not updating**
→ Delete `parliaments_periods.json` to force API re-fetch on next run

**API connection issues**
→ Cached data from previous run will still work

## 📞 For More Information

See:

- `data_sources/parliament/most recent output/README.md` - Full documentation
- `SCRIPT_UPDATE_SUMMARY.md` - Change details
- `data_sources/parliament/VALIDATION_REPORT.md` - Test results

---

**Last Updated**: January 15, 2026
**Script Version**: Updated for "most recent" data architecture
**Status**: ✅ Tested & Working
