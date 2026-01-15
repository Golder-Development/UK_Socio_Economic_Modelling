# Deduplication Analysis: UK Socio-Economic Modelling vs Dashboard Demo

**Date**: January 15, 2026
**Status**: Cross-repository review for effort deduplication

## Executive Summary

Review of recent parliament/MP work against dashboard_demo_readonly reveals **significant potential for deduplication**. While the projects have different primary purposes (donations analysis vs socio-economic modeling), both consume UK Parliament data and perform related transformations. Key opportunities exist to **eliminate duplicate code** while maintaining project independence.

---

## 1. Data Sources Comparison

### UK Socio-Economic Modelling

**Primary Data Source**: pdpy (UK Parliament API)

**Data Extracted**:
```
✓ Cabinet Ministers      (3,745 records, via pdpy)
✓ MPs                   (from pdpy.fetch_mps)
✓ Lords                 (from pdpy.fetch_lords_government_roles)
✓ Parliament Periods    (23 parliaments, 1945-2026)
✓ Party Memberships     (via pdpy.fetch_mps_party_memberships)
```

**Storage Locations**:
- `data_sources/parliament/most recent extract/` - current extracts
- `data_sources/parliament/most recent output/` - processed outputs
- `data_sources/parliament/extract_*` - timestamped archives (3 recent)

**Recent Code Files**:
- `cabinet_ministers.py` (390 lines) - Main extraction script
- `mps.py` (58 lines) - MP data extraction
- `lords.py` - Lords data extraction
- `party_membership.py` - Party membership data
- `parliaments.py` (55 lines) - Parliament periods
- `create_tenure_visualization.py` - Interactive Plotly visualization
- `build_sos_churn_by_parliament.py` - SoS analysis script

---

### Dashboard Demo

**Primary Data Source**: Political donations (Electoral Commission API) + static MP/Party reference data

**Data Available**:
```
✓ Donations Data        (cleaned, 2+ million records)
✓ Donor Lists          (cleaned, deduplicated)
✓ Regulated Entities   (cleaned)
✓ Parliamentary Sitting Reference (by donation period)
✓ Party Group Data
✓ Party Switcher Donors (analysis output)
✓ Donor Timeline Analysis (output)
✓ Party Diversity Data (output)
```

**Storage Locations**:
- `data_sources/dashboard_demo_readonly/output/` - processed data/charts
- `data_sources/dashboard_demo_readonly/data/` - data loading utilities
- `data_sources/dashboard_demo_readonly/source/` - political donations CSVs

**Key Utilities**:
- `data_file_defs.py` - Data loading schemas
- `clean_and_enhance.py` - Data cleaning pipelines
- `data_dedupe.py` - Deduplication logic
- `data_loader.py` - Streamlit data caching
- `politicalperson.py` - Person object model

---

## 2. Code Overlap Analysis

### **HIGH OVERLAP**: Parliament Periods Reference

**Current State** (UK Socio-Economic Modelling):
```python
# data_sources/parliament/parliaments.py
def get_parliament_periods() -> pd.DataFrame:
    client = get_client()
    data = client.get_parliaments()
    df = pd.DataFrame(data)
    return df[["parliament_number", "start_date", "end_date"]]
```

**Outputs**: `data_sources/parliament/most recent output/parliaments_periods.json` (23 records)

**Used By Dashboard Demo**: 
- Implicitly in donation analysis via `parliamentary_sitting` column
- Stored in donations data but not as dedicated reference dataset

**Deduplication Opportunity**: ⭐⭐⭐ HIGH
- Parliament periods are generated dynamically but could be cached and reused
- Create single source of truth in `dashboard_demo_readonly/output/parliament_reference.csv`
- Both projects reference via consistent columns: `parliament_number`, `start_date`, `end_date`

**Action**: Instead of regenerating parliament periods in cabinet_ministers.py, import from dashboard_demo_readonly if available, fall back to API call if not.

---

### **MEDIUM OVERLAP**: Party Classification Logic

**Current State** (UK Socio-Economic Modelling):
```python
# data_sources/parliament/cabinet_ministers.py (lines ~58-71)
get_government_timeline() with hardcoded party mappings:
- "Conservative", "Labour", "Liberal Democrat", "Coalition", etc.
```

**Current State** (Dashboard Demo):
```python
# data_sources/dashboard_demo_readonly/data/clean_and_enhance.py
- Party classification from Electoral Commission "Party_Group"
- Party switcher donor analysis
- Party exception handling
```

**Deduplication Opportunity**: ⭐⭐ MEDIUM
- Party classification logic could be centralized
- Dashboard demo has more sophisticated party grouping (Party_Group mapping)
- Create `dashboard_demo_readonly/utils/party_utils.py` with shared party mappings
- Cabinet ministers script currently uses simple hardcoded lookup

**Action**: Extract party classification to shared utility, reference from both projects.

---

### **MEDIUM OVERLAP**: Data Deduplication Patterns

**Current State** (Dashboard Demo):
```python
# data_sources/dashboard_demo_readonly/data/data_dedupe.py
Comprehensive deduplication logic for:
- Donor name normalization
- Entity name normalization
- Address standardization
- Company registration matching
```

**Current State** (UK Socio-Economic Modelling):
- Manual deduplication in cabinet_ministers.py (find_prime_minister logic)
- Simple direct matching without sophisticated normalization

**Deduplication Opportunity**: ⭐⭐ MEDIUM
- Cabinet ministers data would benefit from donor-style deduplication
- Could adapt dashboard_demo deduplication patterns for MP/minister names
- Standardized deduplication would improve data quality

**Action**: Review and potentially adopt dashboard_demo deduplication patterns for minister data cleaning.

---

### **MEDIUM OVERLAP**: Data Schema & Type Conversion

**Current State** (Dashboard Demo):
```python
# data_sources/dashboard_demo_readonly/data/data_file_defs.py (218 lines)
Detailed data type schemas for all donations fields:
- ECRef, RegulatedEntityName, Value (float), AcceptedDate, etc.
- Schema-driven data loading with type validation
```

**Current State** (UK Socio-Economic Modelling):
```python
# Simple inline type conversion
df["start_date"] = pd.to_datetime(df["start_date"])
df["end_date"] = pd.to_datetime(df["end_date"])
```

**Deduplication Opportunity**: ⭐ LOW (Context-specific)
- Donation schemas not directly applicable to parliament data
- Different data structures warrant different schemas
- Low benefit to unification

**Action**: Keep separate; note as "intentional divergence"

---

## 3. Output Data Analysis

### Datasets Generated

| Dataset | Location | Size | Used By | Dedup Potential |
|---------|----------|------|---------|-----------------|
| **Parliament Periods** | `parliament/most recent output/parliaments_periods.json` | 23 rows | Cabinet ministers, tenure viz | ⭐⭐⭐ HIGH |
| **Cabinet Ministers** | `parliament/most recent extract/cabinet_ministers.csv` | 3,745 rows | Internal (tenure analysis) | ⭐ LOW |
| **Parliamentary Churn Summary** | `parliament/most recent output/parliamentary_churn_summary.csv` | 23 rows | SoS analysis | ⭐ LOW |
| **SoS Churn Visualization** | `parliament/most recent output/sos_churn_bar.jpg` | 131 KB | Internal (reference) | ⭐ LOW |
| **Tenure Visualization** | `generated_charts/*.html` | ~6 MB | Internal (Plotly) | ⭐ LOW |
| **Cleaned Donations** | `dashboard_demo_readonly/output/cleaned_donations.csv` | Large | Dashboard | ✓ Already shared |
| **Donor Lists** | `dashboard_demo_readonly/output/cleaned_donorlist.csv` | Large | Dashboard | ✓ Already shared |
| **Parliamentary Sitting Donations** | `dashboard_demo_readonly/output/` | Via parliamentary_sitting | Dashboard | ⭐ PARTIAL |

---

## 4. Code Patterns & Utilities

### Shared Patterns Found

| Pattern | Location (USEM) | Location (Dashboard) | Status |
|---------|-----------------|----------------------|--------|
| **Data Loading Caching** | In progress | `data_loader.py` + Streamlit | ⭐ ADOPT |
| **Parliament Period Lookup** | `parliaments.py` | Implicit in data | ⭐⭐⭐ CONSOLIDATE |
| **Date Type Conversion** | Inline | `data_file_defs.py` | ✓ Keep separate |
| **Party Classification** | Hardcoded dict | `clean_and_enhance.py` | ⭐⭐ EXTRACT |
| **Logging/Debugging** | Basic | `utils/logger.py` | ✓ USEM could adopt |
| **Error Handling** | Basic try/except | More comprehensive | ✓ Good reference |

---

## 5. Specific Recommendations

### **Priority 1: Parliament Periods Consolidation** (HIGH IMPACT)

**Current Duplication**:
- Parliament periods extracted via pdpy in `parliament/parliaments.py`
- Stored in `parliament/most recent output/parliaments_periods.json`
- Also implicitly in donation data via `parliamentary_sitting` field

**Recommended Action**:
```python
# NEW: data_sources/SHARED_PARLIAMENT_REFERENCE.csv
parliament_number, start_date, end_date, parliamentary_sitting
31, 1945-07-05, 1945-08-15, "31st Parliament"
...

# cabinet_ministers.py - CHANGE FROM:
from data_sources.parliament.parliaments import get_parliament_periods()
# CHANGE TO:
def get_parliament_periods():
    """Load parliament reference from shared source"""
    # Try dashboard_demo first
    shared_ref = Path("data_sources/dashboard_demo_readonly/output/parliament_reference.csv")
    if shared_ref.exists():
        return pd.read_csv(shared_ref)
    # Fallback to API
    return fetch_parliament_periods_from_pdpy()
```

**Benefits**:
- Single source of truth
- Faster load time (no API call)
- Consistent across both projects
- Reduces data extraction from pdpy

**Effort**: 2-3 hours

---

### **Priority 2: Party Classification Utility** (MEDIUM IMPACT)

**Current Duplication**:
- Cabinet ministers has hardcoded party list
- Dashboard has party grouping logic

**Recommended Action**:
```python
# NEW: data_sources/dashboard_demo_readonly/utils/party_reference.py
PARTY_MAPPING = {
    "Conservative": "Conservative",
    "Labour": "Labour",
    "Liberal Democrat": "Lib Dem",
    ...
}

PARTY_GROUPS = {
    "Left Wing": ["Labour", "Lib Dem"],
    "Right Wing": ["Conservative", ...],
    ...
}

# USAGE in cabinet_ministers.py:
from data_sources.dashboard_demo_readonly.utils.party_reference import PARTY_MAPPING
```

**Benefits**:
- Shared reference reduces maintenance
- Consistent party naming across projects
- Easier to update party groupings

**Effort**: 1-2 hours

---

### **Priority 3: Data Quality Utilities** (MEDIUM IMPACT)

**Current Issue**:
- Cabinet ministers data lacks sophisticated name normalization
- Dashboard demo has proven deduplication patterns

**Recommended Action**:
```python
# REFERENCE dashboard_demo_readonly/data/data_dedupe.py patterns
# Adapt name normalization for MPs/Ministers:
# - Normalize diacritics (é → e)
# - Handle name suffixes (Jr., Sr., III)
# - Standardize spacing/capitalization

# cabinet_ministers.py - ADD:
from data_sources.dashboard_demo_readonly.data.data_dedupe import (
    normalize_name, 
    normalize_text  # Adapt for names
)
```

**Benefits**:
- Better data quality for minister matching
- Proven deduplication logic
- Reduced manual intervention

**Effort**: 2-3 hours

---

### **Priority 4: Logging & Error Handling** (LOW IMPACT)

**Current Issue**:
- Parliament scripts use basic error handling
- Dashboard has sophisticated logging setup

**Recommended Action**:
```python
# REFERENCE dashboard_demo_readonly/utils/logger.py
# cabinet_ministers.py - ADD:
from data_sources.dashboard_demo_readonly.utils.logger import (
    logger,
    log_function_call  # Decorator
)

# Then use:
@log_function_call
def get_cabinet_ministers():
    logger.debug("Starting cabinet ministers extraction...")
    ...
```

**Benefits**:
- Better debugging visibility
- Consistent logging across projects
- Audit trail for data processing

**Effort**: 1-2 hours

---

## 6. Items NOT to Consolidate (Maintain Separation)

### ✓ Keep Separate: Core Analysis Logic

- **Cabinet Ministers Extraction** - Project-specific focus
- **Tenure Visualization** - Project-specific analysis
- **SoS Churn Analysis** - Project-specific modeling
- **Donations Data Processing** - Different sources/domains

### ✓ Keep Separate: Project Dependencies

- Dashboard demo uses Streamlit (requires running as app)
- USEM uses Jupyter notebooks and standalone scripts
- Different dependency requirements

### ✓ Keep Separate: Database Schemas

- Parliament data schema (parliament_number, MP ID, etc.)
- Donations data schema (donor, amount, party, etc.)
- Different data structures

---

## 7. Implementation Roadmap

### Phase 1: Quick Wins (Week 1)
- [ ] Create `SHARED_PARLIAMENT_REFERENCE.csv` in dashboard_demo_readonly/output
- [ ] Update `cabinet_ministers.py` to use shared parliament periods
- [ ] Document in DEVELOPER_REFERENCE.md

### Phase 2: Consolidation (Week 2)
- [ ] Extract party reference to `dashboard_demo_readonly/utils/party_reference.py`
- [ ] Update both projects to import party mappings
- [ ] Test backward compatibility

### Phase 3: Enhancement (Week 3)
- [ ] Review `data_dedupe.py` for name normalization patterns
- [ ] Adapt for MP/minister data
- [ ] Add to parliament data pipeline

### Phase 4: Polish (Week 4)
- [ ] Adopt dashboard_demo logging patterns
- [ ] Create shared utilities documentation
- [ ] Update DEVELOPER_REFERENCE.md with integration guide

---

## 8. Risk Assessment

| Action | Risk Level | Mitigation |
|--------|-----------|-----------|
| **Consolidate parliament periods** | ✓ LOW | Keep fallback to API call |
| **Share party reference** | ✓ LOW | Version-pin reference data |
| **Adapt deduplication logic** | ⭐ MEDIUM | Thorough testing on cabinet data |
| **Depend on dashboard_demo utilities** | ⭐⭐ MEDIUM-HIGH | Use explicit imports, clear documentation |

---

## 9. Dependencies & Order

```
Prerequisite: dashboard_demo_readonly properly initialized as submodule ✓

1. Parliament reference (standalone)
   ↓
2. Party reference (uses parliament reference)
   ↓
3. Deduplication utilities (uses party reference)
   ↓
4. Update cabinet_ministers.py (uses all above)
   ↓
5. Logging integration (final polish)
```

---

## 10. Success Metrics

### Before Deduplication
- Parliament periods: Extracted from API on every run (~5s latency)
- Party classification: Hardcoded in 2+ locations
- Name normalization: Manual, inconsistent
- Logging: Basic print statements

### After Deduplication
- Parliament periods: Loaded from CSV (<100ms), cached
- Party classification: Single source in dashboard_demo_readonly
- Name normalization: Consistent deduplication library
- Logging: Structured logging with audit trail
- Code reduction: ~200 lines eliminated from parliament module

---

## 11. Files to Modify/Create

### Create (New)
```
data_sources/dashboard_demo_readonly/output/parliament_reference.csv
data_sources/dashboard_demo_readonly/utils/party_reference.py
```

### Modify (Refactor)
```
data_sources/parliament/cabinet_ministers.py (consolidate parliament periods)
data_sources/parliament/parliaments.py (update with shared reference)
data_sources/parliament/create_tenure_visualization.py (optional: use shared parliament)
data_sources/parliament/build_sos_churn_by_parliament.py (optional: use shared parliament)
```

### Reference (No changes to dashboard_demo_readonly)
```
data_sources/dashboard_demo_readonly/data/data_dedupe.py (study/adapt)
data_sources/dashboard_demo_readonly/data/clean_and_enhance.py (reference patterns)
data_sources/dashboard_demo_readonly/utils/logger.py (reference implementation)
```

---

## 12. Notes

- **No modifications to dashboard_demo_readonly**: All changes maintain one-way dependency (USEM imports FROM dashboard_demo, not vice versa)
- **Backward compatibility**: All changes use fallback patterns to maintain independence
- **Minimal disruption**: Changes are additive, existing code continues to work
- **Clear documentation**: All shared resources documented for team

---

## Appendix: File Statistics

### UK Socio-Economic Modelling Parliament Module
```
Total Python files: ~100 (parliament-related: ~8)
Recent parliament work: cabinet_ministers.py (390 lines)
                       build_sos_churn_by_parliament.py (~150 lines)
                       create_tenure_visualization.py (~200 lines)
                       parliaments.py (55 lines)
                       mps.py (58 lines)
                       party_membership.py (~60 lines)
Total parliament code: ~915 lines
```

### Dashboard Demo
```
Total Python files: ~40-50
Data utilities: data/*.py (~800 lines)
Visualization: Visualisations/*.py (~300 lines)
Utilities: utils/*.py (~200 lines)
Main app: politicalpartyanalysis.py (~50 lines)
Total: ~1500 lines (donations-focused)
```

---

**End of Analysis**
**Review Status**: Ready for discussion and prioritization
**Next Step**: Prioritize actions, assign owners, create tickets
