"""
Generate summary mortality data by year
Shows: total deaths per 100,000 and drug-related deaths per 100,000
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

MORTALITY_DIR = Path(__file__).parent
POPULATION_DIR = Path(__file__).parent.parent / "population"


def load_data():
    """Load mortality and population data"""
    logger.info("\n" + "=" * 70)
    logger.info("LOADING DATA")
    logger.info("=" * 70)

    # Load mortality
    mortality_file = MORTALITY_DIR / "uk_mortality_comprehensive_1901_2019.csv"
    logger.info(f"Loading mortality: {mortality_file.name}")
    mortality = pd.read_csv(mortality_file, low_memory=False)
    logger.info(f"  ✓ {len(mortality):,} records")

    # Load population
    pop_file = POPULATION_DIR / "combined_population_data.csv"
    logger.info(f"Loading population: {pop_file.name}")
    population = pd.read_csv(pop_file)
    logger.info(f"  ✓ {len(population):,} records")

    return mortality, population


def prepare_data(mortality, population):
    """Prepare and aggregate data"""
    logger.info("\n" + "=" * 70)
    logger.info("PREPARING DATA")
    logger.info("=" * 70)

    # Standardize mortality
    mort = mortality.copy()
    mort = mort.rename(columns={"year": "YR"})
    mort["deaths"] = (
        pd.to_numeric(mort["deaths"], errors="coerce").fillna(0).astype(int)
    )
    mort["YR"] = pd.to_numeric(mort["YR"], errors="coerce")
    mort = mort.dropna(subset=["YR"])
    logger.info(f"  Mortality records: {len(mort):,}")

    # Standardize population
    pop = population.copy()
    pop = pop[["YR", "SEX", "AGE", "POP"]].copy()
    # Fix AGE column for 2001+
    if "Agegroup" in population.columns:
        pop["AGE"] = population["AGE"].fillna(population["Agegroup"])
    pop.columns = ["YR", "sex", "age", "population"]
    pop["population"] = pd.to_numeric(pop["population"], errors="coerce")
    pop = pop.dropna(subset=["population", "age"])
    logger.info(f"  Population records: {len(pop):,}")

    return mort, pop


def calculate_summary(mortality, population_raw):
    """Calculate total deaths per 100k and drug deaths per 100k by year"""
    logger.info("\n" + "=" * 70)
    logger.info("CALCULATING SUMMARY")
    logger.info("=" * 70)

    # Define drug-related ICD-10 codes (poisoning by drugs)
    drug_codes = [
        "X410",
        "X411",
        "X412",
        "X413",
        "X414",
        "X415",
        "X416",
        "X417",
        "X418",
        "X419",
        "X420",
        "X421",
        "X422",
        "X423",
        "X424",
        "X425",
        "X426",
        "X427",
        "X428",
        "X429",
        "X430",
        "X431",
        "X432",
        "X438",
        "X439",
        "X440",
        "X441",
        "X442",
        "X443",
        "X444",
        "X445",
        "X446",
        "X447",
        "X448",
        "X449",
        "X610",
        "X611",
        "X612",
        "X613",
        "X614",
        "X615",
        "X616",
        "X617",
        "X618",
        "X619",
        "X620",
        "X621",
        "X622",
        "X623",
        "X624",
        "X625",
        "X627",
        "X628",
        "X629",
        "X630",
        "X631",
        "X634",
        "X635",
        "X638",
        "X639",
        "X640",
        "X641",
        "X642",
        "X643",
        "X644",
        "X645",
        "X646",
        "X647",
        "X648",
        "X649",
        "Y110",
        "Y111",
        "Y112",
        "Y113",
        "Y114",
        "Y115",
        "Y116",
        "Y117",
        "Y118",
        "Y119",
        "Y120",
        "Y121",
        "Y122",
        "Y124",
        "Y125",
        "Y127",
        "Y128",
        "Y129",
        "Y130",
        "Y134",
        "Y138",
        "Y139",
        "Y140",
        "Y141",
        "Y142",
        "Y143",
        "Y144",
        "Y145",
        "Y147",
        "Y148",
        "Y149",
    ]

    # Separate drug and non-drug deaths
    mort_all = mortality.copy()
    mort_all["is_drug"] = mort_all["cause"].astype(str).isin(drug_codes)

    # Aggregate by year
    logger.info("Aggregating total deaths by year...")
    total_deaths = mort_all.groupby("YR")["deaths"].sum().reset_index()
    total_deaths.columns = ["year", "total_deaths"]

    logger.info("Aggregating drug-related deaths by year...")
    drug_deaths = (
        mort_all[mort_all["is_drug"]].groupby("YR")["deaths"].sum().reset_index()
    )
    drug_deaths.columns = ["year", "drug_deaths"]

    # Aggregate population by year
    logger.info("Aggregating population by year...")
    pop_totals = population_raw.groupby("YR")["POP"].sum().reset_index()
    pop_totals.columns = ["year", "total_population"]

    # Merge all
    summary = total_deaths.merge(drug_deaths, on="year", how="left").fillna(0)
    summary = summary.merge(pop_totals, on="year", how="left")
    summary["drug_deaths"] = summary["drug_deaths"].astype(int)

    # Calculate rates per 100,000
    summary["total_deaths_per_100k"] = (
        summary["total_deaths"] / summary["total_population"]
    ) * 100000
    summary["drug_deaths_per_100k"] = (
        summary["drug_deaths"] / summary["total_population"]
    ) * 100000

    # Select final columns
    summary = summary[
        [
            "year",
            "total_deaths",
            "total_population",
            "total_deaths_per_100k",
            "drug_deaths",
            "drug_deaths_per_100k",
        ]
    ]

    summary = summary.sort_values("year")

    # Remove years without population data
    summary = summary.dropna(subset=["total_population"])

    logger.info(f"  ✓ {len(summary)} years of summary data")
    logger.info(
        f"  Year range: {summary['year'].min():.0f}-{summary['year'].max():.0f}"
    )

    return summary


def main():
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 15 + "UK MORTALITY SUMMARY (1900-2025)" + " " * 21 + "║")
    logger.info("╚" + "=" * 68 + "╝")

    mortality, population = load_data()
    mort_prep, pop_prep = prepare_data(mortality, population)
    summary = calculate_summary(mort_prep, population)

    # Save to CSV
    logger.info("\n" + "=" * 70)
    logger.info("SAVING OUTPUT")
    logger.info("=" * 70)

    output_file = MORTALITY_DIR / "uk_mortality_summary_1901_2016.csv"
    summary.to_csv(output_file, index=False)
    logger.info(f"✓ Saved: {output_file.name}")
    logger.info(f"  {len(summary)} years of data")

    # Display statistics
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 70)

    logger.info("\nTotal Deaths per 100,000:")
    logger.info(f"  1901: {summary.iloc[0]['total_deaths_per_100k']:.2f} per 100,000")
    logger.info(f"  2016: {summary.iloc[-1]['total_deaths_per_100k']:.2f} per 100,000")
    logger.info(
        f"  Change: {summary.iloc[-1]['total_deaths_per_100k'] - summary.iloc[0]['total_deaths_per_100k']:.2f} ({((summary.iloc[-1]['total_deaths_per_100k'] / summary.iloc[0]['total_deaths_per_100k']) - 1) * 100:.1f}%)"
    )

    logger.info("\nDrug-Related Deaths per 100,000:")
    drug_data = summary[summary["drug_deaths_per_100k"] > 0]
    if len(drug_data) > 0:
        logger.info(f"  Available from: {drug_data['year'].min():.0f} onwards")
        logger.info(
            f"  {drug_data['year'].max():.0f}: {drug_data.iloc[-1]['drug_deaths_per_100k']:.3f} per 100,000"
        )
        logger.info(
            f"  Peak: {drug_data['drug_deaths_per_100k'].max():.3f} per 100,000 ({int(drug_data.loc[drug_data['drug_deaths_per_100k'].idxmax(), 'year'])})"
        )
    else:
        logger.info(
            "  No drug-related deaths recorded (data not available for pre-2001 years)"
        )

    logger.info("\n" + "=" * 70)
    logger.info("✓ SUMMARY COMPLETE!")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
