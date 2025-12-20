# UK Mortality Statistics - Data Summary

## What We Have Now

### 1. **Yearly Totals: 2001-2025** 
**File:** `uk_mortality_comprehensive.csv`
- **Coverage:** 23 years (2001-2017, 2020-2025)
- **Missing:** 2018-2019 (but available in API, just need to add)
- **Source:** Local CSV files + ONS API

### 2. **Deaths by Cause (ICD-10): 2001-2017**
**File:** `uk_mortality_by_cause.csv`
- **Coverage:** 17 years with detailed cause breakdown
- **Granularity:** ICD-10 chapter level (A-Z categories)
- **Examples:**
  - I: Circulatory system diseases (~420k deaths/year)
  - C: Neoplasms/Cancer (~272k deaths/year)
  - J: Respiratory diseases (~135k deaths/year)

## Data Gaps

### Short-term gaps (easily fillable):
- **2018-2019 totals**: Already in our API results, just need to include
- **2020-2025 by cause**: ONS API doesn't provide cause breakdown for recent years

### Long-term gaps (need additional sources):
- **Pre-2001 data**: Need historical mortality files going back to 1970s or earlier

## Options for Extending Coverage

### Option 1: Fill 2018-2019 gap (5 minutes)
✅ **Easiest** - Already have the data from API, just update the script

### Option 2: Get ONS Bulk Historical Files (requires manual steps)
The ONS publishes comprehensive mortality datasets but URLs change frequently:

**Recommended approach:**
1. Visit: https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/deaths/datasets
2. Look for:
   - "Deaths registered in England and Wales" (annual series, goes back decades)
   - "21st Century Mortality Files" (2001-present with ICD codes)
   - "Historical mortality data" (1970s onwards)
3. Download Excel/CSV files manually
4. Place in `data_sources/mortality_stats/ons_downloads/`
5. Run analysis script to incorporate them

### Option 3: Use NOMIS API
**NOMIS** (nomisweb.co.uk) has historical mortality data:
- Coverage: 1970s to present
- Includes: Age, sex, cause of death
- API access available (more stable than ONS beta API)
- Requires free registration

### Option 4: Office for Health Improvement (OHID)
Previously Public Health England, has:
- Mortality rates by cause
- Standardized mortality ratios
- Local authority breakdowns
- Historical trends

## Current Capabilities

With what we have now, you can analyze:

### 1. Total Deaths Trends (2001-2025)
```
2001: 532,498 deaths
2010: 493,242 deaths (-7.4%)
2020: 614,114 deaths (COVID spike: +24%)
2025: 502,553 deaths (partial year)
```

### 2. Top Causes of Death (2001-2017)
```
1. Circulatory diseases (I): ~420k/year
2. Cancer (C): ~270k/year  
3. Respiratory diseases (J): ~135k/year
4. Mental/behavioral (F): ~29k/year
5. Nervous system (G): ~29k/year
```

### 3. Trend Analysis by Cause
- Track how specific causes change over time
- Compare pre-COVID vs COVID era
- Identify emerging health trends

## Recommendation

**Quick Win:** Let me fix the script to include 2018-2019, giving you complete 2001-2025 coverage.

**For 50+ years:** I recommend visiting the ONS datasets page directly to download historical files, as their URLs change frequently and bulk downloads are more reliable than scraping.

Would you like me to:
A) Fix the 2018-2019 gap now?
B) Create a helper script to process any ONS Excel files you download manually?
C) Try the NOMIS API for historical data?
