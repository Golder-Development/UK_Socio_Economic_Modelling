# data_sources/parliament/lords.py
import pandas as pd
import pdpy


def get_lords_memberships(
    from_date: str = "1900-01-01",
    to_date: str = "2030-12-31"
) -> pd.DataFrame:
    """
    Get all House of Lords memberships with admission and removal dates.

    Parameters
    ----------
    from_date : str, optional
        Start date for filtering memberships (default: "1900-01-01")
    to_date : str, optional
        End date for filtering memberships (default: "2030-12-31")

    Returns
    -------
    pd.DataFrame
        DataFrame with House of Lords membership data including dates
    """
    lords_df = pdpy.fetch_lords_memberships(
        from_date=from_date,
        to_date=to_date
    )

    # Convert date columns to datetime if they exist
    # The column names may vary, so we handle common patterns
    for date_col in ['start_date', 'from_date', 'startDate']:
        if date_col in lords_df.columns:
            lords_df[date_col] = pd.to_datetime(lords_df[date_col])
            # Standardize to start_date
            if date_col != 'start_date':
                lords_df['start_date'] = lords_df[date_col]
            break

    for date_col in ['end_date', 'to_date', 'endDate']:
        if date_col in lords_df.columns:
            lords_df[date_col] = pd.to_datetime(lords_df[date_col])
            # Standardize to end_date
            if date_col != 'end_date':
                lords_df['end_date'] = lords_df[date_col]
            break

    return lords_df


def get_government_timeline() -> pd.DataFrame:
    """
    Create a timeline of which party was in government.
    Based on UK general election results.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
            start_date
            end_date
            party_in_power
            prime_minister
    """
    # Historical UK governments - can be enhanced with more detailed data
    governments = [
        {"start_date": "1945-07-26", "end_date": "1951-10-26", "party_in_power": "Labour", "prime_minister": "Clement Attlee"},
        {"start_date": "1951-10-26", "end_date": "1955-04-06", "party_in_power": "Conservative", "prime_minister": "Winston Churchill"},
        {"start_date": "1955-04-06", "end_date": "1957-01-10", "party_in_power": "Conservative", "prime_minister": "Anthony Eden"},
        {"start_date": "1957-01-10", "end_date": "1963-10-19", "party_in_power": "Conservative", "prime_minister": "Harold Macmillan"},
        {"start_date": "1963-10-19", "end_date": "1964-10-16", "party_in_power": "Conservative", "prime_minister": "Alec Douglas-Home"},
        {"start_date": "1964-10-16", "end_date": "1970-06-19", "party_in_power": "Labour", "prime_minister": "Harold Wilson"},
        {"start_date": "1970-06-19", "end_date": "1974-03-04", "party_in_power": "Conservative", "prime_minister": "Edward Heath"},
        {"start_date": "1974-03-04", "end_date": "1976-04-05", "party_in_power": "Labour", "prime_minister": "Harold Wilson"},
        {"start_date": "1976-04-05", "end_date": "1979-05-04", "party_in_power": "Labour", "prime_minister": "James Callaghan"},
        {"start_date": "1979-05-04", "end_date": "1990-11-28", "party_in_power": "Conservative", "prime_minister": "Margaret Thatcher"},
        {"start_date": "1990-11-28", "end_date": "1997-05-02", "party_in_power": "Conservative", "prime_minister": "John Major"},
        {"start_date": "1997-05-02", "end_date": "2007-06-27", "party_in_power": "Labour", "prime_minister": "Tony Blair"},
        {"start_date": "2007-06-27", "end_date": "2010-05-11", "party_in_power": "Labour", "prime_minister": "Gordon Brown"},
        {"start_date": "2010-05-11", "end_date": "2015-05-08", "party_in_power": "Conservative-Liberal Democrat Coalition", "prime_minister": "David Cameron"},
        {"start_date": "2015-05-08", "end_date": "2016-07-13", "party_in_power": "Conservative", "prime_minister": "David Cameron"},
        {"start_date": "2016-07-13", "end_date": "2019-07-24", "party_in_power": "Conservative", "prime_minister": "Theresa May"},
        {"start_date": "2019-07-24", "end_date": "2022-09-06", "party_in_power": "Conservative", "prime_minister": "Boris Johnson"},
        {"start_date": "2022-09-06", "end_date": "2022-10-25", "party_in_power": "Conservative", "prime_minister": "Liz Truss"},
        {"start_date": "2022-10-25", "end_date": "2024-07-05", "party_in_power": "Conservative", "prime_minister": "Rishi Sunak"},
        {"start_date": "2024-07-05", "end_date": "2030-12-31", "party_in_power": "Labour", "prime_minister": "Keir Starmer"},
    ]

    df = pd.DataFrame(governments)
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])

    return df


def get_lords_with_government(
    from_date: str = "1900-01-01",
    to_date: str = "2030-12-31"
) -> pd.DataFrame:
    """
    Get House of Lords memberships with the party in power when they were admitted.

    Parameters
    ----------
    from_date : str, optional
        Start date for filtering memberships (default: "1900-01-01")
    to_date : str, optional
        End date for filtering memberships (default: "2030-12-31")

    Returns
    -------
    pd.DataFrame
        DataFrame with all Lord membership information plus:
            party_in_power_at_admission
            prime_minister_at_admission
    """
    lords_df = get_lords_memberships(from_date, to_date)
    government_df = get_government_timeline()

    # For each lord membership, find which government was in power at admission
    def find_government_at_date(date):
        if pd.isna(date):
            return None, None

        matching = government_df[
            (government_df["start_date"] <= date) &
            (government_df["end_date"] >= date)
        ]

        if len(matching) > 0:
            return matching.iloc[0]["party_in_power"], matching.iloc[0]["prime_minister"]
        return "Unknown", "Unknown"

    # Apply the function to get party and PM at admission
    lords_df[["party_in_power_at_admission", "prime_minister_at_admission"]] = lords_df["start_date"].apply(
        lambda x: pd.Series(find_government_at_date(x))
    )

    return lords_df


def _most_recent_extract_dir():
    """Return the most recent extract directory, or create a new one."""
    from pathlib import Path
    base_dir = Path(__file__).parent
    extract_dirs = [p for p in base_dir.iterdir() if p.is_dir() and p.name.startswith("extract_")]
    if extract_dirs:
        return max(extract_dirs, key=lambda p: p.stat().st_mtime)
    
    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    new_dir = base_dir / f"extract_{ts}"
    new_dir.mkdir(parents=True, exist_ok=True)
    return new_dir


def main():
    """Demo usage of the functions."""
    print("Fetching House of Lords memberships...")

    try:
        lords_df = get_lords_memberships()

        print(f"\nTotal Lords memberships: {len(lords_df)}")
        print(f"\nAvailable columns: {list(lords_df.columns)}")

        if len(lords_df) > 0:
            print("\n\nFirst 5 Lords memberships:")
            print(lords_df.head(5).to_string())

            # Save to CSV in extract directory
            extract_dir = _most_recent_extract_dir()
            output_file = extract_dir / "lords_memberships.csv"
            lords_df.to_csv(output_file, index=False)
            print(f"\n✓ Data saved to: {output_file}")
        else:
            print("No data retrieved from API")

    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: The API may be temporarily unavailable.")
        print("You can test with the following once the API is available:")
        print("  - Uncomment the get_lords_with_government() call to add government context")
        print("  - Check that 'start_date' column exists in the returned data")


if __name__ == "__main__":
    main()
