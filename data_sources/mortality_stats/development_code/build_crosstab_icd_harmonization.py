"""
Generate a crosswalk table showing original codes and descriptions mapped to harmonized categories.
Outputs CSV at the mortality_stats folder.
"""

import pandas as pd
from pathlib import Path
import zipfile

BASE_DIR = Path(__file__).parent.parent
SOURCE_ZIP = BASE_DIR / "uk_mortality_by_cause_1901_2000_harmonized.zip"
SOURCE_CSV = BASE_DIR / "uk_mortality_by_cause_1901_2000_harmonized.csv"
OUT = BASE_DIR / "icd_harmonization_crosswalk.csv"


def _read_csv_from_zip(zip_path: Path, inner_name: str | None = None) -> pd.DataFrame:
    """Read a CSV from a zip file; if inner_name is None, use the first .csv inside."""
    with zipfile.ZipFile(zip_path, 'r') as zf:
        name = inner_name
        if name is None:
            csvs = [n for n in zf.namelist() if n.lower().endswith('.csv')]
            if not csvs:
                raise FileNotFoundError(f"No CSV found inside {zip_path}")
            name = csvs[0]
        with zf.open(name) as f:
            return pd.read_csv(f)


def main():
    # Prefer ZIP source (policy), fallback to CSV if present
    if SOURCE_ZIP.exists():
        df = _read_csv_from_zip(SOURCE_ZIP)
    elif SOURCE_CSV.exists():
        df = pd.read_csv(SOURCE_CSV)
    else:
        raise FileNotFoundError(
            f"No harmonized source found: {SOURCE_ZIP} or {SOURCE_CSV}"
        )
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
