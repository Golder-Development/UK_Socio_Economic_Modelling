# Developer Quick Reference - Dual Repository Setup

## The Two Projects

### 1. UK Socio-Economic Modelling (This Project)

**Purpose**: Cabinet ministers analysis & government turnover metrics  
**Repository**: Local (this workspace)  
**Data Focus**: Government roles only  
**Key Output**: Minister tenure analysis, SoS churn rates

### 2. Dashboard Demo (Related Project)

**Purpose**: Broader parliamentary analysis  
**Repository**: https://github.com/Golder-Development/dashboard_demo  
**Data Focus**: All MPs and Lords  
**Key Output**: Member activity dashboards

---

## Working with Both (Quick Reference)

### Setup (One-Time)

```bash
# Clone this project
git clone <this-repo> UK_Socio_Economic_Modelling
cd UK_Socio_Economic_Modelling

# For reference, clone dashboard_demo elsewhere
cd ..
git clone https://github.com/Golder-Development/dashboard_demo
```

### Daily Workflow

```bash
# Work in this project
cd UK_Socio_Economic_Modelling

# Run cabinet minister analysis
python data_sources/parliament/cabinet_ministers.py

# Generate visualizations
python data_sources/parliament/create_tenure_visualization.py

# Analyze SoS turnover
python visuals/build_sos_churn_by_parliament.py

# Check outputs
ls data_sources/parliament/most recent output/
```

---

## Shared Data Reference

### Parliament Periods

Location (this project):

```
data_sources/parliament/most recent output/parliaments_periods.json
```

When to check dashboard_demo:

- Parliament session definitions differ?
- Need broader parliamentary timeline?
- Want example of parliament utilities?

### Member Data

This project uses:

- `person_id` (Parliament API ID)
- `mnis_id` (UK Parliament MNIS ID)

dashboard_demo may have:

- Extended member records
- Additional member fields
- Member lookup utilities

---

## Code Reuse Guide

### Pattern 1: Copy Function

```python
# If you find useful code in dashboard_demo:

# ❌ DON'T: Hard import
from dashboard_demo.parliament import get_parliaments

# ✅ DO: Copy and document
def get_parliaments():
    """
    Parliament period retrieval

    Based on dashboard_demo.parliament.get_parliaments
    Source: https://github.com/Golder-Development/dashboard_demo
    Copied: 2026-01-15
    """
    # Your implementation...
```

### Pattern 2: Reference Approach

```python
# If dashboard_demo has a good pattern:

# ❌ DON'T: Try to import shared code
import dashboard_demo.utils

# ✅ DO: Document the pattern
# This implementation mirrors dashboard_demo's approach to...
# See: https://github.com/Golder-Development/dashboard_demo/blob/main/src/utils.py
```

---

## Data Exchange Between Projects

### Sharing Parliament Data

If parliament dates changed:

**Step 1**: Update this project

```bash
cd UK_Socio_Economic_Modelling
rm data_sources/parliament/most recent output/parliaments_periods.json
python visuals/build_sos_churn_by_parliament.py  # Re-fetches from API
```

**Step 2**: Check if dashboard_demo needs update

- Look in its documentation for parliament data location
- If it has similar caching, might need update too
- Note the change for future syncs

### Syncing Member IDs

If Parliament API changes ID formats:

1. Update `cabinet_ministers.py` in this project
2. Check dashboard_demo's member handling
3. Document the API change in both repos

---

## File Locations to Remember

**This Project - Key Files**:

```
cabinet_ministers.csv        → data_sources/parliament/most recent extract/
parliamentary_churn_summary.csv → data_sources/parliament/most recent output/
parliaments_periods.json     → data_sources/parliament/most recent output/
sos_churn_bar.jpg           → data_sources/parliament/most recent output/
```

**Related Project**:

```
Check github.com/Golder-Development/dashboard_demo for:
- Member data locations
- Parliament utilities
- Visualization examples
```

---

## Troubleshooting

### Parliament Data Issues

**Problem**: Parliament dates seem wrong  
**Check**: `data_sources/parliament/most recent output/parliaments_periods.json`  
**Fix**: Delete and re-run `build_sos_churn_by_parliament.py`  
**Reference**: See dashboard_demo if dates should be different

### Member ID Mismatches

**Problem**: Some person_ids don't exist  
**Check**: Parliament API response format  
**Compare**: dashboard_demo's member ID handling  
**Action**: Update ID extraction in `cabinet_ministers.py`

### Missing Data

**Problem**: Some records missing from cabinet_ministers.csv  
**Check**: pdpy library filters and options  
**Reference**: pdpy documentation and examples  
**Coordinate**: Check if dashboard_demo has similar issues

---

## Documentation Map

### This Project (Local)

| File                                                 | Purpose                       |
| ---------------------------------------------------- | ----------------------------- |
| REPOSITORY_ARCHITECTURE.md                           | (You are here) Overall setup  |
| data_sources/parliament/README.md                    | pdpy basics & setup           |
| data_sources/parliament/RELATED_REPOSITORIES.md      | Detailed project relationship |
| data_sources/parliament/QUICK_REFERENCE.md           | Running the scripts           |
| data_sources/parliament/most recent output/README.md | Understanding outputs         |

### Related Project (External)

Check: https://github.com/Golder-Development/dashboard_demo

- Architecture documentation
- Member data structures
- Utility functions
- Visualization patterns

---

## Communication Points

### When to Ask Questions

**About THIS project's code/data**:

- Cabinet minister extraction
- Government role analysis
- Tenure calculations
- SoS churn metrics

**About DASHBOARD_DEMO**:

- Member data structures
- Broader parliamentary analysis
- Dashboard development
- Member lookup patterns

### Making Changes

**Change only THIS project's code**:

- Cabinet minister processing
- Visualization generation
- Output formatting

**Check dashboard_demo before changing**:

- Parliament period definitions
- Member ID handling
- Shared data structure expectations

---

## One-Line Commands

```bash
# Run full pipeline (this project)
cd UK_Socio_Economic_Modelling && python data_sources/parliament/cabinet_ministers.py && python visuals/build_sos_churn_by_parliament.py && python data_sources/parliament/create_tenure_visualization.py

# Check outputs
ls -lah data_sources/parliament/most recent output/

# View parliament data
cat data_sources/parliament/most recent output/parliaments_periods.json | python -m json.tool | head -30

# Check cabinet ministers count
wc -l data_sources/parliament/most recent extract/cabinet_ministers.csv
```

---

**Status**: Ready to use  
**Last Updated**: January 15, 2026  
**Maintainer Note**: Keep projects independent but document shared patterns
