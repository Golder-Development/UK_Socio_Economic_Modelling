# Economic Data Combined: 1801-2024

## Overview

This dataset combines two comprehensive sources of UK public finances data:

- **PublicFinances1800-2023**: Historical tax receipts, spending by function, borrowing, debt, and GDP (1801-1937)
- **PUSF (Public Sector Finances)**: Detailed financial flows, assets, liabilities, and account levels (1938-2024)

**Total Coverage**: 224 years (1801-2024)  
**Total Measures**: 688 unique economic indicators  
**Total Rows**: 61,843 observations  
**Data Completeness**: 53.5% (33,096 non-null values)

---

## File Structure

### Schema

| Column           | Type    | Description                                            |
| ---------------- | ------- | ------------------------------------------------------ |
| `date_period`    | int     | Calendar year (1801-2024)                              |
| `measure`        | string  | Measure name/description                               |
| `cdid`           | string  | ONS Code Identifier (CDID)                             |
| `value`          | float64 | Measure value (may be NaN for missing data)            |
| `unit`           | string  | Unit of measurement (£m, %, etc.)                      |
| `pre_unit`       | string  | PUSF pre-unit metadata (mostly NaN for PublicFinances) |
| `source_dataset` | string  | "PUSF" or "PublicFinances1800-2023"                    |
| `category`       | string  | Auto-categorized measure type                          |

### Categories

The dataset automatically categorizes measures into 8 groups:

1. **Tax Receipts** (10,979 rows)

   - Income Tax, National Insurance, VAT, Corporation Tax
   - Business Rates, Stamp Duties, Council Tax
   - Customs & Excise, Capital Gains Tax, etc.

2. **Government Spending** (8,976 rows)

   - Defence, Health, Education
   - Social Security (pensioners/non-pensioners)
   - Debt Interest, Other Public Sector Spending

3. **Fiscal Position** (5,233 rows)

   - Public Sector Net Borrowing (PSNB)
   - Public Sector Net Debt (PSND)
   - Deficit/Surplus measures

4. **Economic Indicators** (709 rows)

   - Retail Prices Index (RPI) 1801-2024
   - Nominal GDP (£m)
   - GDP (March-centred, fiscal year adjusted)

5. **Balance Sheet** (10,788 rows - PUSF specific)

   - Assets and Liabilities
   - Equity positions
   - Insurance, Pension, and Guarantee Schemes

6. **Transactions** (1,566 rows - PUSF specific)

   - Financial flows
   - Inter-sector transactions

7. **PUSF - Other** (22,359 rows)

   - Uncategorized PUSF measures

8. **PublicFinances - Other** (1,233 rows)
   - Uncategorized historical measures

---

## Data Sources

### Source Breakdown

| Source                      | Years     | Rows   | Measures | Coverage             |
| --------------------------- | --------- | ------ | -------- | -------------------- |
| **PublicFinances1800-2023** | 1801-1937 | 5,206  | 38       | Historical baseline  |
| **PUSF**                    | 1938-2024 | 56,637 | 650      | Modern detailed data |

### Temporal Structure

```
1801─────────────1937│1938──────────────────────2024
 PublicFinances only │        PUSF only
      (137 years)    │        (87 years)
```

**Overlap Period (1938-2023)**: In the merged dataset, PUSF is used as the primary source for this period, as it provides more granular detail. PublicFinances measures from this period are excluded to avoid duplication.

---

## Key Measures Available

### Tax Receipts (25+ types available from 1801+)

From PublicFinances historical data:

- Income Tax (LIBR-MS62) - 1801+
- National Insurance Contributions (AIIH) - 1801+
- Capital Gains Tax (MS62) - 1801+
- Death Duties/Inheritance Tax (ACCH) - 1801+
- Business Rates (CUKY) - 1801+
- Corporation Tax (CPRN) - 1801+
- Petroleum Revenue Tax (ACCJ) - 1801+
- Energy Profits Levy (JIS6) - 1801+
- VAT/Purchase Tax (NZGF) - 1801+
- Customs & Excise Duties - 1801+
- Stamp Duties (GTBC) - 1801+
- License Fee Receipts (DH7A) - 1801+
- Council Tax (NMHM) - 1801+
- Other Public Sector Taxes & Receipts - 1801+

### Government Spending by Function (1801+)

- Defence Spending - War expenditure patterns over 224 years
- Health Spending - NHS and predecessor systems
- Social Security Spending - Pensioners and non-pensioners
- Education Spending - Historical education investment
- Debt Interest - Cost of servicing public debt
- Other Public Sector Spending (NMFX)

### Fiscal Aggregates (1801+)

- Public Sector Net Borrowing (PSNB) - Annual borrowing requirement
- Public Sector Net Debt (PSND) - Total net debt position
- Nominal GDP (£m) - Economic output for scaling
- Nominal GDP (March-centred) - Fiscal year adjusted

### Price Index (1801-2024)

- **Retail Prices Index (RPI)** - MM23 dataset
  - Base year: Jan 1974 = 100
  - Coverage: 1801-2024 (224 years)
  - Essential for inflation adjustment

### PUSF Detailed Measures (1938-2024)

650 additional measures including:

- Detailed asset and liability positions
- Financial flows and transactions
- Sectoral breakdowns (Central Government, Local Government, Public Corporations)
- Account-level detail (Current Account, Capital Account, Financial Account)

---

## Usage Examples

### 1. Time Series Analysis

```python
import pandas as pd

# Load combined dataset
df = pd.read_csv('economic_data_combined_1800_2024.csv')

# Get Income Tax over time
income_tax = df[df['measure'] == 'Income tax1'].copy()
income_tax = income_tax[['date_period', 'value']].dropna()

# Plot
import matplotlib.pyplot as plt
plt.plot(income_tax['date_period'], income_tax['value'])
plt.title('UK Income Tax Receipts: 1801-2024')
plt.xlabel('Year')
plt.ylabel('£m')
plt.show()
```

### 2. Inflation Adjustment Using RPI

```python
# Get RPI series
rpi = df[df['cdid'] == 'MM23'].copy()
rpi = rpi[['date_period', 'value']].rename(columns={'value': 'rpi'})

# Merge with economic data
df_with_rpi = df.merge(rpi, on='date_period', how='left')

# Convert to real terms (2024 base)
rpi_2024 = rpi[rpi['date_period'] == 2024]['rpi'].values[0]
df_with_rpi['value_real_2024'] = df_with_rpi['value'] * (rpi_2024 / df_with_rpi['rpi'])
```

### 3. Government Spending by Function

```python
# Get spending measures
spending_measures = [
    'Defence5',
    'Health6',
    'Education8',
    'Social Security7',
    'Debt Interest9'
]

spending_df = df[df['measure'].isin(spending_measures)]
spending_pivot = spending_df.pivot(
    index='date_period',
    columns='measure',
    values='value'
)

# Plot spending evolution
spending_pivot.plot(title='UK Government Spending by Function: 1801-2024')
plt.ylabel('£m')
plt.show()
```

### 4. Compare Historical vs Modern Data

```python
# Check data availability by source
availability = df.groupby(['source_dataset', 'category']).agg({
    'value': ['count', lambda x: x.notna().sum()]
}).round(2)

print(availability)
```

---

## Data Quality Notes

### Completeness by Period

- **1801-1900**: ~40-60% complete (PublicFinances)
  - Better coverage for tax receipts and defence spending
  - Limited coverage for some functions (health, education evolving)
- **1900-1937**: ~60-80% complete (PublicFinances)

  - Improved data collection post-Victorian era
  - More comprehensive spending breakdown

- **1938-2024**: ~45-55% complete (PUSF)
  - Very high granularity (650 measures)
  - Many specialized measures with sparse data
  - Core measures well-populated

### Null Value Handling

- `-` symbols in original CSVs converted to `NaN`
- Empty cells preserved as `NaN`
- Nulls represent genuinely missing data (not zero)
- **Important**: Do not interpret `NaN` as zero in analysis

### Data Type Conversions

- All values converted to `float64` for consistency
- Date periods stored as `int` (calendar years)
- CDID codes preserved as strings (may contain combinations like "CUDG+GTAO")

---

## Integration with Population and Mortality Data

### Next Steps

This dataset is designed to be merged with:

1. **Population Data** - Enable per-capita analysis

   ```python
   # Merge with population
   df_merged = df.merge(population_df, on='date_period', how='left')
   df_merged['value_per_capita'] = df_merged['value'] / df_merged['population']
   ```

2. **Mortality Data** - Mortality-weighted fiscal metrics
   ```python
   # Merge with mortality
   df_merged = df.merge(mortality_df, on='date_period', how='left')
   # Calculate mortality-adjusted spending measures
   ```

### Recommended Join Keys

- **Primary key**: `date_period` (calendar year)
- **Secondary keys**: `category` for targeted analysis

---

## Known Limitations

1. **Measure Name Inconsistencies**

   - PublicFinances measures include footnote numbers (e.g., "Income tax1")
   - PUSF measures are long descriptive strings
   - No direct measure overlap between sources (zero common measures)

2. **CDID Code Variations**

   - Some PublicFinances codes are combinations (e.g., "CUDG+GTAO+MF6V")
   - PUSF uses single CDID codes
   - Empty CDID for some measures (especially older historical data)

3. **Unit Variations**

   - PublicFinances: mostly £m (millions)
   - PUSF: mix of £m, £bn, percentages, counts
   - RPI: Index (Jan 1974 = 100)
   - **Critical**: Check `unit` column before aggregating

4. **Fiscal Year vs Calendar Year**

   - PublicFinances uses fiscal year labels (e.g., "1800-01" for fiscal 1800/01)
   - PUSF uses calendar years
   - Both converted to calendar year in this dataset for consistency

5. **Historical Context**
   - Pre-1900 data quality varies significantly
   - Accounting standards evolved over time
   - Some measures (VAT, NI) not applicable in early periods
   - War years (1914-18, 1939-45) show dramatic spending spikes

---

## File Generation

### Generated By

- **Script**: `merge_datasets.py`
- **Date**: 2024 (generated)
- **Dependencies**:
  - `pusf_long_format.csv` (from `transform_pusf_to_long_format.py`)
  - `publicfinances_long_format.csv` (from `transform_publicfinances_to_long_format.py`)

### Reproducibility

To regenerate this file:

```bash
# 1. Transform PUSF to long format
python transform_pusf_to_long_format.py

# 2. Transform PublicFinances to long format
python transform_publicfinances_to_long_format.py

# 3. Merge datasets
python merge_datasets.py
```

---

## Contact & Attribution

- **PUSF Source**: ONS (Office for National Statistics)
- **PublicFinances Source**: ONS/HM Treasury Historical Database
- **RPI Source**: ONS MM23 dataset

For questions about data accuracy or methodology, refer to the original source documentation from ONS.

---

## Version History

- **v1.0** (2024): Initial merge of PUSF (1938-2024) + PublicFinances (1801-1937)
  - 688 measures, 224 years, 61,843 observations
  - Auto-categorization into 8 measure types
  - RPI included for inflation adjustment
