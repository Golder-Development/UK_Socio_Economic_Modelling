"""
Calculate UK mortality rates per 100,000 population by cause and age group.

Inputs:
- uk_mortality_by_cause_1901_onwards.zip (preferred; cause/sex/age ranges by year)
- uk_mortality_comprehensive_1901_2025_harmonized.csv (fallback if zip is missing)
- uk_population_harmonized_age_groups.csv (population by sex, harmonized age group, year)

Outputs (all explicitly labelled to avoid denominator confusion):
- uk_mortality_rates_per_100k_by_cause.zip (compressed)
    Contains: uk_mortality_rates_per_100k_by_cause.csv
    columns: year, cause, sex, age_group, deaths, population_age_group, mortality_rate_per_100k_age_group_population
- uk_mortality_rates_per_100k_by_age_group.csv
    columns: year, age_group, sex, deaths, population_age_group, mortality_rate_per_100k_age_group_population
- uk_mortality_rates_per_100k_yearly_totals.csv
    columns: year, deaths, population_total, mortality_rate_per_100k_total_population
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path

AGE_GROUP_ORDER = [
    "0-4",
    "5-14",
    "15-24",
    "25-34",
    "35-44",
    "45-54",
    "55-64",
    "65-74",
    "75-84",
    "85+",
]

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DEV_DIR = Path(__file__).parent
MORTALITY_DIR = DEV_DIR.parent  # data_sources/mortality_stats
ROOT_DIR = MORTALITY_DIR.parent  # data_sources
POPULATION_DIR = ROOT_DIR / "population"
POPULATION_FILE = POPULATION_DIR / "uk_population_harmonized_age_groups.csv"
PREFERRED_MORTALITY_FILE = MORTALITY_DIR / "uk_mortality_by_cause_1901_onwards.zip"
FALLBACK_MORTALITY_FILE = MORTALITY_DIR / "uk_mortality_comprehensive_1901_2025_harmonized.csv"


def resolve_mortality_file() -> Path:
    """Return the best available mortality source, preferring the extended zip."""
    for candidate in [PREFERRED_MORTALITY_FILE, FALLBACK_MORTALITY_FILE]:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "No mortality input found: expected uk_mortality_by_cause_1901_onwards.zip or uk_mortality_comprehensive_1901_2025_harmonized.csv"
    )


def standardize_age_group(age_value) -> str:
    """Map varied age strings into harmonized demographic bins used by population file."""
    if pd.isna(age_value):
        return "Unknown"

    age_str = str(age_value).strip()
    age_str = age_str.replace("T", "")  # remove potential leading T

    # Handle open-ended or special labels
    if age_str in {"<1", "00", "0"}:
        return "0-4"
    if age_str in {"85+", "80+", "90+"}:
        return "85+"

    # Extract starting age
    try:
        start_age = int(age_str.split("-")[0]) if "-" in age_str else int(age_str)
    except ValueError:
        return "Unknown"

    if start_age <= 4:
        return "0-4"
    if start_age <= 14:
        return "5-14"
    if start_age <= 24:
        return "15-24"
    if start_age <= 34:
        return "25-34"
    if start_age <= 44:
        return "35-44"
    if start_age <= 54:
        return "45-54"
    if start_age <= 64:
        return "55-64"
    if start_age <= 74:
        return "65-74"
    if start_age <= 84:
        return "75-84"
    return "85+"


def load_data():
    """Load mortality and population data"""
    logger.info("=" * 70)
    logger.info("LOADING DATA")
    logger.info("=" * 70)

    # Load mortality
    mortality_file = resolve_mortality_file()
    logger.info(f"Loading mortality: {mortality_file.name}")
    mortality = pd.read_csv(mortality_file)
    logger.info(
        f"  ✓ {len(mortality):,} records ({mortality['year'].min():.0f}-{mortality['year'].max():.0f})"
    )

    # Load population
    pop_file = POPULATION_FILE
    logger.info(f"Loading population: {pop_file.name}")
    population = pd.read_csv(pop_file)
    logger.info(
        f"  ✓ {len(population):,} records ({population['year'].min()}-{population['year'].max()})"
    )

    return mortality, population


def prepare_data(mortality, population):
    """Standardize and prepare data for merging (harmonized age groups + sex labels)."""
    logger.info("\n" + "=" * 70)
    logger.info("PREPARING DATA")
    logger.info("=" * 70)

    # Standardize mortality
    logger.info("Standardizing mortality data...")
    mort_std = mortality.copy()
    mort_std.columns = mort_std.columns.str.lower()
    mort_std = mort_std.rename(columns={"year": "YR"})
    mort_std["sex"] = mort_std["sex"].astype(str).str.strip().str.capitalize()
    mort_std["age_group"] = mort_std["age"].apply(standardize_age_group)
    mort_std = mort_std[mort_std["age_group"] != "Unknown"]

    logger.info(f"  Mortality records (harmonized ages): {len(mort_std):,}")

    # Year coverage
    mort_years = sorted(mort_std["YR"].unique())
    logger.info(
        f"  Year coverage: {mort_years[0]:.0f}-{mort_years[-1]:.0f} ({len(mort_years)} years with data)"
    )

    # Standardize population
    logger.info("Standardizing population data (harmonized age groups)...")
    pop_std = population.copy()
    pop_std.columns = pop_std.columns.str.lower()
    pop_std = pop_std.rename(columns={"year": "YR"})
    pop_std["sex"] = pop_std["sex"].astype(str).str.strip().str.capitalize()
    pop_std["age_group"] = pop_std["age_group"].apply(standardize_age_group)
    pop_std = pop_std[["YR", "sex", "age_group", "population"]].copy()
    pop_std["population"] = pd.to_numeric(pop_std["population"], errors="coerce")
    pop_std = pop_std.dropna(subset=["population", "age_group"])

    # Trim to shared years to avoid empty joins
    common_years = sorted(set(mort_std["YR"]) & set(pop_std["YR"]))
    mort_std = mort_std[mort_std["YR"].isin(common_years)]
    pop_std = pop_std[pop_std["YR"].isin(common_years)]

    pop_years = sorted(pop_std["YR"].unique())
    logger.info(f"  Population records: {len(pop_std):,}")
    logger.info(
        f"  Year coverage: {pop_years[0]}-{pop_years[-1]} ({len(pop_years)} continuous years)"
    )

    return mort_std, pop_std


def aggregate_by_dimensions(mort_std, pop_std):
    """Aggregate mortality and population by harmonized age group."""
    logger.info("\n" + "=" * 70)
    logger.info("AGGREGATING DATA")
    logger.info("=" * 70)

    # Mortality by year, cause, sex, age_group
    logger.info("Aggregating mortality by year, cause, sex, age_group...")
    mort_agg = (
        mort_std.groupby(["YR", "cause", "sex", "age_group"], as_index=False)["deaths"].sum()
    )
    mort_agg = mort_agg[mort_agg["deaths"] > 0]
    logger.info(f"  ✓ {len(mort_agg):,} cause/age combinations")

    # Population by year, sex, age_group
    logger.info("Aggregating population by year, sex, age_group...")
    pop_agg = pop_std.groupby(["YR", "sex", "age_group"], as_index=False)["population"].sum()
    logger.info(f"  ✓ {len(pop_agg):,} age/sex population combinations")

    return mort_agg, pop_agg


def calculate_mortality_rates(mort_agg, pop_agg):
    """Calculate mortality rates per 100,000 using age-group denominators."""
    logger.info("\n" + "=" * 70)
    logger.info("CALCULATING MORTALITY RATES")
    logger.info("=" * 70)

    logger.info("Merging mortality and population data on year/sex/age_group...")

    merged = mort_agg.merge(pop_agg, on=["YR", "sex", "age_group"], how="left")

    # Check merge quality
    unmatched = merged[merged["population"].isna()]
    logger.info(f"  Matched records: {len(merged[merged['population'].notna()]):,}")
    if len(unmatched) > 0:
        logger.warning(
            f"  Unmatched mortality records (no population): {len(unmatched):,}"
        )

    # Calculate rate per 100,000 using age-group population
    logger.info("Calculating rates per 100,000 population (age-group denominators)...")
    merged["mortality_rate_per_100k_age_group_population"] = np.where(
        merged["population"] > 0,
        (merged["deaths"] / merged["population"]) * 100000,
        np.nan,
    )
    merged["mortality_rate_per_100k"] = merged["mortality_rate_per_100k_age_group_population"]  # alias for backward compatibility
    merged["population_age_group"] = merged["population"]

    merged_with_rates = merged.dropna(subset=["mortality_rate_per_100k_age_group_population"])
    logger.info(f"  ✓ {len(merged_with_rates):,} records with calculated rates")

    # Select final columns
    rates = merged_with_rates[
        [
            "YR",
            "cause",
            "sex",
            "age_group",
            "deaths",
            "population_age_group",
            "mortality_rate_per_100k_age_group_population",
            "mortality_rate_per_100k",
        ]
    ].copy()

    rates = rates.rename(columns={"YR": "year"})
    rates = rates.sort_values(["year", "cause", "sex", "age_group"])

    return rates


def calculate_age_group_totals(rates: pd.DataFrame) -> pd.DataFrame:
    """Aggregate across causes but keep age-group denominators explicit."""
    logger.info("\nCalculating age-group totals (all causes combined)...")

    pop_unique = rates[["year", "sex", "age_group", "population_age_group"]].drop_duplicates()
    deaths = rates.groupby(["year", "sex", "age_group"], as_index=False)["deaths"].sum()

    age_group_totals = deaths.merge(pop_unique, on=["year", "sex", "age_group"], how="left")
    age_group_totals["mortality_rate_per_100k_age_group_population"] = (
        age_group_totals["deaths"] / age_group_totals["population_age_group"]
    ) * 100000
    age_group_totals["mortality_rate_per_100k"] = age_group_totals[
        "mortality_rate_per_100k_age_group_population"
    ]  # alias
    age_group_totals["denominator_label"] = "age group population"

    age_group_totals["age_group"] = pd.Categorical(
        age_group_totals["age_group"], categories=AGE_GROUP_ORDER, ordered=True
    )
    age_group_totals = age_group_totals.sort_values(["year", "age_group", "sex"]).reset_index(drop=True)
    return age_group_totals


def calculate_yearly_totals(rates: pd.DataFrame) -> pd.DataFrame:
    """Calculate yearly mortality rates using total population as denominator."""
    logger.info("\nCalculating yearly total rates (explicitly using total population)...")

    # Unique population per year (avoid double-counting across causes)
    pop_unique = (
        rates[["year", "sex", "age_group", "population_age_group"]]
        .drop_duplicates()
        .groupby("year", as_index=False)["population_age_group"]
        .sum()
        .rename(columns={"population_age_group": "population_total"})
    )

    deaths_year = rates.groupby("year", as_index=False)["deaths"].sum()

    yearly = deaths_year.merge(pop_unique, on="year", how="left")
    yearly["mortality_rate_per_100k_total_population"] = (
        yearly["deaths"] / yearly["population_total"]
    ) * 100000
    yearly["mortality_rate_per_100k"] = yearly["mortality_rate_per_100k_total_population"]  # alias
    yearly["denominator_label"] = "total population"

    logger.info(f"  ✓ {len(yearly):,} yearly records")

    return yearly


def save_outputs(rates, age_group_totals, yearly):
    """Save output files with explicit denominator labelling."""
    logger.info("\n" + "=" * 70)
    logger.info("SAVING OUTPUTS")
    logger.info("=" * 70)

    out_dir = MORTALITY_DIR

    # Save detailed rates by cause as ZIP (age-group denominator)
    import zipfile
    out_rates_zip = out_dir / "uk_mortality_rates_per_100k_by_cause.zip"
    with zipfile.ZipFile(out_rates_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        csv_name = "uk_mortality_rates_per_100k_by_cause.csv"
        zf.writestr(csv_name, rates.to_csv(index=False))
    logger.info(f"✓ Saved: {out_rates_zip.name}")
    logger.info(f"  {len(rates):,} records")
    logger.info(f"  Columns: {list(rates.columns)}")

    # Save age-group totals (all causes combined)
    out_age_groups = out_dir / "uk_mortality_rates_per_100k_by_age_group.csv"
    age_group_totals.to_csv(out_age_groups, index=False)
    logger.info(f"✓ Saved: {out_age_groups.name}")
    logger.info(f"  {len(age_group_totals):,} records")

    # Save yearly totals (overall population denominator)
    out_yearly = out_dir / "uk_mortality_rates_per_100k_yearly_totals.csv"
    yearly.to_csv(out_yearly, index=False)
    logger.info(f"✓ Saved: {out_yearly.name}")
    logger.info(f"  {len(yearly):,} records")

    return out_rates_zip, out_age_groups, out_yearly


def print_summary(rates, age_group_totals, yearly):
    """Print summary statistics with explicit denominator notes."""
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 70)

    logger.info("\nMortality Rates Overview (by cause, age-group denominators):")
    logger.info(f"  Time period: {rates['year'].min():.0f} - {rates['year'].max():.0f}")
    logger.info(f"  Distinct causes: {rates['cause'].nunique()}")
    logger.info(f"  Years with data: {rates['year'].nunique()}")

    logger.info("\nMortality Rate Statistics (per 100,000; age-group denominators):")
    logger.info(f"  Mean: {rates['mortality_rate_per_100k_age_group_population'].mean():.2f}")
    logger.info(f"  Median: {rates['mortality_rate_per_100k_age_group_population'].median():.2f}")
    logger.info(f"  Min: {rates['mortality_rate_per_100k_age_group_population'].min():.2f}")
    logger.info(f"  Max: {rates['mortality_rate_per_100k_age_group_population'].max():.2f}")

    logger.info("\nExample yearly total rates (per 100,000; total population denominator):")
    for year in [
        yearly["year"].min(),
        yearly["year"].min() + 25,
        yearly["year"].max() - 25,
        yearly["year"].max(),
    ]:
        if year in yearly["year"].values:
            rate = yearly.loc[yearly["year"] == year, "mortality_rate_per_100k_total_population"].values[0]
            logger.info(f"  {int(year)}: {rate:.1f} per 100,000 (total population)")

    logger.info("\nTop 5 age-group rates in latest year (per 100,000; age-group denominators):")
    latest_year = age_group_totals["year"].max()
    latest = age_group_totals[age_group_totals["year"] == latest_year]
    latest_sorted = latest.sort_values("mortality_rate_per_100k_age_group_population", ascending=False).head(5)
    for _, row in latest_sorted.iterrows():
        logger.info(
            f"  {int(row['year'])} {row['age_group']} {row['sex']}: "
            f"{row['mortality_rate_per_100k_age_group_population']:.1f} per 100k"
        )

    logger.info("\nTop 10 Causes by Total Deaths (2010-2017):")
    recent = rates[rates["year"] >= 2010]
    top_causes = recent.groupby("cause")["deaths"].sum().nlargest(10)
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
        age_group_totals = calculate_age_group_totals(rates)
        yearly = calculate_yearly_totals(rates)

        # Save
        out_rates, out_age_groups, out_yearly = save_outputs(rates, age_group_totals, yearly)

        # Summary
        print_summary(rates, age_group_totals, yearly)

        return True

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
