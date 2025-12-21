import pandas as pd
import requests
from io import StringIO


CSV_URL = (
    "https://www.ons.gov.uk/file?"
    "uri=/economy/governmentpublicsectorandtaxes/"
    "publicsectorfinance/datasets/publicsectorfinances/"
    "current/publicsectorfinances.csv"
)

SERIES_MAP = {
    "ps_net_investment_ex_banks": "Public sector net investment excluding public sector banks",
    "total_receipts_ex_banks": "Public sector current receipts excluding public sector banks",
    "paye_income_tax": "Central government PAYE income tax receipts",
}


def to_financial_year(d: pd.Series) -> pd.Series:
    return d.dt.year.where(d.dt.month >= 4, d.dt.year - 1)


def main():
    print("Downloading ONS Public Sector Finances dataset…")
    r = requests.get(CSV_URL, timeout=60)
    r.raise_for_status()

    df = pd.read_csv(StringIO(r.text))
    df.columns = [c.strip() for c in df.columns]

    # Standardise date
    df["date"] = pd.to_datetime(df["Month"], errors="coerce")
    df = df.dropna(subset=["date"])

    out = None

    for out_col, ons_name in SERIES_MAP.items():
        if ons_name not in df.columns:
            raise ValueError(f"Series not found in dataset: {ons_name}")

        tmp = df[["date", ons_name]].copy()
        tmp[out_col] = pd.to_numeric(tmp[ons_name], errors="coerce")
        tmp["fy_start"] = to_financial_year(tmp["date"])

        fy = (
            tmp.groupby("fy_start")[out_col]
            .sum()
            .reset_index()
        )

        out = fy if out is None else out.merge(
            fy, on="fy_start", how="outer"
        )

    out = out.sort_values("fy_start")
    out.to_csv("ons_fiscal_fy.csv", index=False)

    print("Saved: ons_fiscal_fy.csv")
    print(out.tail(10))


if __name__ == "__main__":
    main()
