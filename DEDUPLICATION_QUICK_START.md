# Quick-Start Deduplication Implementation Guide

**Status**: Ready for implementation
**Priority**: Start with Parliament Reference consolidation (HIGH IMPACT, LOW RISK)

---

## Quick Summary

**Biggest Win**: Parliament periods are extracted dynamically every time but could be shared.

**What to Do First**:
1. ✅ Create `parliament_reference.csv` in dashboard_demo_readonly/output
2. ✅ Update `cabinet_ministers.py` to load from shared reference
3. ✅ Update `parliaments.py` to save to shared location
4. ✅ Document in DEVELOPER_REFERENCE.md

**Expected Benefit**: Eliminates API call for parliament data, creates single source of truth

---

## Step 1: Create Shared Parliament Reference

### Option A: From Existing Data (Fastest - 5 minutes)

Use the parliament periods already generated:

```bash
# Copy existing generated parliament reference
cp data_sources/parliament/most\ recent\ output/parliaments_periods.json \
   data_sources/dashboard_demo_readonly/output/parliament_reference.json

# OR convert JSON to CSV (more universal):
# Run Python snippet below
```

### Option B: Generate Fresh (Recommended - 10 minutes)

```python
# Create data_sources/generate_parliament_reference.py
import pandas as pd
from data_sources.parliament.parliaments import get_parliament_periods

def generate_parliament_reference():
    """Create shared parliament reference for both projects."""
    parliaments = get_parliament_periods()
    
    # Ensure consistent formatting
    parliaments['start_date'] = pd.to_datetime(parliaments['start_date'])
    parliaments['end_date'] = pd.to_datetime(parliaments['end_date'])
    
    # Save to shared location
    output_path = Path("data_sources/dashboard_demo_readonly/output/parliament_reference.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    parliaments.to_csv(output_path, index=False)
    
    print(f"✓ Parliament reference saved: {output_path}")
    print(f"  {len(parliaments)} parliament periods")
    return parliaments

if __name__ == "__main__":
    generate_parliament_reference()
```

### Result
```
data_sources/dashboard_demo_readonly/output/parliament_reference.csv
├── parliament_number
├── start_date
├── end_date
└── (23 rows, 1945-2026)
```

---

## Step 2: Update Cabinet Ministers Script

### Current Code (REMOVE)

```python
# data_sources/parliament/cabinet_ministers.py (currently lines ~160-180)

def get_parliaments_data():
    """Fetch parliament dates from pdpy API."""
    # Calls pdpy API directly
    ...
    return df
```

### New Code (ADD)

```python
# data_sources/parliament/cabinet_ministers.py

def get_parliament_periods():
    """
    Load parliament reference from shared source.
    
    Priority:
    1. Shared reference (dashboard_demo_readonly)
    2. Fallback to API call
    """
    from pathlib import Path
    
    shared_ref = Path(__file__).parent.parent / "dashboard_demo_readonly/output/parliament_reference.csv"
    
    if shared_ref.exists():
        print(f"✓ Loading parliament periods from shared reference: {shared_ref}")
        df = pd.read_csv(shared_ref)
        df['start_date'] = pd.to_datetime(df['start_date'])
        df['end_date'] = pd.to_datetime(df['end_date'])
        return df
    else:
        print("⚠ Shared parliament reference not found, fetching from API...")
        # Fallback to existing code
        from .parliaments import get_parliament_periods as api_get_parliaments
        return api_get_parliaments()
```

### Integration in Main Function

```python
# Update get_cabinet_ministers_datafile() to use new function:

# BEFORE:
parliaments_df = get_parliaments_data()  # Calls API

# AFTER:
parliaments_df = get_parliament_periods()  # Uses shared reference
```

---

## Step 3: Update Parliaments.py to Save to Shared Location

### Current Code

```python
# data_sources/parliament/parliaments.py

def main():
    parliaments_df = get_parliament_periods()
    extract_dir = _most_recent_extract_dir()
    output_file = extract_dir / "parliaments.csv"
    parliaments_df.to_csv(output_file, index=False)
```

### New Code (APPEND)

```python
# data_sources/parliament/parliaments.py

def save_parliament_reference(df):
    """Save parliament data to shared reference location."""
    from pathlib import Path
    
    # Also save to shared location for dashboard_demo_readonly
    shared_ref = Path(__file__).parent.parent / "dashboard_demo_readonly/output/parliament_reference.csv"
    shared_ref.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(shared_ref, index=False)
    print(f"✓ Parliament reference updated: {shared_ref}")

def main():
    """Demo: fetch and save Parliament periods data."""
    print("Fetching Parliament periods...")
    try:
        parliaments_df = get_parliament_periods()
        print(f"Retrieved {len(parliaments_df)} Parliament periods")
        
        if len(parliaments_df) > 0:
            # Save to timestamped extract
            extract_dir = _most_recent_extract_dir()
            output_file = extract_dir / "parliaments.csv"
            parliaments_df.to_csv(output_file, index=False)
            print(f"✓ Data saved to extract: {output_file}")
            
            # ALSO save to shared reference
            save_parliament_reference(parliaments_df)
    except Exception as e:
        print(f"Error: {e}")
```

---

## Step 4: Verify Integration

### Test Script

```python
# test_parliament_deduplication.py
import pandas as pd
from pathlib import Path
from data_sources.parliament.cabinet_ministers import get_parliament_periods

def test_shared_parliament_reference():
    """Test that parliament reference loads from shared location."""
    
    # Load parliament periods
    parliaments = get_parliament_periods()
    
    print(f"✓ Loaded {len(parliaments)} parliament periods")
    print(f"  Date range: {parliaments['start_date'].min()} to {parliaments['end_date'].max()}")
    
    # Verify columns
    required_cols = ['parliament_number', 'start_date', 'end_date']
    assert all(col in parliaments.columns for col in required_cols), "Missing required columns"
    print(f"✓ All required columns present: {required_cols}")
    
    # Verify shared reference exists
    shared_ref = Path("data_sources/dashboard_demo_readonly/output/parliament_reference.csv")
    assert shared_ref.exists(), f"Shared reference not found: {shared_ref}"
    print(f"✓ Shared reference exists: {shared_ref}")
    
    # Verify it matches
    shared_data = pd.read_csv(shared_ref)
    assert len(shared_data) == len(parliaments), "Parliament counts don't match"
    print(f"✓ Shared reference matches extracted data")
    
    print("\n✓✓✓ All tests passed!")

if __name__ == "__main__":
    test_shared_parliament_reference()
```

### Run Test

```bash
cd h:\VScode\UK_Socio_Economic_Modelling
python test_parliament_deduplication.py
```

---

## Step 5: Update Documentation

### Add to DEVELOPER_REFERENCE.md

```markdown
## Shared Data References

### Parliament Periods Reference
**Location**: `data_sources/dashboard_demo_readonly/output/parliament_reference.csv`

**Usage**: Both UK Socio-Economic Modelling and dashboard_demo use this shared reference to avoid duplicate API calls.

**Update Mechanism**:
1. Run `data_sources/parliament/parliaments.py` main()
2. Automatically saves to shared reference AND timestamped extract
3. Both projects load from shared reference with fallback to API

**Columns**:
- `parliament_number` (int): Parliament number (31-59)
- `start_date` (datetime): Start date of parliament
- `end_date` (datetime): End date of parliament

**Example Usage**:
```python
from data_sources.parliament.cabinet_ministers import get_parliament_periods
parliaments = get_parliament_periods()  # Automatically uses shared reference
```
```

---

## Step 6: Next Steps After Parliament Consolidation

Once parliament periods are consolidated, consider:

1. **Party Reference** (2-3 hours)
   - Create `dashboard_demo_readonly/utils/party_reference.py`
   - Update both projects to import party mappings

2. **Name Normalization** (2-3 hours)
   - Document deduplication patterns from dashboard_demo
   - Apply to minister name matching

3. **Logging Integration** (1-2 hours)
   - Adopt dashboard_demo logging patterns
   - Add decorator logging to parliament scripts

---

## Estimated Timeline

- **Parliament Reference Setup**: 20-30 minutes
- **Testing & Verification**: 15-20 minutes
- **Documentation**: 10-15 minutes
- **Total**: ~1 hour for first consolidation

**Then**: 2-3 hours for party reference, 2-3 hours for name normalization

---

## Key Benefits

✅ **Eliminates duplicate work**: No more API calls for parliament data
✅ **Single source of truth**: Both projects reference same data
✅ **Faster**: Loads from CSV instead of API call
✅ **Maintainable**: Easy to update one reference location
✅ **Independent**: Fallback to API maintains independence
✅ **Low risk**: Additive changes, no breaking changes

---

## Rollback Plan

If issues arise:

1. Remove shared reference usage from `cabinet_ministers.py`
2. Revert to direct `get_parliament_periods()` API calls
3. Keep shared reference as optional enhancement
4. No data loss or state corruption

---

## Success Criteria

- [ ] `parliament_reference.csv` exists in `dashboard_demo_readonly/output/`
- [ ] `cabinet_ministers.py` loads from shared reference
- [ ] `parliaments.py` saves to shared reference
- [ ] Test script passes all checks
- [ ] DEVELOPER_REFERENCE.md updated with shared reference docs
- [ ] Cabinet ministers extraction still produces correct results

