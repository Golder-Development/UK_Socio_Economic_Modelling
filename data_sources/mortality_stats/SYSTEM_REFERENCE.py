#!/usr/bin/env python3
"""
Quick reference for UK Mortality Data Pipeline and Dashboard Generation

This file documents the complete system for generating clean mortality data
with L1 socio-economic classifications and interactive dashboards.
"""

# ============================================================================
# ARCHITECTURE OVERVIEW
# ============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                       UK MORTALITY DATA PIPELINE                            │
└─────────────────────────────────────────────────────────────────────────────┘

INPUT SOURCES (ONS Excel Files)
├── icd1.xls          (1901-1910, 34,519 records)
├── icd2.xls          (1911-1920, 69,349 records)  
├── icd3.xls          (1921-1930, 66,132 records)
├── icd4.xls          (1931-1939, 62,547 records)
├── icd5.xls          (1940-1949, 85,778 records)
├── icd6.xls          (1950-1957, 86,281 records)
├── icd7.xlsx         (1958-1967, 135,537 records)
├── icd8.xls          (1968-1978, 170,442 records)
├── icd9_a.xlsx       (1979-1984, 114,462 records)
├── icd9_b.xls        (1985-1993, 167,680 records)
└── icd9_c.xls        (1994-2000, 122,031 records)

                           │
                           ▼
        STEP 1: build_mortality_per_icd_version.py
        - Load each ICD version independently
        - Extract descriptions from SAME version only
        - Preserve ICD codes (no cross-version contamination)
        - Output: 1,114,758 records with icd_version + description

                           │
                           ▼
        STEP 2: regenerate_all_data_clean.py (steps 1-2)
        - Load per-version compiled data
        - Apply per-version L1 classifications
        - Output: 1,110,961 matched records (99.7%)

                           │
                           ▼
        STEP 3: Generate per-ICD unmatched reports
        - Only 3,797 unmatched records across entire dataset
        - 6 ICD versions with 100% match (ICD1, ICD2, ICD6, ICD7, ICD8, ICD9_A)

                           │
                           ▼
        STEP 4: create_mortality_dashboards.py
        - Generic dashboard builder (accepts any CSV)
        - Flexible category column specification
        - Multiple dashboard types
        - Output: 11-12 interactive Plotly dashboards

                           │
                           ▼
OUTPUT DASHBOARDS (in generated_charts/)
├── mortality_dashboard_interactive.html       (main dashboard)
├── mortality_dashboard_drilldown.html          (cause drill-down)
├── mortality_dashboard_filtered.html           (age/sex filtered)
├── mortality_dashboard_age_groups.html         (by age group)
└── mortality_dashboard_age_*.html             (6 age-based subsets)
"""

# ============================================================================
# PIPELINE EXECUTION
# ============================================================================

"""
FULL AUTOMATED PIPELINE (one command):

    python development_code/regenerate_all_data_clean.py

    This orchestrates:
    ✓ Step 1: Build per-ICD-version compiled data
    ✓ Step 2: Apply L1 classifications  
    ✓ Step 3: Generate unmatched reports
    ✓ Step 4: Create dashboards
    
    Time: ~1 hour (includes 5-minute dashboard generation)

INDIVIDUAL STEPS:

    # Step 1 only
    python build_mortality_per_icd_version.py
    
    # Step 2-4
    python development_code/regenerate_all_data_clean.py --skip-build

    # Dashboard generation only
    python development_code/create_mortality_dashboards.py \\
        uk_mortality_by_cause_1901_onwards_L1.csv
"""

# ============================================================================
# DASHBOARD BUILDER - FLEXIBLE & REUSABLE
# ============================================================================

"""
The create_mortality_dashboards.py script is GENERIC and works with ANY
mortality CSV file. Specify input file and category column via CLI:

EXAMPLE 1: L1-classified data (default)
    python create_mortality_dashboards.py \\
        uk_mortality_by_cause_1901_onwards_L1.csv \\
        --category-column L1_category \\
        --dashboards interactive,drilldown,age_groups

EXAMPLE 2: Compiled (pre-classification) data
    python create_mortality_dashboards.py \\
        uk_mortality_by_cause_1901_onwards_compiled.csv \\
        --category-column cause_description \\
        --dashboards drilldown,subset

EXAMPLE 3: Custom data source
    python create_mortality_dashboards.py \\
        my_custom_mortality_data.csv \\
        --category-column my_group_column \\
        --output-dir ./analysis/dashboards \\
        --dashboards interactive,age_groups

DASHBOARD TYPES:
    ✓ interactive  - Main category-filtered dashboard
    ✓ drilldown    - Top: categories, bottom: top 10 causes
    ✓ filtered     - Age/sex filters + stacked/unstacked toggle
    ✓ age_groups   - Mortality by 10 age groups
    ✓ subset       - 6 age cohort dashboards (preschool, school, adults, OAPs)

REQUIRED CSV COLUMNS:
    - year (numeric): Year of death
    - deaths (numeric): Count of deaths
    - age (string): Age or age range
    - sex (string): Male/Female/All
    - <category_column>: Whatever you specify (e.g., L1_category, cause_description)
    
OPTIONAL COLUMNS:
    - cause (string): ICD code
    - cause_description (string): Description of cause
    - icd_version (string): ICD-1 through ICD-10
    - population (numeric): Used for rate calculations (auto-interpolated if missing)
"""

# ============================================================================
# KEY IMPROVEMENTS FROM V1
# ============================================================================

"""
PROBLEM IN V1 (Old System):
    ✗ Global description merge from mixed-version file
    ✗ ICD-2 unmatched codes contained codes >190 (from ICD-9)
    ✗ Cross-version code contamination
    ✗ Only 73.6% match rate (26.4% spurious unmatched)
    ✗ Hard-coded dashboard builder (not reusable)

SOLUTION IN V2 (Clean System):
    ✓ Per-ICD-version isolated processing (NO cross-version contamination)
    ✓ ICD-2: codes 1-187 numeric, 193 alphanumeric, ZERO codes >190
    ✓ ICD-2: 100% match rate (69,349 / 69,349 records)
    ✓ 99.7% match rate overall (1,110,961 / 1,114,758 records)
    ✓ Generic, reusable dashboard builder (works with any CSV)

DATA QUALITY METRICS:
    
    ICD Version    Records    Matched    % Match
    ─────────────────────────────────────────────
    ICD-1          34,519     34,519     100.0%
    ICD-2          69,349     69,349     100.0%
    ICD-3          66,132     63,887      96.6%
    ICD-4          62,547     61,340      98.1%
    ICD-5          85,778     85,455      99.6%
    ICD-6          86,281     86,281     100.0%
    ICD-7         135,537    135,537     100.0%
    ICD-8         170,442    170,442     100.0%
    ICD-9_A       114,462    114,462     100.0%
    ICD-9_B       167,677    167,677     100.0%
    ICD-9_C       122,031    122,012      99.9%
    ─────────────────────────────────────────────
    TOTAL       1,114,758  1,110,961      99.7%
"""

# ============================================================================
# FILES & LOCATIONS
# ============================================================================

"""
DATA_SOURCES DIRECTORY:
data_sources/mortality_stats/
├── ons_downloads/extracted/          # Input Excel files (icd1.xls - icd9_c.xls)
├── socio_economic_classification/
│   ├── inputs/                        # ICD code lists
│   │   └── icdXcodes.csv  (for X=1-10)
│   └── outputs/                       # L1 classification results
│       └── icdXresults.csv (for X=1-10)
├── build_mortality_per_icd_version.py (STEP 1)
├── development_code/
│   ├── regenerate_all_data_clean.py   (MAIN PIPELINE ORCHESTRATOR)
│   └── create_mortality_dashboards.py (GENERIC DASHBOARD BUILDER)
├── uk_mortality_by_cause_1901_onwards_compiled.csv   (STEP 1 OUTPUT)
├── uk_mortality_by_cause_1901_onwards_L1.csv         (STEP 2 OUTPUT)
├── icd_unmatched_codes_detail_*.csv                  (STEP 3 OUTPUT)
├── icd_unmatched_codes_summary.csv                   (STEP 3 OUTPUT)
└── DASHBOARD_BUILDER_GUIDE.md         (USAGE DOCUMENTATION)

GENERATED CHARTS DIRECTORY:
generated_charts/
├── mortality_dashboard_interactive.html       (11.8 MB - main dashboard)
├── mortality_dashboard_drilldown.html          (7.3 MB)
├── mortality_dashboard_filtered.html           (4.9 MB)
├── mortality_dashboard_age_groups.html         (5.1 MB)
├── mortality_dashboard_age_preschool.html      (5.0 MB)
├── mortality_dashboard_age_school.html         (5.0 MB)
├── mortality_dashboard_age_young_adults.html   (5.0 MB)
├── mortality_dashboard_age_older_adults.html   (5.0 MB)
├── mortality_dashboard_age_young_oaps.html     (5.0 MB)
└── mortality_dashboard_age_old_oaps.html       (5.0 MB)
"""

# ============================================================================
# COMMON WORKFLOWS
# ============================================================================

"""
WORKFLOW 1: Generate everything from scratch
    cd data_sources/mortality_stats
    python development_code/regenerate_all_data_clean.py
    
    Output: Clean compiled data + L1 classifications + dashboards

WORKFLOW 2: Just update dashboards (data already exists)
    cd data_sources/mortality_stats/development_code
    python create_mortality_dashboards.py \\
        ../uk_mortality_by_cause_1901_onwards_L1.csv

WORKFLOW 3: Quick analysis of compiled data (before classification)
    cd data_sources/mortality_stats/development_code
    python create_mortality_dashboards.py \\
        ../uk_mortality_by_cause_1901_onwards_compiled.csv \\
        --category-column cause_description \\
        --dashboards drilldown,subset

WORKFLOW 4: Age-specific analysis only
    cd data_sources/mortality_stats/development_code
    python create_mortality_dashboards.py \\
        ../uk_mortality_by_cause_1901_onwards_L1.csv \\
        --dashboards age_groups,subset

WORKFLOW 5: Export to future classification system
    # Regenerate with different category column (when new classification ready)
    python create_mortality_dashboards.py \\
        uk_mortality_by_future_classification.csv \\
        --category-column new_category_column \\
        --output-dir ./future_charts
"""

# ============================================================================
# TESTING & VERIFICATION
# ============================================================================

"""
VERIFY ICD-2 CODES (check for cross-version contamination):
    
    python -c "
    import pandas as pd
    df = pd.read_csv('uk_mortality_by_cause_1901_onwards_L1.csv')
    df2 = df[df['icd_version'] == 'ICD2']
    codes = df2['cause'].unique()
    numeric = [int(c) for c in codes if str(c).isdigit()]
    print(f'ICD-2 codes range: {min(numeric)} to {max(numeric)}')
    high = [c for c in numeric if c > 190]
    print(f'Codes > 190: {len(high)} [SHOULD BE 0]')
    "
    
    Expected output:
    ICD-2 codes range: 1 to 187
    Codes > 190: 0

VERIFY MATCH RATES BY VERSION:
    
    python verify_clean_pipeline.py
    
    Expected: >95% match for all versions, >99.7% overall

CHECK UNMATCHED CODES:
    
    ls -la icd_unmatched_codes_detail_*.csv
    
    Expected: Only ICD3, ICD4, ICD5, ICD9_B, ICD9_C with small unmatched sets

VERIFY DASHBOARD FILES EXIST:
    
    ls generated_charts/mortality_dashboard_*.html | wc -l
    
    Expected: 11 files (interactive, drilldown, filtered, age_groups, 6 subsets)
"""

# ============================================================================
# COMMAND REFERENCE
# ============================================================================

"""
QUICK COMMAND REFERENCE:

# Full pipeline (data + dashboards)
python development_code/regenerate_all_data_clean.py

# Just dashboards from L1 data
python development_code/create_mortality_dashboards.py \\
    uk_mortality_by_cause_1901_onwards_L1.csv

# Just dashboards from compiled data
python development_code/create_mortality_dashboards.py \\
    uk_mortality_by_cause_1901_onwards_compiled.csv \\
    --category-column cause_description

# Just dashboards, specific types
python development_code/create_mortality_dashboards.py \\
    uk_mortality_by_cause_1901_onwards_L1.csv \\
    --dashboards interactive,age_groups

# Custom output directory
python development_code/create_mortality_dashboards.py \\
    uk_mortality_by_cause_1901_onwards_L1.csv \\
    --output-dir ./my_dashboards

# Verify data quality
python verify_clean_pipeline.py

# Check unmatched codes
python -c "import pandas as pd; df = pd.read_csv('icd_unmatched_codes_summary.csv'); print(df.head(20))"
"""

# ============================================================================
# KEY DESIGN PRINCIPLES
# ============================================================================

"""
1. ICD VERSION ISOLATION
   - Each ICD version processed independently
   - No cross-version code lookup or contamination
   - Descriptions come ONLY from that version's source file

2. REUSABLE COMPONENTS
   - Dashboard builder works with ANY mortality CSV
   - Category column specified at runtime (not hard-coded)
   - Easy to extend for future classification schemes

3. QUALITY FIRST
   - 99.7% match rate for 1.1M+ records
   - Per-version unmatched reports for review
   - No spurious codes from cross-version contamination

4. TRANSPARENCY
   - Clear logging at each step
   - Unmatched codes visible and exportable
   - Match rates reported per ICD version
   - All code changes documented

5. PERFORMANCE
   - Full pipeline: ~1 hour
   - Just dashboards: ~2 minutes
   - Per-version processing parallelizable (future optimization)
"""
