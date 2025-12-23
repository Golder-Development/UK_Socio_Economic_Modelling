# UK Economic Indicators - Public Finances Dataset

## 📊 Overview

This folder contains UK public finance data spanning over two centuries (1800-2023), providing comprehensive historical context for government revenues, expenditures, borrowing, debt, and GDP. The dataset enables analysis of long-term economic trends, fiscal policy evolution, and the relationship between government finances and mortality/social outcomes.

## ✅ What You Have

### 1. **Public Finances: 1800-2023** (224 years)

**File:** `PublicFinances1800-2023.csv`

```text
Year Range: 1800 - 2023
Total Records: ~224 years
Coverage: Complete historical series
Data Quality: ONS authoritative source
```

**Key Variables:**

#### Government Revenues
- **Income Tax** (from introduction in 1842)
- **National Insurance Contributions**
- **VAT** (Purchase Tax pre-1973)
- **Corporation Tax** (Profits taxes pre-1966)
- **Business Rates**
- **Capital Gains Tax**
- **Inheritance Tax** (Death Duties historically)
- **Custom & Excise Duties**
- **Stamp Duties**
- **Petroleum Revenue Tax** (North Sea oil era)
- **Council Tax** (Community Charge/Domestic Rates pre-1993)

#### Government Expenditure
- **Total Central Government Spending**
- **Current Spending vs. Capital Investment**
- **Defence**
- **Health (NHS from 1948)**
- **Social Security** (Pensions vs. Non-Pensioners breakdown)
- **Education**
- **Debt Interest**

#### Fiscal Balance
- **Public Sector Net Borrowing (PSNB)** - Annual deficit/surplus
- **Public Sector Net Debt (PSND)** - Total accumulated debt
- **Nominal GDP** - Economic output for context
- **GDP (March-Centred)** - Alternative measure

#### Price Index
- **Retail Price Index (RPI): 1800-2024** - Base: Jan 1974 = 100

---

## 📁 Data Sources

| Source | Years | Type | Location |
|--------|-------|------|----------|
| PublicFinances1800-2023.csv | 1800-2023 | Full public finance series | `downloaded_sourcefiles/` |
| PublicFinances1800-2023.xlsx | 1800-2023 | Excel version with notes | `downloaded_sourcefiles/` |
| Historical-public-finances-database.xlsx | 1800-2023 | ONS master database | `downloaded_sourcefiles/` |
| pusf.csv | Various | Supplementary data | `downloaded_sourcefiles/` |
| Inflation-RPI-series-191125.xls | 1800-2024 | RPI long series | `downloaded_sourcefiles/` |

**Primary Source:** Office for National Statistics (ONS)  
**Attribution:** UK Public Sector Finances - Historical Series

---

## 📈 Usage Examples

### Load and explore the data

```python
import pandas as pd
from pathlib import Path

# Load public finances data
csv_path = Path('data_sources/economic/development_code/downloaded_sourcefiles/PublicFinances1800-2023.csv')
df = pd.read_csv(csv_path, skiprows=4)  # Skip header metadata rows

# Clean up - remove empty trailing rows
df = df.dropna(subset=['Source dataset ID'])

# Rename year column for clarity
df = df.rename(columns={'Source dataset ID': 'year'})

# Convert year to integer
df['year'] = df['year'].astype(int)

print(f"Year range: {df['year'].min()} - {df['year'].max()}")
print(f"Total records: {len(df)}")
```

### Analyze debt-to-GDP ratio over time

```python
# Calculate debt/GDP percentage
df['debt_to_gdp'] = (df['Public sector net debt (PSND)2'] / df['Nominal GDP (£m)3']) * 100

# Key periods
pre_ww1 = df[(df['year'] >= 1800) & (df['year'] < 1914)]['debt_to_gdp'].mean()
interwar = df[(df['year'] >= 1919) & (df['year'] <= 1939)]['debt_to_gdp'].mean()
post_ww2 = df[(df['year'] >= 1946) & (df['year'] < 1980)]['debt_to_gdp'].mean()
modern = df[df['year'] >= 2000]['debt_to_gdp'].mean()

print(f"Pre-WW1 debt/GDP: {pre_ww1:.1f}%")
print(f"Interwar debt/GDP: {interwar:.1f}%")
print(f"Post-WW2 debt/GDP: {post_ww2:.1f}%")
print(f"Modern era debt/GDP: {modern:.1f}%")
```

### Compare revenue sources

```python
# Extract key revenue columns (adjust column names as needed based on actual file)
revenue_cols = [
    'LIBR-MS62',  # Income tax
    'AIIH',       # National Insurance
    'NZGF',       # VAT
    'CUKY',       # Corporation tax
]

# Calculate total revenue and composition
df['total_revenue'] = df[revenue_cols].sum(axis=1)

for col in revenue_cols:
    df[f'{col}_share'] = (df[col] / df['total_revenue']) * 100

# Modern era composition (2000+)
modern = df[df['year'] >= 2000]
print("Modern revenue composition (2000+):")
for col in revenue_cols:
    avg_share = modern[f'{col}_share'].mean()
    print(f"  {col}: {avg_share:.1f}%")
```

### Adjust for inflation using RPI

```python
# Use RPI to convert historical values to 2023 prices
# RPI base: Jan 1974 = 100
df['rpi'] = df['MM23']  # RPI column

# Calculate real GDP (2023 prices)
rpi_2023 = df[df['year'] == 2023]['rpi'].iloc[0]
df['real_gdp_2023'] = df['Nominal GDP (£m)3'] * (rpi_2023 / df['rpi'])

# Plot real GDP over time
import matplotlib.pyplot as plt
plt.figure(figsize=(14, 6))
plt.plot(df['year'], df['real_gdp_2023'] / 1000, linewidth=2)
plt.title('UK Real GDP 1800-2023 (2023 prices)')
plt.xlabel('Year')
plt.ylabel('GDP (£ billions, 2023 prices)')
plt.grid(True, alpha=0.3)
plt.show()
```

---

## 🔍 Historical Context & Data Notes

### Key Historical Events Visible in Data

1. **Napoleonic Wars (1803-1815):** Introduction of income tax, high debt levels
2. **Victorian Era (1837-1901):** Debt reduction, free trade policies
3. **World War I (1914-1918):** Massive borrowing, spending spike
4. **Great Depression (1929-1939):** Revenue collapse, rising unemployment costs
5. **World War II (1939-1945):** Peak debt/GDP ratio (~250%)
6. **Post-War Period (1945-1979):** Welfare state expansion, NHS creation (1948)
7. **Thatcher Era (1979-1990):** Privatization, tax reforms
8. **Financial Crisis (2007-2009):** Bank bailouts, austerity debates
9. **COVID-19 Pandemic (2020-2021):** Furlough schemes, health spending surge

### Data Quality Notes

- **Pre-1900:** Limited granularity, some series not collected
- **1900-1948:** Increasing detail, still gaps in some categories
- **1948+:** NHS creation adds health spending clarity
- **1966+:** Corporation tax introduced (profits taxes prior)
- **1973+:** VAT replaces Purchase Tax (EEC membership)
- **1993+:** Council Tax replaces Community Charge

### Missing Data Patterns

Some tax categories don't exist before their introduction:
- **Income Tax:** Starts 1842 (temporary introduction 1799-1802)
- **National Insurance:** Starts 1911
- **Corporation Tax:** Starts 1966 (profits taxes before)
- **VAT:** Starts 1973 (Purchase Tax before)
- **Petroleum Revenue Tax:** 1975-2016 (North Sea oil)
- **Energy Profits Levy:** 2022+ (windfall tax on oil/gas)

---

## 🚀 Getting Started

### Prerequisites

```powershell
# Activate project virtual environment
& H:/VScode/UK_Socio_Economic_Modelling/.venv/Scripts/Activate.ps1

# Install dependencies (if not already)
pip install pandas numpy matplotlib openpyxl xlrd
```

### Quick Start Script

Location: `data_sources/economic/development_code/`

```powershell
cd data_sources/economic/development_code

# Examine data structure
python examine_public_finances.py
```

---

## 📁 Folder Structure

```
data_sources/economic/
├── README.md                          # This file
├── development_code/                  # Analysis scripts
│   ├── downloaded_sourcefiles/        # Original ONS data (gitignored)
│   │   ├── PublicFinances1800-2023.csv
│   │   ├── PublicFinances1800-2023.xlsx
│   │   ├── Historical-public-finances-database.xlsx
│   │   ├── pusf.csv
│   │   └── Inflation-RPI-series-191125.xls
│   └── examine_public_finances.py     # Data exploration script
└── (generated outputs will go here)
```

---

## 🔗 Integration Opportunities

### Cross-Dataset Analysis

Combine with other data sources in this repository:

1. **Mortality Stats (1901-2025):**
   - Correlate NHS spending with mortality improvements
   - Analyze war periods (spending + excess deaths)
   - Social Security vs. pensioner mortality

2. **Housing Pressure:**
   - Government investment in housing
   - Planning revenue (development taxes)

3. **Political Context:**
   - Election cycles vs. spending patterns
   - Party in power vs. tax/spend mix

### Potential Research Questions

- Does higher health spending correlate with lower mortality?
- How did wars affect fiscal position and population health?
- What's the relationship between education spending and long-term growth?
- How has the tax mix shifted over 200+ years?
- Is there a "sustainable" debt-to-GDP ratio based on historical data?

---

## 📝 Notes

- All monetary values are **nominal** (not adjusted for inflation) unless stated otherwise
- Use the RPI series to convert to real terms
- Data represents **UK public sector** (central + local government + public corporations)
- Some historical data uses **financial years** (April-March), others use **calendar years**
- **Scotland and Northern Ireland** data integrated differently across periods (check source notes)
- **Brexit (2020)** and **COVID-19 (2020-21)** create structural breaks in recent data

---

## 🔄 Updates

| Date | Change | Author |
|------|--------|--------|
| 2025-12-23 | Initial README created | GitHub Copilot |
| 2025-12-23 | Organized source files into development_code structure | GitHub Copilot |

---

## 📚 References

- **ONS Public Sector Finances:** https://www.ons.gov.uk/economy/governmentpublicsectorandtaxes/publicsectorfinance
- **Historical Series:** https://www.ons.gov.uk/economy/governmentpublicsectorandtaxes/publicsectorfinance/datasets/publicsectorfinanceshistoricalcompiledseriesbrowsablexlsxhistoricseries
- **UK Data Service:** Historical government finance statistics
- **Bank of England:** Historical inflation and interest rate data

---

**For questions or contributions, see:** [CONTRIBUTING.md](../../CONTRIBUTING.md)
