# data_sources/parliament/parliaments.py
import pandas as pd
from pathlib import Path
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


def _most_recent_extract_dir() -> Path:
    """Return the most recent extract directory, or create a new one."""
    base_dir = Path(__file__).parent
    extract_dirs = [p for p in base_dir.iterdir() if p.is_dir() and p.name.startswith("extract_")]
    if extract_dirs:
        return max(extract_dirs, key=lambda p: p.stat().st_mtime)
    
    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    new_dir = base_dir / f"extract_{ts}"
    new_dir.mkdir(parents=True, exist_ok=True)
    return new_dir


def main():
    """Demo: fetch and save Parliament periods data."""
    print("Fetching Parliament periods...")
    try:
        parliaments_df = get_parliament_periods()
        print(f"Retrieved {len(parliaments_df)} Parliament periods")
        
        if len(parliaments_df) > 0:
            extract_dir = _most_recent_extract_dir()
            output_file = extract_dir / "parliaments.csv"
            parliaments_df.to_csv(output_file, index=False)
            print(f"✓ Data saved to: {output_file}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
