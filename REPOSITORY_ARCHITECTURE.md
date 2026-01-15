# Repository Architecture & References

## Projects Overview

This workspace contains the **UK Socio-Economic Modelling** project with a focus on government cabinet minister analysis and turnover patterns.

### Related External Repository

**[dashboard_demo](https://github.com/Golder-Development/dashboard_demo)** (Separate Repository)

- Broader parliamentary analysis
- Member of Parliament data structures
- Parliament session utilities
- Visualization frameworks

---

## Data Architecture

### This Project: UK Socio-Economic Modelling

**Focus**: Government cabinet ministers, tenure analysis, and turnover metrics

**Key Components**:

```
data_sources/parliament/
├── cabinet_ministers.py          → Extract cabinet minister data
├── create_tenure_visualization.py → Visualize tenure patterns
├── build_sos_churn_by_parliament.py → Analyze SoS turnover
├── most recent extract/          → Cabinet ministers CSV (latest)
├── most recent output/           → Analysis outputs (CSV, JPG, JSON)
└── parliaments_periods.json      → Cached parliament dates
```

**Data Source**: UK Parliament API via `pdpy` package
**Output**: Government turnover metrics, visualizations, cached parliament data

### Related Project: dashboard_demo

**Focus**: Broader parliamentary analysis (all members, not just government)

**Scope**:

- All MPs and Lords members
- Broader activity analysis
- Dashboard visualizations
- Member lookup utilities

---

## Data Independence

Both projects maintain **separate data extracts** because:

1. **Different Scopes**

   - This project: Government roles only (~3,700 records)
   - dashboard_demo: All members (~2,500+ MPs/Lords)

2. **Different Update Cycles**

   - This project: Government updates drive regeneration
   - dashboard_demo: Broader parliamentary changes drive updates

3. **Different Caching**

   - This project: Caches parliament periods locally
   - dashboard_demo: May have different cache strategies

4. **Different Processing**
   - This project: Government-specific aggregations
   - dashboard_demo: Broader member aggregations

### When to Sync

- **Parliament periods data** - If structure changes, update both
- **Member ID standards** - If Parliament API changes IDs, both need updates
- **Base data structures** - Major improvements could benefit both

---

## Shared Data Elements

### Parliament Periods

**Used by both projects**: Parliament session start/end dates

**This project location**:

```
data_sources/parliament/most recent output/parliaments_periods.json
```

**Structure**:

```json
[
  {
    "parliament_number": 59,
    "parliament_start_date": "2024-07-09",
    "parliament_end_date": "2026-01-15",
    "parliament_duration_days": 556
  }
]
```

### Member IDs

**Used by both projects**: Parliament member identifiers

**Fields**:

- `person_id` - Internal Parliament identifier
- `mnis_id` - UK Parliament MNIS ID
- `member_house` - Commons or Lords

---

## Integration Guidelines

### DO

✅ Reference structures and patterns from dashboard_demo  
✅ Copy useful utility functions when needed  
✅ Document the source when copying code  
✅ Maintain separate data extracts  
✅ Coordinate on shared data changes

### DON'T

❌ Create hard dependencies between projects  
❌ Import directly from dashboard_demo  
❌ Share mutable state  
❌ Assume identical data structures  
❌ Break independence through tight coupling

### Example: Referencing Code

Instead of:

```python
from dashboard_demo.parliament import get_parliaments
```

Do this:

```python
# Copied from dashboard_demo.parliament (2026-01-15)
# Original: https://github.com/Golder-Development/dashboard_demo/src/parliament.py
def get_parliaments():
    # Implementation...
```

---

## Working with Both Projects

### Install Both Locally

```bash
# This project
git clone <this-repo> UK_Socio_Economic_Modelling
cd UK_Socio_Economic_Modelling

# Related project (separate directory)
git clone https://github.com/Golder-Development/dashboard_demo
```

### Data Flow

```
UK Parliament API (pdpy)
    ├─→ This Project: Cabinet Ministers Extract
    │   └─→ most recent output/ (government analysis)
    │
    └─→ dashboard_demo: Member Data Extract
        └─→ visualizations/ (broader analysis)
```

### Coordination Points

1. **Parliament periods changes** - Update both caches if structure changes
2. **Member ID updates** - Check both projects if API changes
3. **Data quality improvements** - Document and potentially backport to both
4. **Visualization patterns** - Reference each other for approaches

---

## Documentation Files

### This Project

- `data_sources/parliament/README.md` - Parliament data overview (pdpy basics)
- `data_sources/parliament/RELATED_REPOSITORIES.md` - Detailed relationship docs
- `data_sources/parliament/QUICK_REFERENCE.md` - Quick start guide
- `data_sources/parliament/most recent output/README.md` - Output file docs

### Related Project

See [dashboard_demo](https://github.com/Golder-Development/dashboard_demo) repository directly

---

## Maintenance Checklist

### Regular (Monthly/Quarterly)

- [ ] Run `cabinet_ministers.py` to get latest government data
- [ ] Run `build_sos_churn_by_parliament.py` for updated analysis
- [ ] Check Parliament API for breaking changes

### When Updating Parliament Data

- [ ] Update `parliaments_periods.json` in this project
- [ ] Note if parliament dates changed
- [ ] Check if dashboard_demo needs updating
- [ ] Document the changes

### Coordinating Changes

- [ ] Document improvements in both projects (if applicable)
- [ ] Note which project leads on specific data types
- [ ] Keep separate data extracts in sync conceptually
- [ ] Communicate major changes between repos

---

## Quick Links

**This Project**:

- Cabinet Ministers: `data_sources/parliament/most recent extract/cabinet_ministers.csv`
- Analysis Outputs: `data_sources/parliament/most recent output/`
- Visualization: `create_tenure_visualization.py`
- Churn Analysis: `build_sos_churn_by_parliament.py`

**Related Project**:

- Repository: https://github.com/Golder-Development/dashboard_demo
- Check repo for current documentation
- Reference for parliament utilities and member structures

---

**Last Updated**: January 15, 2026  
**Status**: Active (separate but coordinated projects)
