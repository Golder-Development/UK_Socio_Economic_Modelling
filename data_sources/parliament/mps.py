# data_sources/parliament/mps.py
import pandas as pd
from .client import get_client


def get_mps() -> pd.DataFrame:
    """
    Returns:
        mp_id
        name
        party
        constituency
        start_date
        end_date
    """
    client = get_client()
    data = client.get_mps()

    df = pd.DataFrame(data)
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])

    return df
