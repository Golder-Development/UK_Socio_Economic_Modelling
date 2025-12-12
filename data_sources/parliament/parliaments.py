# data_sources/parliament/parliaments.py
import pandas as pd
from .client import get_client


def get_parliament_periods() -> pd.DataFrame:
    """
    Returns:
        parliament_number
        start_date
        end_date
    """
    client = get_client()
    data = client.get_parliaments()

    df = pd.DataFrame(data)
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])

    return df[["parliament_number", "start_date", "end_date"]]
