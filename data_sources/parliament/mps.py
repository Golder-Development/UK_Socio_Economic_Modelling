# data_sources/parliament/mps.py
import pandas as pd
from pathlib import Path
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
    """Demo: fetch and save MPs data."""
    print("Fetching House of Commons MPs...")
    try:
        mps_df = get_mps()
        print(f"Retrieved {len(mps_df)} MPs")
        
        if len(mps_df) > 0:
            extract_dir = _most_recent_extract_dir()
            output_file = extract_dir / "mps.csv"
            mps_df.to_csv(output_file, index=False)
            print(f"✓ Data saved to: {output_file}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
