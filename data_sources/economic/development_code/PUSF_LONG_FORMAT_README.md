# PUSF Long-Format Transformation

## Overview

The `pusf_long_format.csv` is a tidy/long-format transformation of the original PUSF (Public sector use of Financial statistics) CSV file from the ONS (Office for National Statistics).

## Transformation Details

**Source file:** `downloaded_sourcefiles/pusf.csv`
**Output file:** `pusf_long_format.csv`
**Transformation script:** `transform_pusf_to_long_format.py`

### File Structure

#### Input Format (Wide/Pivot)

The original PUSF CSV has:

- **Metadata rows (0-6):**

  - Row 0: Measure titles/descriptions
  - Row 1: CDID codes (UK Office for National Statistics codes)
  - Row 2: PreUnit (currency indicator - £ or m)
  - Row 3: Unit (measurement unit - m for millions, M for millions, % for percentage, etc.)
  - Row 4: Release Date
  - Row 5: Next release
  - Row 6: Important Notes

- **Data rows (7+):** Each row represents a year, with columns containing values for different measures

#### Output Format (Long/Tidy)

Each row represents a single **date_period + measure + value** combination:

| Column      | Description                               | Type   | Example                                             |
| ----------- | ----------------------------------------- | ------ | --------------------------------------------------- |
| date_period | Year of the observation                   | int    | 1946                                                |
| measure     | Full descriptive name of the measure      | string | "General Government Net Borrowing as a %GDP: CPNSA" |
| cdid        | Official ONS CDID code                    | string | "A3PT"                                              |
| value       | The numeric value for this period/measure | float  | 0.5 (or NaN if missing)                             |
| unit        | Measurement unit                          | string | "m", "M", "%", ""                                   |
| pre_unit    | Currency prefix                           | string | "£", ""                                             |

## Data Summary

- **Total rows:** 56,637
- **Unique measures:** 650
- **Date range:** 1938 to 2024
- **Non-null values:** 30,860 (54.5%)
- **Missing values:** 25,777 (45.5%)

The high percentage of missing/null values is expected as:

1. Many measures only started being collected in recent years
2. Some measures are discontinued
3. Sparse historical data, particularly for older years

## Data Quality Notes

### Null Handling

- Missing values in the original file are preserved as NaN in the long format
- This allows for proper multi-variant analysis with population and mortality data
- Null entries are retained (not filtered out) to maintain full temporal coverage

### Value Types

- All values are converted to float64 to handle both integers and decimals
- Currency values are kept in their original units (millions or billions as specified by the unit column)
- Percentage values retain decimal places

## Use Cases

This tidy format enables:

1. **Time Series Analysis:** Easy filtering by measure and date
2. **Multi-variant Analysis:** Joining with population and mortality data on date_period
3. **Comparative Analysis:** Querying specific measures across time periods
4. **Data Validation:** Simple identification of null patterns and data gaps
5. **Machine Learning:** Ready for feature engineering with aligned date periods

## Example Queries

### Find all values for a specific measure and year

```python
df[(df['measure'] == 'General Government Net Borrowing as a %GDP: CPNSA') &
   (df['date_period'] == 2020)]
```

### Get all non-null values in a year range

```python
df[(df['date_period'] >= 2010) & (df['date_period'] <= 2020) &
   (df['value'].notna())]
```

### Calculate annual statistics by measure

```python
df.groupby(['date_period', 'measure'])['value'].agg(['count', 'mean', 'sum'])
```

## Integration with Other Datasets

To combine with population and mortality data:

```python
# Assuming population_df and mortality_df are similarly formatted
combined = pusf_long.merge(
    population_df,
    on='date_period',
    how='outer'
).merge(
    mortality_df,
    on='date_period',
    how='outer'
)
```

## Technical Details

### Column Alignment

- Original columns are transformed row-by-row to ensure data integrity
- Year index matches exactly with the source file
- CDID codes are preserved as string values for accurate lookups

### Missing Data Patterns

Row-level nulls occur when:

- Measure did not exist in the original data for that year
- Data collection had gaps
- Confidentiality restrictions applied

## Next Steps

1. **Merge with population data** on `date_period`
2. **Merge with mortality data** on `date_period`
3. **Create composite measures** for multi-variant analysis
4. **Normalize values** if combining different unit types
5. **Validate patterns** by comparing with original source file

## References

- Source: ONS PUSF releases
- Original file: `pusf.csv`
- Data dictionary: Refer to CDID codes in ONS database
