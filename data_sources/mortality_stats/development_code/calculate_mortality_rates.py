"""
Calculate UK Mortality Rates per 100,000 Population by Cause
============================================================

Combines:
- uk_mortality_comprehensive_1901_2019.csv (death counts by cause, sex, age, year)
- combined_population_data.csv (population by sex, age, year)

Outputs:
- uk_mortality_rates_per_100k_by_cause.csv
- uk_mortality_rates_per_100k_yearly_totals.csv
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MORTALITY_DIR = Path(__file__).parent
POPULATION_DIR = Path(__file__).parent.parent / "population"


def load_data():
    """Load mortality and population data"""
    logger.info("=" * 70)
    logger.info("LOADING DATA")
    logger.info("=" * 70)
    
    # Load mortality
    mortality_file = MORTALITY_DIR / "uk_mortality_comprehensive_1901_2019.csv"
    logger.info(f"Loading mortality: {mortality_file.name}")
    mortality = pd.read_csv(mortality_file)
    logger.info(f"  ✓ {len(mortality):,} records ({mortality['year'].min():.0f}-{mortality['year'].max():.0f})")
    
    # Load population
    pop_file = POPULATION_DIR / "combined_population_data.csv"
    logger.info(f"Loading population: {pop_file.name}")
    population = pd.read_csv(pop_file)
    logger.info(f"  ✓ {len(population):,} records ({population['YR'].min()}-{population['YR'].max()})")
    
    return mortality, population


def prepare_data(mortality, population):
    """Standardize and prepare data for merging"""
    logger.info("\n" + "=" * 70)
    logger.info("PREPARING DATA")
    logger.info("=" * 70)
    
    # Standardize mortality
    logger.info("Standardizing mortality data...")
    mort_std = mortality.copy()
    mort_std.columns = mort_std.columns.str.lower()
    mort_std = mort_std.rename(columns={'year': 'YR'})
    
    # Standardize sex: 1=Male, 2=Female
    mort_std['sex'] = mort_std['sex'].map({'Male': 1, 'Female': 2}).fillna(mort_std['sex'])
    mort_std['sex'] = pd.to_numeric(mort_std['sex'], errors='coerce')
    mort_std = mort_std[mort_std['sex'].notna()]
    mort_std['sex'] = mort_std['sex'].astype('Int64')
    
    logger.info(f"  Mortality records: {len(mort_std):,}")
    
    # Show year coverage
    mort_years = sorted(mort_std['YR'].unique())
    logger.info(f"  Year coverage: {mort_years[0]:.0f}-{mort_years[-1]:.0f} ({len(mort_years)} years with data)")
    missing_years = [y for y in range(int(mort_years[0]), int(mort_years[-1])+1) if y not in mort_years]
    if missing_years:
        logger.info(f"  Missing years (1997-2000): {missing_years}")
    
    # Standardize population
    logger.info("Standardizing population data...")
    pop_std = population.copy()
    pop_std = pop_std[['YR', 'SEX', 'AGE', 'POP']].copy()
    
    # Fix AGE column: use Agegroup where AGE is NaN (for years 2001+)
    if 'Agegroup' in population.columns:
        pop_std['AGE'] = population['AGE'].fillna(population['Agegroup'])
    
    pop_std.columns = ['YR', 'sex', 'age', 'population']
    pop_std['population'] = pd.to_numeric(pop_std['population'], errors='coerce')
    pop_std = pop_std.dropna(subset=['population', 'age'])
    
    pop_years = sorted(pop_std['YR'].unique())
    logger.info(f"  Population records: {len(pop_std):,}")
    logger.info(f"  Year coverage: {pop_years[0]}-{pop_years[-1]} ({len(pop_years)} continuous years)")
    
    return mort_std, pop_std


def aggregate_by_dimensions(mort_std, pop_std):
    """Aggregate mortality and population by available dimensions"""
    logger.info("\n" + "=" * 70)
    logger.info("AGGREGATING DATA")
    logger.info("=" * 70)
    
    # For mortality: aggregate by year, cause, sex, age
    logger.info("Aggregating mortality by year, cause, sex, age...")
    mort_agg = mort_std.groupby(['YR', 'cause', 'sex', 'age'], as_index=False, dropna=False)['deaths'].sum()
    mort_agg = mort_agg[mort_agg['deaths'] > 0]
    logger.info(f"  ✓ {len(mort_agg):,} distinct cause categories")
    
    # For population: aggregate by year, sex, age
    logger.info("Aggregating population by year, sex, age...")
    pop_agg = pop_std.groupby(['YR', 'sex', 'age'], as_index=False)['population'].sum()
    logger.info(f"  ✓ {len(pop_agg):,} age/sex combinations")
    
    return mort_agg, pop_agg


def calculate_mortality_rates(mort_agg, pop_agg):
    """Calculate mortality rates per 100,000 population"""
    logger.info("\n" + "=" * 70)
    logger.info("CALCULATING MORTALITY RATES")
    logger.info("=" * 70)
    
    logger.info("Merging mortality and population data...")
    
    # Merge on year, sex, age
    merged = mort_agg.merge(
        pop_agg,
        on=['YR', 'sex', 'age'],
        how='left'
    )
    
    # Check merge quality
    unmatched = merged[merged['population'].isna()]
    logger.info(f"  Matched records: {len(merged[merged['population'].notna()]):,}")
    if len(unmatched) > 0:
        logger.warning(f"  Unmatched mortality records (no population): {len(unmatched):,}")
        logger.warning("  (This is expected for rare age/sex combinations)")
    
    # Calculate rate per 100,000
    logger.info("Calculating rates per 100,000 population...")
    merged['mortality_rate_per_100k'] = np.where(
        merged['population'] > 0,
        (merged['deaths'] / merged['population']) * 100000,
        np.nan
    )
    
    # Remove records without population
    merged_with_rates = merged.dropna(subset=['mortality_rate_per_100k'])
    logger.info(f"  ✓ {len(merged_with_rates):,} records with calculated rates")
    
    # Standardize sex names
    sex_map = {1: 'Male', 2: 'Female', 1.0: 'Male', 2.0: 'Female'}
    merged_with_rates['sex'] = merged_with_rates['sex'].map(sex_map).fillna(merged_with_rates['sex'])
    
    # Select final columns
    rates = merged_with_rates[[
        'YR', 'cause', 'sex', 'age', 'deaths', 'population', 'mortality_rate_per_100k'
    ]].copy()
    
    rates = rates.rename(columns={'YR': 'year'})
    rates = rates.sort_values(['year', 'cause', 'sex', 'age'])
    
    return rates


def calculate_yearly_totals(rates):
    """Calculate yearly mortality rates (all causes combined)"""
    logger.info("\nCalculating yearly total rates...")
    
    # Aggregate deaths and population by year (across all causes, sexes, ages)
    yearly = rates.groupby('year', as_index=False).agg({
        'deaths': 'sum',
        'population': 'sum'
    })
    
    yearly['mortality_rate_per_100k'] = (yearly['deaths'] / yearly['population']) * 100000
    
    logger.info(f"  ✓ {len(yearly):,} yearly records")
    
    return yearly


def save_outputs(rates, yearly):
    """Save output files"""
    logger.info("\n" + "=" * 70)
    logger.info("SAVING OUTPUTS")
    logger.info("=" * 70)
    
    out_dir = MORTALITY_DIR
    
    # Save detailed rates by cause
    out_rates = out_dir / "uk_mortality_rates_per_100k_by_cause.csv"
    rates.to_csv(out_rates, index=False)
    logger.info(f"✓ Saved: {out_rates.name}")
    logger.info(f"  {len(rates):,} records")
    logger.info(f"  Columns: {list(rates.columns)}")
    
    # Save yearly totals
    out_yearly = out_dir / "uk_mortality_rates_per_100k_yearly_totals.csv"
    yearly.to_csv(out_yearly, index=False)
    logger.info(f"✓ Saved: {out_yearly.name}")
    logger.info(f"  {len(yearly):,} records")
    
    return out_rates, out_yearly


def print_summary(rates, yearly):
    """Print summary statistics"""
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 70)
    
    logger.info("\nMortality Rates Overview:")
    logger.info(f"  Time period: {rates['year'].min():.0f} - {rates['year'].max():.0f}")
    logger.info(f"  Distinct causes: {rates['cause'].nunique()}")
    logger.info(f"  Years with data: {rates['year'].nunique()}")
    
    logger.info("\nMortality Rate Statistics (per 100,000):")
    logger.info(f"  Mean: {rates['mortality_rate_per_100k'].mean():.2f}")
    logger.info(f"  Median: {rates['mortality_rate_per_100k'].median():.2f}")
    logger.info(f"  Min: {rates['mortality_rate_per_100k'].min():.2f}")
    logger.info(f"  Max: {rates['mortality_rate_per_100k'].max():.2f}")
    
    logger.info("\nYearly Total Mortality Rates (per 100,000):")
    for year in [yearly['year'].min(), yearly['year'].min() + 25, yearly['year'].max() - 25, yearly['year'].max()]:
        if year in yearly['year'].values:
            rate = yearly[yearly['year'] == year]['mortality_rate_per_100k'].values[0]
            logger.info(f"  {int(year)}: {rate:.1f} per 100,000")
    
    logger.info("\nTop 10 Causes by Total Deaths (2010-2017):")
    recent = rates[rates['year'] >= 2010]
    top_causes = recent.groupby('cause')['deaths'].sum().nlargest(10)
    for i, (cause, deaths) in enumerate(top_causes.items(), 1):
        logger.info(f"  {i}. {cause}: {deaths:,.0f} deaths")
    
    logger.info("\n" + "=" * 70)
    logger.info("✓ MORTALITY RATE CALCULATION COMPLETE!")
    logger.info("=" * 70)


def main():
    logger.info("\n")
    logger.info("╔" + "═" * 68 + "╗")
    logger.info("║" + " " * 68 + "║")
    logger.info("║" + "UK MORTALITY RATES PER 100,000 CALCULATOR".center(68) + "║")
    logger.info("║" + " " * 68 + "║")
    logger.info("╚" + "═" * 68 + "╝")
    logger.info("")
    
    try:
        # Load data
        mortality, population = load_data()
        
        # Prepare
        mort_std, pop_std = prepare_data(mortality, population)
        
        # Aggregate
        mort_agg, pop_agg = aggregate_by_dimensions(mort_std, pop_std)
        
        # Calculate rates
        rates = calculate_mortality_rates(mort_agg, pop_agg)
        yearly = calculate_yearly_totals(rates)
        
        # Save
        out_rates, out_yearly = save_outputs(rates, yearly)
        
        # Summary
        print_summary(rates, yearly)
        
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
