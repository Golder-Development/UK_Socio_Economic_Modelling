"""
Integrate population data with economic_data_combined_1800_2024.csv

Steps:
1. Load population data (1901-2016) and aggregate by year
2. Load economic data (1801-2024)
3. Merge on date_period (year)
4. Create per-capita measures for key economic indicators
"""

import pandas as pd
import numpy as np
from pathlib import Path


def integrate_population_data():
    # Define paths
    economic_file = Path(__file__).parent / 'economic_data_combined_1800_2024.csv'
    population_file = (
        Path(__file__).parent.parent.parent / 'population' / 'development_code' /
        'downloaded_sourcefiles' / 'combined_population_data.csv'
    )
    output_file = Path(__file__).parent / 'economic_data_with_population_1800_2024.csv'

    print("Loading datasets...")

    # Load economic data
    econ_df = pd.read_csv(economic_file)
    print("\nEconomic data:")
    print(f"  Shape: {econ_df.shape}")
    print(f"  Date range: {econ_df['date_period'].min()} - {econ_df['date_period'].max()}")

    # Load population data
    pop_df = pd.read_csv(population_file)
    print("\nPopulation data (raw):")
    print(f"  Shape: {pop_df.shape}")
    print(f"  Year range: {pop_df['YR'].min()} - {pop_df['YR'].max()}")

    # Aggregate population by year (sum across all age groups and sexes)
    pop_by_year = pop_df.groupby('YR')['POP'].sum().reset_index()
    pop_by_year.columns = ['date_period', 'population']

    print("\nAggregated population by year:")
    print(f"  Shape: {pop_by_year.shape}")
    print("  Sample:")
    print(pop_by_year.head(10))

    # Merge with economic data
    merged_df = econ_df.merge(pop_by_year, on='date_period', how='left')

    print("\nMerged data:")
    print(f"  Shape: {merged_df.shape}")
    pop_count = merged_df['population'].notna().sum()
    pop_pct = pop_count / len(merged_df) * 100
    print(f"  Population coverage: {pop_count} / {len(merged_df)} rows ({pop_pct:.1f}%)")
    pop_data = merged_df[merged_df['population'].notna()]
    pop_min = pop_data['date_period'].min()
    pop_max = pop_data['date_period'].max()
    print(f"  Population available for years: {pop_min:.0f} - {pop_max:.0f}")

    # Create per-capita measures for monetary values
    # Identify measures that are in £m (millions) or similar monetary units
    monetary_categories = ['Tax Receipts', 'Government Spending', 'Fiscal Position']

    # Create per-capita column (value per person, converted from millions)
    # value is in £m, population is in persons
    # per_capita = (value * 1,000,000) / population
    merged_df['value_per_capita'] = np.where(
        (merged_df['value'].notna()) & (merged_df['population'].notna()) &
        (merged_df['category'].isin(monetary_categories)),
        (merged_df['value'] * 1_000_000) / merged_df['population'],
        np.nan
    )

    # Sort by date_period and measure for consistency
    merged_df = merged_df.sort_values(['date_period', 'measure']).reset_index(drop=True)

    # Save to CSV
    merged_df.to_csv(output_file, index=False)

    print("\n✓ Successfully integrated population data")
    print(f"Output: {output_file}")
    print(f"Shape: {merged_df.shape}")

    print("\nColumn summary:")
    for col in merged_df.columns:
        non_null = merged_df[col].notna().sum()
        print(f"  {col}: {non_null} non-null ({non_null / len(merged_df) * 100:.1f}%)")

    print("\nPer-capita measures created:")
    per_capita_available = merged_df['value_per_capita'].notna().sum()
    print(f"  Total per-capita values: {per_capita_available}")
    print(f"  Coverage: {per_capita_available / len(merged_df) * 100:.1f}% of all rows")

    # Show sample per-capita calculations
    print("\nSample per-capita calculations (most recent data):")
    sample = merged_df[
        (merged_df['value_per_capita'].notna()) &
        (merged_df['date_period'] >= 2015)
    ].sort_values('date_period', ascending=False).head(10)

    for _, row in sample.iterrows():
        print(f"  {row['date_period']:.0f} | {row['measure'][:50]:50} | £{row['value_per_capita']:.2f} per capita")

    # Category breakdown with population data
    print("\nCategory breakdown (with per-capita availability):")
    category_stats = merged_df.groupby('category').agg({
        'value': 'count',
        'population': lambda x: x.notna().sum(),
        'value_per_capita': lambda x: x.notna().sum()
    }).round(0)
    category_stats.columns = ['Total rows', 'With population', 'With per-capita']
    print(category_stats)

    return merged_df


if __name__ == "__main__":
    merged_df = integrate_population_data()
