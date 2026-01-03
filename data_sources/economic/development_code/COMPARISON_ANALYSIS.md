# Comparison Analysis: PUSF.csv vs PublicFinances1800-2023.csv

## Executive Summary

**Finding:** The PublicFinances file provides valuable historical data that extends PUSF backwards from 1938 to 1800, covering 224 years of UK public finances history.

---

## 1. File Characteristics

### PUSF.csv

- **Coverage:** 1938-2024 (87 years)
- **Measures:** 651 unique economic indicators
- **Focus:** Detailed financial flows, assets, liabilities, and account levels
- **Granularity:** Very high (comprehensive accounting framework)
- **Data Completeness:** 45.7% non-null values

### PublicFinances1800-2023.csv

- **Coverage:** 1800-2023 (224 years)
- **Measures:** ~21 core measures (structured differently than PUSF)
- **Focus:** Tax receipts, spending by function, debt, borrowing
- **Granularity:** Medium (aggregated categories)
- **Data Completeness:** High for available years, especially 1900+

---

## 2. Unique Measures in PublicFinances (NOT in PUSF)

The following core measures appear in PublicFinances but have no direct equivalent in PUSF:

### Tax Receipts

1. **Income Tax** (LIBR-MS62)
2. **National Insurance Contributions** (AIIH)
3. **Capital Gains Tax** (MS62)
4. **Death Duties/Inheritance Tax** (ACCH)
5. **Business Rates** (CUKY)
6. **Corporation Tax** (CPRN)
7. **Petroleum Revenue Tax** (ACCJ)
8. **Energy Profits Levy** (JIS6)
9. **Other Business Taxes** (KIH3 + N43V)
10. **VAT/Purchase Tax** (NZGF)
11. **Customs & Excise Duties** (CUDG+GTAO+MF6V+EKED+CDDZ+CWAA)
12. **Stamp Duties** (GTBC)
13. **License Fee Receipts** (DH7A)
14. **Council Tax** (NMHM)
15. **Other Public Sector Taxes & Receipts** (GCSU)

### Spending by Function

16. **Defence Spending** (specific coding)
17. **Health Spending** (specific coding)
18. **Social Security Spending** (specific coding)
    - Subset: Pensioners
    - Subset: Non-pensioners
19. **Education Spending** (specific coding)
20. **Other Public Sector Spending** (NMFX)

### Key Fiscal Aggregates

21. **Public Sector Net Borrowing (PSNB)** - Main borrowing measure
22. **Public Sector Net Debt (PSND)** - Total net debt
23. **Nominal GDP (£m)** - Annual GDP in millions
24. **Nominal GDP (March-centred)** - Fiscal-year adjusted GDP

### Price Index

25. **Retail Prices Index (RPI)** - 1800-2024 series, Jan 1974=100

---

## 3. Integration Potential

### High Value Additions

| Measure                         | Period    | Value                                        | Source            |
| ------------------------------- | --------- | -------------------------------------------- | ----------------- |
| Income Tax flows                | 1800-2023 | Historical tax analysis                      | LIBR-MS62         |
| Government spending by function | 1800-2023 | Sectoral allocation patterns                 | Various           |
| Historical GDP                  | 1800-2023 | Long-term economic scaling                   | National Accounts |
| Retail Price Index              | 1800-2024 | Inflation adjustment/nominal-real conversion | ONS MM23          |
| Defence spending                | 1800-2023 | War/military expenditure patterns            | Defence tracking  |

### Multi-Variant Analysis Opportunities

1. **Tax-to-GDP Ratios** (1800-2024)

   - Combine PUSF/PublicFinances tax revenue with PublicFinances GDP
   - Track taxation patterns over 224 years

2. **Spending Composition** (1800-2024)

   - Analyse shifts in government priorities
   - Health, education, social security allocation patterns
   - Defence spending cycles

3. **Fiscal Sustainability** (1800-2024)

   - Borrowing vs spending patterns
   - Debt accumulation cycles
   - Austerity periods identification

4. **Real vs Nominal Analysis** (1800-2024)

   - Use RPI to deflate historical values
   - Compare real spending across centuries

5. **Demographic-Fiscal Correlation** (1938-2024)
   - Combine with population & mortality data
   - Spending-per-capita trends
   - Social spending patterns vs demographics

---

## 4. Data Structure Differences

### PUSF Format (Recommended for transformation)

```
Row 0:  Measure titles
Row 1:  CDID codes (ONS identifiers)
Row 2:  PreUnit (currency prefix)
Row 3:  Unit (m, M, %, etc.)
Row 7+: Data by year
```

### PublicFinances Format (Unique structure)

```
Row 1:  Navigation header ("Back to contents")
Row 2:  Category groupings (non-CG Receipts, Spending by Function, etc.)
Row 3:  Measure names
Row 4:  ONS present codes (CDID equivalents)
Row 5+: Data by fiscal year (1800-2023)
```

---

## 5. Recommended Integration Approach

### Option A: Extended Timeline (RECOMMENDED)

**Best for historical analysis**

- Use PublicFinances 1800-1937 (224 years of baseline metrics)
- Use PUSF 1938-2024 (detailed modern metrics)
- Join on date_period
- Result: 225-year dataset with increasing granularity forward

**Advantages:**
✓ Longest temporal coverage
✓ Best data quality for each period
✓ Captures institutional changes over time

### Option B: Enriched Current Data

**Best for modern analysis with historical context**

- Primary: PUSF 1938-2024 (main dataset)
- Enrichment: PublicFinances measures for overlap period 1938-2023
- Add RPI from PublicFinances for all years 1938-2024
- Result: PUSF with historical context

**Advantages:**
✓ Leverages PUSF's superior granularity
✓ Adds historical tax/spending detail
✓ RPI enables real-value analysis

### Option C: Dual Dataset

**For comparative analysis**

- Keep both datasets separate
- PublicFinances as supplementary "macro" view
- PUSF as primary "detail" view
- Merge on common fiscal aggregates for validation

**Advantages:**
✓ Data quality validation
✓ Independent cross-check
✓ Longer historical lookback available

---

## 6. Implementation Roadmap

### Phase 1: Transform PublicFinances to Long Format

Create `publicfinances_long_format.csv` (similar to `pusf_long_format.csv`)

- Columns: date_period, measure, cdid, value, unit, category
- Rows: One per date × measure combination
- Handle fiscal year labeling (e.g., 1800-01)

### Phase 2: Validate Historical Overlap (1938-2023)

- Compare common measures between PUSF and PublicFinances
- Identify data reconciliation issues
- Document methodology differences

### Phase 3: Merge Datasets

```
Combined dataset:
- 1800-1937: PublicFinances data
- 1938-2023: Both (prioritize PUSF where granular, include PF for macro)
- 2024: PUSF only
```

### Phase 4: Integrate with Population & Mortality

- Merge on date_period
- Create per-capita and ratio measures
- Normalize inflation using RPI

### Phase 5: Multi-Variant Analysis

- Historical patterns 1800-2024
- Demographic-fiscal correlation 1938-2024
- Tax composition evolution
- Spending prioritization trends

---

## 7. Key Metrics for Integration

### From PublicFinances (Add to PUSF dataset)

- **RPI (Retail Price Index)** - Essential for real-value conversion
- **Income tax receipts** - Primary revenue source
- **Spending by function** - Sectoral allocation
- **Net borrowing** - Core fiscal indicator
- **GDP nominal** - For ratio calculations

### Maintain from PUSF

- All existing 651 measures
- Detailed financial asset/liability breakdown
- Account-level flows and stock positions

---

## 8. Data Quality Notes

### PublicFinances Strengths

- Longest historical coverage (1800-2023)
- Clean aggregated measures
- Official ONS codes provided
- RPI series particularly valuable

### PublicFinances Limitations

- Lower granularity than PUSF
- Some gaps in 1800-1900 period
- Fiscal year labeling (1800-01) vs calendar year
- Some measures marked with notes/caveats

### Integration Considerations

1. **Fiscal vs Calendar Years:** PublicFinances uses fiscal years (April-March)

   - Consider converting to calendar years or noting period type

2. **Consistency Checks:** Validate overlapping measures 1938-2023

   - PSND/PSNB should align with PUSF equivalents
   - Tax receipts should reconcile

3. **RPI Conversion:** Use for historical purchasing power parity
   - Account for different base years across measures

---

## 9. Conclusion

**Recommendation: IMPLEMENT OPTION A (Extended Timeline)**

The PublicFinances dataset provides **crucial historical extension** enabling:

- 225-year analysis capability (vs 87 years from PUSF alone)
- Institutional continuity across government structure changes
- Long-term fiscal patterns and trends
- Inflation-adjusted historical comparisons

**Priority measures to incorporate:**

1. RPI (Retail Price Index) - Critical for all deflation
2. Net borrowing & net debt - Macro fiscal health
3. Spending by function - Allocation patterns
4. Tax receipts - Revenue evolution

**Timeline:** 2-3 weeks for full integration with population and mortality data

---

## 10. Files to Create

1. `publicfinances_long_format.csv` - Transformed PublicFinances data
2. `economic_data_combined_1800_2024.csv` - Merged PUSF + PublicFinances
3. `economic_data_enriched_1938_2024.csv` - Combined with population/mortality
4. `transformation_notes_publicfinances.md` - Documentation of process
