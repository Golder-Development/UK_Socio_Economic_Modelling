# Economic Data with Population: 1801-2024

## Overview

This dataset combines UK public finances data (1801-2024) with population data (1901-2016), enabling per-capita economic analysis across 116 years of population records.

**Supersedes**: [economic_data_combined_1800_2024.csv](economic_data_combined_1800_2024.csv)

**Total Coverage**: 224 years economic data (1801-2024), 116 years population data (1901-2016)  
**Total Measures**: 688 unique economic indicators + population  
**Total Rows**: 61,843 observations  
**Population Coverage**: 85.4% of rows (52,835 with population data)  
**Per-Capita Values**: 12,075 observations (19.5% of total)

---

## What's New

### Population Data Integration

- **Years covered**: 1901-2016 (116 years)
- **Source**: ONS combined_population_data.csv
- **Aggregation**: Total UK population (sum of all age groups and sexes)
- **Merge key**: `date_period` (calendar year)

### Per-Capita Measures

Automatically calculated for monetary categories:

- **Tax Receipts** - 5,502 per-capita values
- **Government Spending** - 4,069 per-capita values
- **Fiscal Position** - 2,504 per-capita values

**Total**: 12,075 per-capita calculations available

---

## File Structure

### Schema

| Column                 | Type        | Description                                   |
| ---------------------- | ----------- | --------------------------------------------- |
| `date_period`          | int         | Calendar year (1801-2024)                     |
| `measure`              | string      | Measure name/description                      |
| `cdid`                 | string      | ONS Code Identifier (CDID)                    |
| `value`                | float64     | Measure value in original units (£m, %, etc.) |
| `unit`                 | string      | Unit of measurement                           |
| `source_dataset`       | string      | "PUSF" or "PublicFinances1800-2023"           |
| `pre_unit`             | string      | PUSF pre-unit metadata                        |
| `category`             | string      | Auto-categorized measure type                 |
| **`population`**       | **float64** | **Total UK population (NEW)**                 |
| **`value_per_capita`** | **float64** | **Value per person in £ (NEW)**               |

### Population Coverage by Period

```
1801────1900│1901─────────────────2016│2017───2024
  No pop    │    Population data      │  No pop
  (100yrs)  │      (116 years)        │  (8 yrs)
```

**Rows with population**: 52,835 (85.4%)  
**Rows without population**: 9,008 (14.6%)

---

## Per-Capita Calculation Details

### Formula

```python
value_per_capita = (value * 1,000,000) / population
```

Where:

- `value` is in £ millions (from economic data)
- `population` is total persons
- `value_per_capita` is in £ per person

### Categories with Per-Capita Data

| Category                | Total Rows | With Per-Capita | Coverage |
| ----------------------- | ---------- | --------------- | -------- |
| **Tax Receipts**        | 10,979     | 5,502           | 50.1%    |
| **Government Spending** | 8,976      | 4,069           | 45.3%    |
| **Fiscal Position**     | 5,233      | 2,504           | 47.9%    |
| Balance Sheet           | 10,788     | 0               | 0% \*    |
| Economic Indicators     | 709        | 0               | 0% \*    |
| PUSF - Other            | 22,359     | 0               | 0% \*    |
| Transactions            | 1,566      | 0               | 0% \*    |
| PublicFinances - Other  | 1,233      | 0               | 0% \*    |

\* Per-capita not applicable for non-monetary measures

---

## Usage Examples

### 1. Basic Per-Capita Analysis

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('economic_data_with_population_1800_2024.csv')

# Filter for a specific measure with per-capita data
income_tax = df[
    (df['measure'] == 'Income tax1') &
    (df['value_per_capita'].notna())
]

# Plot per-capita income tax over time
plt.figure(figsize=(12, 6))
plt.plot(income_tax['date_period'], income_tax['value_per_capita'])
plt.title('UK Income Tax Per Capita: 1901-2016')
plt.xlabel('Year')
plt.ylabel('£ per person')
plt.grid(True)
plt.show()
```

### 2. Compare Nominal vs Per-Capita Trends

```python
# Get defence spending
defence = df[
    (df['measure'].str.contains('Defence', case=False, na=False)) &
    (df['value'].notna())
].copy()

# Create visualization comparing nominal and per-capita
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

# Nominal values
defence_nominal = defence[defence['value'].notna()]
ax1.plot(defence_nominal['date_period'], defence_nominal['value'])
ax1.set_title('Defence Spending (Nominal)')
ax1.set_ylabel('£m')
ax1.set_xlabel('Year')

# Per-capita values
defence_pc = defence[defence['value_per_capita'].notna()]
ax2.plot(defence_pc['date_period'], defence_pc['value_per_capita'])
ax2.set_title('Defence Spending (Per Capita)')
ax2.set_ylabel('£ per person')
ax2.set_xlabel('Year')

plt.tight_layout()
plt.show()
```

### 3. Tax Burden Analysis

```python
# Get all tax receipts per capita for a recent year
tax_2016 = df[
    (df['date_period'] == 2016) &
    (df['category'] == 'Tax Receipts') &
    (df['value_per_capita'].notna())
].sort_values('value_per_capita', ascending=False)

print("Tax Burden Per Capita (2016):")
print(tax_2016[['measure', 'value_per_capita', 'population']])

# Total tax per capita
total_tax_pc = tax_2016['value_per_capita'].sum()
print(f"\nTotal tax per capita: £{total_tax_pc:,.2f}")
```

### 4. Population-Weighted Fiscal Analysis

```python
# Calculate spending as % of population-weighted average
spending = df[
    (df['category'] == 'Government Spending') &
    (df['value_per_capita'].notna())
]

# Group by year to get total spending per capita
spending_by_year = spending.groupby('date_period')['value_per_capita'].sum()

# Plot evolution
plt.figure(figsize=(12, 6))
plt.plot(spending_by_year.index, spending_by_year.values)
plt.title('Total Government Spending Per Capita')
plt.ylabel('£ per person')
plt.xlabel('Year')
plt.grid(True)
plt.show()
```

### 5. Combine with RPI for Real Per-Capita Values

```python
# Get RPI data
rpi = df[df['cdid'] == 'MM23'][['date_period', 'value']].copy()
rpi.columns = ['date_period', 'rpi']

# Merge RPI with per-capita data
df_with_rpi = df.merge(rpi, on='date_period', how='left')

# Calculate real per-capita (2016 base)
rpi_2016 = rpi[rpi['date_period'] == 2016]['rpi'].values[0]
df_with_rpi['value_per_capita_real_2016'] = (
    df_with_rpi['value_per_capita'] * (rpi_2016 / df_with_rpi['rpi'])
)

# Example: Real income tax per capita over time
income_tax_real = df_with_rpi[
    (df_with_rpi['measure'] == 'Income tax1') &
    (df_with_rpi['value_per_capita_real_2016'].notna())
]

plt.figure(figsize=(12, 6))
plt.plot(income_tax_real['date_period'], income_tax_real['value_per_capita_real_2016'])
plt.title('Real Income Tax Per Capita (2016 prices)')
plt.ylabel('£ per person (2016 prices)')
plt.xlabel('Year')
plt.grid(True)
plt.show()
```

---

## Data Quality Notes

### Population Data Limitations

1. **Geographic Coverage**: England & Wales initially, expanded to UK over time
2. **Census Years**: Population estimates interpolated between census years
3. **War Years**: Population may include military personnel overseas
4. **Missing Years**:
   - 1801-1900: No population data available (14.6% of economic data)
   - 2017-2024: Population data not yet available (8 years)

### Per-Capita Calculation Notes

1. **Monetary Values Only**: Per-capita calculated only for £m values
2. **Categories Included**: Tax Receipts, Government Spending, Fiscal Position
3. **Not Applicable**:

   - Percentages (e.g., interest rates)
   - Index values (e.g., RPI)
   - Counts (e.g., number of transactions)
   - Non-monetary balance sheet items

4. **Negative Values**: Fiscal deficits and borrowing show negative per-capita values

### Example Per-Capita Values (2016)

| Measure           | Per Capita (£) | Category            |
| ----------------- | -------------- | ------------------- |
| Total taxes       | £8,668         | Tax Receipts        |
| Total expenditure | £12,982        | Government Spending |
| Net borrowing     | £-993          | Fiscal Position     |
| Health spending   | £2,500-3,000   | Government Spending |
| Defence spending  | £800-900       | Government Spending |

---

## Integration Timeline

```
Economic Data Pipeline:
1. PUSF (1938-2024) ──────┐
2. PublicFinances (1801-1937) ──┐
                                 ├──> Merged (1801-2024)
                                 │
3. Population (1901-2016) ───────┴──> WITH POPULATION (current file)
                                      │
4. Mortality (TBD) ──────────────────┴──> FINAL DATASET (next step)
```

**Current Status**: Population integration complete ✓  
**Next Step**: Mortality data integration

---

## Known Issues & Workarounds

### Issue 1: Missing Population for Early Years (1801-1900)

**Impact**: 100 years of economic data without per-capita values  
**Workaround**: Use nominal values only, or extrapolate population from 1901 baseline

```python
# Extrapolate population backwards (rough estimate)
# Assumes constant growth rate from 1901-1910
early_pop = df[df['date_period'].between(1901, 1910)][['date_period', 'population']]
growth_rate = (early_pop['population'].iloc[-1] / early_pop['population'].iloc[0]) ** (1/9) - 1

# Apply to earlier years (use with caution)
```

### Issue 2: Missing Population for Recent Years (2017-2024)

**Impact**: 8 years of latest economic data without per-capita values  
**Workaround**: Use 2016 population as approximation, or source 2017-2024 estimates

```python
# Use 2016 population for 2017-2024 (temporary)
pop_2016 = df[df['date_period'] == 2016]['population'].iloc[0]
df.loc[df['date_period'] >= 2017, 'population'] = pop_2016
```

### Issue 3: Per-Capita Values Appear Low for Some Measures

**Cause**: PUSF measures may be subset values (e.g., specific asset types)  
**Solution**: Check measure name carefully - not all measures represent total values

---

## File Generation

### Generated By

- **Script**: `integrate_population.py`
- **Date**: 2024 (generated)
- **Dependencies**:
  - `economic_data_combined_1800_2024.csv`
  - `combined_population_data.csv` (from ONS)

### Reproducibility

```bash
# Generate this file
python integrate_population.py
```

---

## Column Completeness Summary

| Column               | Non-Null Count | Coverage  | Notes                                 |
| -------------------- | -------------- | --------- | ------------------------------------- |
| date_period          | 61,843         | 100.0%    | Always present                        |
| measure              | 61,843         | 100.0%    | Always present                        |
| cdid                 | 60,473         | 97.8%     | Some historical measures lack codes   |
| value                | 33,096         | 53.5%     | Economic values (many nulls expected) |
| unit                 | 35,482         | 57.4%     | Mostly populated                      |
| source_dataset       | 61,843         | 100.0%    | Always present                        |
| pre_unit             | 29,667         | 48.0%     | PUSF only                             |
| category             | 61,843         | 100.0%    | Auto-categorized                      |
| **population**       | **52,835**     | **85.4%** | **1901-2016 only**                    |
| **value_per_capita** | **12,075**     | **19.5%** | **Requires both value & population**  |

---

## Related Files

- [PUSF_LONG_FORMAT_README.md](PUSF_LONG_FORMAT_README.md) - PUSF transformation documentation
- [COMPARISON_ANALYSIS.md](COMPARISON_ANALYSIS.md) - PublicFinances comparison analysis
- [ECONOMIC_DATA_COMBINED_README.md](ECONOMIC_DATA_COMBINED_README.md) - Pre-population merge documentation

---

## Next Steps: Mortality Integration

The final integration will add mortality data to enable:

- Mortality-weighted fiscal burden analysis
- Health spending vs mortality correlation
- Demographic transition impact on public finances

Expected output: `economic_data_complete_1800_2024.csv` with mortality metrics

---

## Version History

- **v1.0** (2024): Initial population integration
  - Added population column (1901-2016)
  - Created per-capita calculations for monetary categories
  - 12,075 per-capita values generated
