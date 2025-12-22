# ICD-10 Data Integration - Quick Start Guide

## What Changed?

Your mortality data pipeline now automatically processes the new files:
- ✅ `compiled_mortality_2001_2019.csv` (351,085 records)
- ✅ `ICD10_codes.xlsx` (5,366 code descriptions)

## File Locations
```
data_sources/mortality_stats/
├── ons_downloads/extracted/
│   ├── compiled_mortality_2001_2019.csv    ← NEW DATA
│   ├── ICD10_codes.xlsx                    ← NEW REFERENCE
│   ├── icd1.xls through icd9_c.xls        ← Historical (unchanged)
│
├── build_comprehensive_mortality_1901_2025.py  (UPDATED)
├── development_code/
│   └── regenerate_all_data.py               (UPDATED)
```

## What Happens Automatically

When you run the pipeline:
1. **Historical data** (1901-2000) is loaded from archives
2. **New 2001-2019 data** is loaded from your CSV
3. **ICD-10 descriptions** are looked up from Excel file
4. **All data combined** into unified format
5. **Output files** include ICD-10 code descriptions

## Sample Output

Your data now includes records like this:
```
year  cause  sex    age   deaths  icd10_description
2001  A010   Male   <1    1       Typhoid
2008  J12    Female 25-34 8       Viral pneumonia
2017  I63    Male   75+   145     Cerebral infarction
```

## How to Use

### Regenerate All Data
```bash
cd data_sources/mortality_stats/development_code
python regenerate_all_data.py
```

### Just Build Comprehensive Database
```bash
cd data_sources/mortality_stats
python build_comprehensive_mortality_1901_2025.py
```

### With Verbose Output
```bash
python regenerate_all_data.py --verbose
```

## Output Files

After running, you get:
- `uk_mortality_comprehensive_1901_2025.zip` - Complete dataset (1,465,842 records)
- `uk_mortality_by_cause_1901_2025.zip` - By ICD code (1,465,842 records)
- `uk_mortality_yearly_totals_1901_2025.csv` - Annual summaries (117 rows)

All files now include data from **1901-2017** with **integrated ICD-10 descriptions**.

## FAQ

**Q: Do I need to update anything else?**
A: No! The pipeline automatically handles the new data.

**Q: What if I have 2018-2025 data?**
A: Add it to the same folder with same column structure, re-run the script.

**Q: What if ICD-10 codes need updating?**
A: Update the Excel file, re-run the script - descriptions auto-remap.

**Q: Does this affect harmonization?**
A: No! The harmonized category mapping works the same way.

**Q: Can I preview the data?**
A: Yes - the CSV in the ZIP files is easily readable with pandas/Excel.

```python
import pandas as pd
import zipfile

# Quick preview
with zipfile.ZipFile('uk_mortality_comprehensive_1901_2025.zip') as zf:
    df = pd.read_csv(zf.open('uk_mortality_comprehensive_1901_2025.csv'))
    print(df.head(10))
    print(f"\nTotal records: {len(df):,}")
    print(f"Year range: {df['year'].min()}-{df['year'].max()}")
    print(f"Columns: {list(df.columns)}")
```

## Support

For questions about:
- **Data structure** → See `ENHANCEMENT_SUMMARY.md`
- **Harmonization** → See `README.md`
- **Schema details** → See `INDEX.md`

---

**Enhanced:** December 22, 2025
**Status:** Ready to use ✅
