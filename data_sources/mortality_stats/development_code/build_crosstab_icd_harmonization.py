"""
Generate a crosswalk table showing original codes and descriptions mapped to harmonized categories.
Outputs CSV at the mortality_stats folder.
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SOURCE = BASE_DIR / "uk_mortality_by_cause_1901_2000_harmonized.csv"
OUT = BASE_DIR / "icd_harmonization_crosswalk.csv"


def main():
    df = pd.read_csv(SOURCE)
    cols = [
        "icd_version",
        "cause",
        "cause_description",
        "harmonized_category",
        "harmonized_category_name",
        "classification_confidence",
    ]
    # icd_version might not be in SOURCE; reconstruct if needed
    if "icd_version" not in df.columns:
        # year-based mapping
        ranges = {
            "ICD-1 (1901-1910)": (1901, 1910),
            "ICD-2 (1911-1920)": (1911, 1920),
            "ICD-3 (1921-1930)": (1921, 1930),
            "ICD-4 (1931-1939)": (1931, 1939),
            "ICD-5 (1940-1949)": (1940, 1949),
            "ICD-6 (1950-1957)": (1950, 1957),
            "ICD-7 (1958-1967)": (1958, 1967),
            "ICD-8 (1968-1978)": (1968, 1978),
            "ICD-9a (1979-1984)": (1979, 1984),
            "ICD-9b (1985-1993)": (1985, 1993),
            "ICD-9c (1994-2000)": (1994, 2000),
        }
        def ver(y):
            for k,(s,e) in ranges.items():
                if s <= y <= e:
                    return k
            return None
        df["icd_version"] = df["year"].apply(ver)
    cross = (
        df[cols]
        .drop_duplicates()
        .sort_values(["icd_version", "cause", "harmonized_category_name"])
    )
    cross.to_csv(OUT, index=False)
    print(f"Saved crosswalk: {OUT}")


if __name__ == "__main__":
    main()
