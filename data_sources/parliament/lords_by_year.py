# data_sources/parliament/lords_by_year.py
"""
Script to analyze the number of sitting Lords per year.

It prefers using an existing CSV extract (lords_memberships*.csv) from the most
recent extract folder. If none is found, it will refresh data by calling
lords.get_lords_memberships(), write a new CSV, and then proceed.
"""
import pandas as pd
from pathlib import Path
from typing import Optional
from lords import get_lords_memberships


BASE_DIR = Path(__file__).parent


def _most_recent_extract_dir() -> Path:
    """Return the most recent extract directory under parliament (by mtime).

    If none exist, create a new directory named `extract_<YYYYMMDD_HHMMSS>`.
    """
    extract_dirs = [p for p in BASE_DIR.iterdir() if p.is_dir() and p.name.startswith("extract_")]
    if extract_dirs:
        return max(extract_dirs, key=lambda p: p.stat().st_mtime)

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    new_dir = BASE_DIR / f"extract_{ts}"
    new_dir.mkdir(parents=True, exist_ok=True)
    return new_dir


def _load_latest_extract() -> Optional[pd.DataFrame]:
    """Load the most recent lords_memberships CSV if available."""
    extract_dir = _most_recent_extract_dir()
    candidates = sorted(
        extract_dir.glob("lords_memberships*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return None

    latest = candidates[0]
    print(f"Using existing extract: {latest}")
    try:
        return pd.read_csv(latest, parse_dates=True)
    except Exception as exc:
        print(f"Failed to load {latest}: {exc}")
        return None


def get_lords_by_year(
    from_date: str = "1900-01-01",
    to_date: str = "2030-12-31"
) -> pd.DataFrame:
    """
    Calculate the number of sitting Lords for each year, broken down by seat type.

    A Lord is considered "sitting" in a given year if their membership
    overlaps with that year (start_date <= end of year AND 
    end_date >= start of year, or end_date is NaN for current members).

    Parameters
    ----------
    from_date : str, optional
        Start date for filtering memberships
    to_date : str, optional
        End date for filtering memberships

    Returns
    -------
    pd.DataFrame
        Columns:
            year
            total (all seat types)
            one column per seat_type_name (if present in data)
    """
    print("Fetching Lords memberships data...")

    # Prefer a cached extract; otherwise refresh from API and cache it.
    lords_df = _load_latest_extract()
    if lords_df is None:
        print("No cached extract found; refreshing via API...")
        lords_df = get_lords_memberships(from_date, to_date)
        extract_dir = _most_recent_extract_dir()
        extract_path = extract_dir / "lords_memberships.csv"
        lords_df.to_csv(extract_path, index=False)
        print(f"Saved fresh extract to {extract_path}")
    
    if len(lords_df) == 0:
        print("No data retrieved")
        return pd.DataFrame()
    
    print(f"Retrieved {len(lords_df)} Lords memberships")
    print(f"Available columns: {list(lords_df.columns)}")
    
    # Find the date columns (support multiple schemas)
    start_col = None
    end_col = None
    
    for col in [
        'start_date',
        'from_date',
        'startDate',
        'seat_incumbency_start_date',
    ]:
        if col in lords_df.columns:
            start_col = col
            break
    
    for col in [
        'end_date',
        'to_date',
        'endDate',
        'seat_incumbency_end_date',
    ]:
        if col in lords_df.columns:
            end_col = col
            break
    
    if not start_col or not end_col:
        print(f"Error: Could not find start/end date columns")
        print(f"Available columns: {list(lords_df.columns)}")
        return pd.DataFrame()
    
    # Convert to datetime if not already
    lords_df[start_col] = pd.to_datetime(lords_df[start_col], errors="coerce")
    lords_df[end_col] = pd.to_datetime(lords_df[end_col], errors="coerce")
    
    # Ensure seat type column exists
    seat_col = "seat_type_name" if "seat_type_name" in lords_df.columns else None
    if seat_col is None:
        lords_df["seat_type_name"] = "Unknown"
        seat_col = "seat_type_name"

    # Extract years from the data
    start_year = lords_df[start_col].dt.year.min()
    end_year = lords_df[end_col].dt.year.max()

    # Handle NaN end dates (still serving)
    lords_df[end_col] = lords_df[end_col].fillna(pd.Timestamp.now())
    end_year = max(end_year, pd.Timestamp.now().year)

    # Drop rows with missing start dates
    lords_df = lords_df.dropna(subset=[start_col])

    print(f"Date range: {start_year} to {end_year}")

    # Precompute unique seat types for columns
    seat_types = sorted(lords_df[seat_col].dropna().unique())

    # Count sitting lords per year and seat type
    yearly_counts = []

    for year in range(start_year, end_year + 1):
        year_start = pd.Timestamp(f"{year}-01-01")
        year_end = pd.Timestamp(f"{year}-12-31")

        # Lords whose membership overlaps with this year
        sitting = lords_df[
            (lords_df[start_col] <= year_end)
            & (lords_df[end_col] >= year_start)
        ]

        row = {"year": year, "total": len(sitting)}

        # Seat-type breakdown
        counts = sitting[seat_col].value_counts()
        for st in seat_types:
            row[st] = int(counts.get(st, 0))

        yearly_counts.append(row)

    result_df = pd.DataFrame(yearly_counts)
    return result_df


def main():
    """Generate and display Lords by year table."""
    print("=" * 70)
    print("Generating House of Lords membership count by year...")
    print("=" * 70)
    
    try:
        lords_by_year_df = get_lords_by_year()
        
        if len(lords_by_year_df) > 0:
            print("\n\nHouse of Lords membership count by year:")
            print(lords_by_year_df.to_string(index=False))
            
            # Save to CSV in the same extract directory as the source data
            extract_dir = _most_recent_extract_dir()
            output_file = extract_dir / "lords_by_year.csv"
            lords_by_year_df.to_csv(output_file, index=False)
            print(f"\n✓ Data saved to: {output_file}")
            
            # Display summary statistics
            print(f"\n\nSummary Statistics:")
            print(f"  Period: {lords_by_year_df['year'].min()} to {lords_by_year_df['year'].max()}")
            print(f"  Average sitting lords: {lords_by_year_df['total'].mean():.0f}")
            print(f"  Minimum sitting lords: {lords_by_year_df['total'].min()}")
            print(f"  Maximum sitting lords: {lords_by_year_df['total'].max()}")
        else:
            print("No data retrieved")
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        print("\nNote: The Parliament API may be temporarily unavailable.")


if __name__ == "__main__":
    main()
