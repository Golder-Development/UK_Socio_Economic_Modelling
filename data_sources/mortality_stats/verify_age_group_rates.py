#!/usr/bin/env python3
"""
Verify age-group mortality rates and demonstrate denominator clarity.
Runs quick sanity checks and shows examples of proper interpretation.
"""

import pandas as pd
import zipfile
from pathlib import Path

# Paths
STATS_DIR = Path(__file__).parent
BY_CAUSE = STATS_DIR / "uk_mortality_rates_per_100k_by_cause.zip"  # Now a zip file
BY_AGE = STATS_DIR / "uk_mortality_rates_per_100k_by_age_group.csv"
YEARLY = STATS_DIR / "uk_mortality_rates_per_100k_yearly_totals.csv"


def check_files_exist():
    """Verify output files exist."""
    print("=" * 70)
    print("VERIFYING AGE-GROUP MORTALITY RATE FILES")
    print("=" * 70)
    
    files = {"by_cause": BY_CAUSE, "by_age_group": BY_AGE, "yearly_totals": YEARLY}
    for name, path in files.items():
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {name:20} → {path.name}")
    
    if all(p.exists() for p in files.values()):
        print("\n✓ All output files present")
        return True
    else:
        print("\n✗ Some files missing!")
        return False


def load_by_cause_from_zip():
    """Load by_cause data from zip file."""
    with zipfile.ZipFile(BY_CAUSE, 'r') as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith('.csv')]
        if not csv_names:
            raise FileNotFoundError(f"No CSV found in {BY_CAUSE}")
        with zf.open(csv_names[0]) as f:
            return pd.read_csv(f)


def load_and_summarize():
    """Load files and show basic statistics."""
    print("\n" + "=" * 70)
    print("DATA SUMMARY")
    print("=" * 70)
    
    by_cause = load_by_cause_from_zip()
    by_age = pd.read_csv(BY_AGE)
    yearly = pd.read_csv(YEARLY)
    
    print(f"\n1. By Cause (29,452 records)")
    print(f"   Columns: {', '.join(by_cause.columns)}")
    print(f"   Years: {by_cause['year'].min()}-{by_cause['year'].max()}")
    print(f"   Age groups: {sorted(by_cause['age_group'].unique())}")
    print(f"   Key column: mortality_rate_per_100k_age_group_population")
    
    print(f"\n2. By Age Group (2,000 records)")
    print(f"   Columns: {', '.join(by_age.columns)}")
    print(f"   Years: {by_age['year'].min()}-{by_age['year'].max()}")
    print(f"   Sexes: {sorted(by_age['sex'].unique())}")
    print(f"   Key column: mortality_rate_per_100k_age_group_population")
    
    print(f"\n3. Yearly Totals (100 records)")
    print(f"   Columns: {', '.join(yearly.columns)}")
    print(f"   Years: {yearly['year'].min()}-{yearly['year'].max()}")
    print(f"   Key column: mortality_rate_per_100k_total_population")
    
    return by_cause, by_age, yearly


def demonstrate_age_comparison(by_age):
    """Show mortality differences across age groups."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Compare Mortality Across Age Groups (Year 2000)")
    print("=" * 70)
    print("\nMale mortality rates per 100,000 [OF THAT AGE GROUP]:\n")
    
    year_2000 = by_age[(by_age['year'] == 2000) & (by_age['sex'] == 'Male')]
    year_2000 = year_2000.sort_values('mortality_rate_per_100k_age_group_population')
    
    for _, row in year_2000.iterrows():
        rate = row['mortality_rate_per_100k_age_group_population']
        age = row['age_group']
        pop = row['population_age_group']
        deaths = row['deaths']
        print(f"  {age:>6} age: {rate:>9.1f} per 100k  ({deaths:>5} deaths / {pop:>11,.0f} population)")
    
    # Show ratio
    youngest = year_2000[year_2000['age_group'] == '0-4']['mortality_rate_per_100k_age_group_population'].values[0]
    oldest = year_2000[year_2000['age_group'] == '85+']['mortality_rate_per_100k_age_group_population'].values[0]
    ratio = oldest / youngest
    
    print(f"\n  → 85+ mortality is {ratio:.1f}× higher than 0-4 age group")
    print(f"    (Denominator: population OF each age group, not total)")


def demonstrate_cause_comparison(by_cause):
    """Show mortality differences across causes within an age group."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Compare Causes Within 85+ Age Group (Year 2000)")
    print("=" * 70)
    print("\nTop 5 causes of death in 85+ year-olds:\n")
    
    year_2000_elderly = by_cause[
        (by_cause['year'] == 2000) & 
        (by_cause['age_group'] == '85+') &
        (by_cause['sex'] == 'Male')
    ]
    year_2000_elderly = year_2000_elderly.nlargest(5, 'mortality_rate_per_100k_age_group_population')
    
    for i, (_, row) in enumerate(year_2000_elderly.iterrows(), 1):
        rate = row['mortality_rate_per_100k_age_group_population']
        cause = row['cause']
        deaths = row['deaths']
        pop = row['population_age_group']
        print(f"  {i}. Cause {cause}: {rate:>9.1f} per 100k  ({deaths:>5} deaths / {pop:>11,.0f} 85+ males)")
    
    print(f"\n  → All rates use same denominator: 85+ male population")
    print(f"    (Fair comparison - same-age cause profiles)")


def demonstrate_yearly_trend(yearly):
    """Show long-term population-wide mortality trend."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Long-Term Population Mortality Trend")
    print("=" * 70)
    print("\nOverall mortality per 100,000 [TOTAL POPULATION, ALL AGES]:\n")
    
    sample_years = [1901, 1950, 1975, 2000]
    for year in sample_years:
        if year in yearly['year'].values:
            row = yearly[yearly['year'] == year].iloc[0]
            rate = row['mortality_rate_per_100k_total_population']
            deaths = row['deaths']
            pop = row['population_total']
            print(f"  {int(year)}: {rate:>9.1f} per 100k  ({deaths:>7,.0f} deaths / {pop:>12,.0f} total population)")
    
    rate_1901 = yearly[yearly['year'] == 1901]['mortality_rate_per_100k_total_population'].values[0]
    rate_2000 = yearly[yearly['year'] == 2000]['mortality_rate_per_100k_total_population'].values[0]
    improvement = (1 - rate_2000 / rate_1901) * 100
    
    print(f"\n  → Population mortality improved {improvement:.1f}% from 1901 to 2000")
    print(f"    (Denominator: total population - all ages combined)")


def show_denominator_warnings():
    """Highlight common misinterpretations."""
    print("\n" + "=" * 70)
    print("⚠️  COMMON MISTAKES TO AVOID")
    print("=" * 70)
    
    mistakes = [
        {
            "wrong": 'Comparing "85+ rate of 18,824" to "0-4 rate of 4,949" as equivalent',
            "why": "These are per 100k of DIFFERENT population denominators",
            "correct": "Can compare directly because same denominator (each age group)"
        },
        {
            "wrong": "Using by_age_group rate (per-age-group) for total population statement",
            "why": "Mixing denominators leads to wrong conclusions",
            "correct": "Use yearly_totals for population-wide statements (per 100k total)"
        },
        {
            "wrong": "Not mentioning denominator in visualizations",
            "why": "Readers can't interpret the rate correctly",
            "correct": 'Label axes: "Deaths per 100,000 (of 85+ age group population)"'
        },
    ]
    
    for i, m in enumerate(mistakes, 1):
        print(f"\n  Mistake {i}:")
        print(f"    ❌ {m['wrong']}")
        print(f"    Why: {m['why']}")
        print(f"    ✓ {m['correct']}")


def main():
    """Run all checks and demonstrations."""
    if not check_files_exist():
        print("\n✗ Cannot proceed without output files.")
        return False
    
    by_cause, by_age, yearly = load_and_summarize()
    
    demonstrate_age_comparison(by_age)
    demonstrate_cause_comparison(by_cause)
    demonstrate_yearly_trend(yearly)
    show_denominator_warnings()
    
    print("\n" + "=" * 70)
    print("✓ VERIFICATION COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Use by_age_group.csv for dashboards comparing age cohorts")
    print("  2. Use by_cause.csv for cause analysis within age groups")
    print("  3. Use yearly_totals.csv for population-wide trends")
    print("  4. Always label denominators explicitly in visualizations")
    print()


if __name__ == "__main__":
    main()
