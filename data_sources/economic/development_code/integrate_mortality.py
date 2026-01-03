"""
Integrate L1 mortality data with economic_data_with_population_1800_2024.csv

The L1 mortality data uses 10 socio-economic classification categories:
- L1_01: Infectious and Communicable Diseases
- L1_02: Maternal and Early-Life Mortality
- L1_03: Congenital and Developmental Conditions
- L1_04: Later-Life Mortality
- L1_05: Chronic Non-Communicable Diseases
- L1_06: Respiratory and Environmental Disease
- L1_07: Injury and Accidental Harm
- L1_08: Violence and Conflict
- L1_09: Self-Harm and Substance Use
- L1_10: Ill-Defined, Administrative, and Other Causes

Steps:
1. Load mortality L1 data (1901-2017) and aggregate by year and L1 category
2. Load economic+population data (1801-2024)
3. Merge on date_period (year)
4. Pivot mortality categories to create columns for each L1 category
"""

import pandas as pd
import numpy as np
import zipfile
from pathlib import Path


def integrate_mortality_data():
    # Define paths
    economic_pop_file = Path(__file__).parent / 'economic_data_with_population_1800_2024.csv'
    mortality_zip = (
        Path(__file__).parent.parent.parent / 'mortality_stats' /
        'uk_mortality_by_cause_1901_onwards_l1.zip'
    )
    output_file = Path(__file__).parent / 'economic_data_complete_1800_2024.csv'

    print("Loading datasets...")

    # Load economic+population data
    econ_df = pd.read_csv(economic_pop_file)
    print("\nEconomic+Population data:")
    print(f"  Shape: {econ_df.shape}")
    print(f"  Date range: {econ_df['date_period'].min()} - {econ_df['date_period'].max()}")

    # Load mortality L1 data from zip
    print(f"\nLoading mortality L1 data from: {mortality_zip}")
    with zipfile.ZipFile(mortality_zip, 'r') as z:
        csv_file = [n for n in z.namelist() if n.endswith('.csv')][0]
        with z.open(csv_file) as f:
            mort_df = pd.read_csv(f, low_memory=False)

    print("\nMortality L1 data (raw):")
    print(f"  Shape: {mort_df.shape}")
    print(f"  Year range: {mort_df['year'].min()} - {mort_df['year'].max()}")
    print(f"  L1 categories: {mort_df['harmonized_category_code'].nunique()}")

    # Aggregate mortality by year and L1 category
    mort_agg = mort_df.groupby(
        ['year', 'harmonized_category_code', 'harmonized_category_name']
    )['deaths'].sum().reset_index()

    print("\nAggregated mortality by year and L1 category:")
    print(f"  Shape: {mort_agg.shape}")
    print("  Sample:")
    print(mort_agg.head(10))

    # Pivot mortality data to create columns for each L1 category
    mort_pivot = mort_agg.pivot(
        index='year',
        columns='harmonized_category_code',
        values='deaths'
    ).reset_index()

    # Rename year column to match economic data
    mort_pivot.rename(columns={'year': 'date_period'}, inplace=True)

    # Create more readable column names
    l1_name_map = {
        'L1_01': 'mortality_L1_01_infectious',
        'L1_02': 'mortality_L1_02_maternal_early_life',
        'L1_03': 'mortality_L1_03_congenital',
        'L1_04': 'mortality_L1_04_later_life',
        'L1_05': 'mortality_L1_05_chronic_noncommunicable',
        'L1_06': 'mortality_L1_06_respiratory_environmental',
        'L1_07': 'mortality_L1_07_injury_accidental',
        'L1_08': 'mortality_L1_08_violence_conflict',
        'L1_09': 'mortality_L1_09_selfharm_substance',
        'L1_10': 'mortality_L1_10_ill_defined_other'
    }
    mort_pivot.rename(columns=l1_name_map, inplace=True)

    # Calculate total mortality
    mort_cols = [col for col in mort_pivot.columns if col.startswith('mortality_L1_')]
    mort_pivot['mortality_total'] = mort_pivot[mort_cols].sum(axis=1)

    print("\nPivoted mortality data:")
    print(f"  Shape: {mort_pivot.shape}")
    print(f"  Columns: {mort_pivot.columns.tolist()}")
    print("  Sample:")
    print(mort_pivot.head(10))

    # Merge with economic data
    merged_df = econ_df.merge(mort_pivot, on='date_period', how='left')

    print("\nMerged data:")
    print(f"  Shape: {merged_df.shape}")
    mort_count = merged_df['mortality_total'].notna().sum()
    mort_pct = mort_count / len(merged_df) * 100
    print(f"  Mortality coverage: {mort_count} / {len(merged_df)} rows ({mort_pct:.1f}%)")
    mort_data = merged_df[merged_df['mortality_total'].notna()]
    mort_min = mort_data['date_period'].min()
    mort_max = mort_data['date_period'].max()
    print(f"  Mortality available for years: {mort_min:.0f} - {mort_max:.0f}")

    # Create mortality per capita measures (deaths per 100,000 population)
    if 'population' in merged_df.columns:
        for col in mort_cols + ['mortality_total']:
            per_capita_col = col.replace('mortality_', 'mortality_rate_per_100k_')
            merged_df[per_capita_col] = np.where(
                (merged_df[col].notna()) & (merged_df['population'].notna()),
                (merged_df[col] / merged_df['population']) * 100_000,
                np.nan
            )

        print("\nMortality rates per 100k population created:")
        rate_cols = [col for col in merged_df.columns if 'mortality_rate_per_100k' in col]
        rate_available = merged_df[rate_cols[0]].notna().sum()
        print(f"  Total mortality rate values: {rate_available}")
        print(f"  Coverage: {rate_available / len(merged_df) * 100:.1f}% of all rows")

    # Sort by date_period and measure for consistency
    merged_df = merged_df.sort_values(['date_period', 'measure']).reset_index(drop=True)

    # Save to CSV
    merged_df.to_csv(output_file, index=False)

    print("\n✓ Successfully integrated mortality L1 data")
    print(f"Output: {output_file}")
    print(f"Shape: {merged_df.shape}")

    print("\nColumn summary:")
    for col in merged_df.columns:
        non_null = merged_df[col].notna().sum()
        print(f"  {col}: {non_null} non-null ({non_null / len(merged_df) * 100:.1f}%)")

    # Show sample mortality statistics for a recent year
    print("\nSample mortality statistics (2016):")
    sample_2016 = merged_df[merged_df['date_period'] == 2016].iloc[0]
    if 'mortality_total' in sample_2016 and pd.notna(sample_2016['mortality_total']):
        print(f"  Total deaths: {sample_2016['mortality_total']:.0f}")
        print(f"  Population: {sample_2016['population']:.0f}")
        print(f"  Crude death rate: {sample_2016['mortality_rate_per_100k_total']:.1f} per 100,000")

        print("\n  Deaths by L1 category (2016):")
        for col in mort_cols:
            if col in sample_2016 and pd.notna(sample_2016[col]):
                category_name = col.replace('mortality_L1_', '').replace('_', ' ').title()
                print(f"    {category_name}: {sample_2016[col]:.0f}")

    return merged_df


if __name__ == "__main__":
    merged_df = integrate_mortality_data()
