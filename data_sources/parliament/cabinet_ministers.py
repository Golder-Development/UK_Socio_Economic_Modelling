"""
Generate a datafile of all cabinet ministers with department, post, dates, party, and prime minister.

Uses pdpy to fetch government roles for both MPs and Lords.
"""

import pandas as pd
import pdpy
from pathlib import Path
from datetime import datetime
import sys

# Import classification logic
sys.path.insert(0, str(Path(__file__).parent))
from cabinet_post_classifier import classify_post

# --- Configuration ----------------------------------------------------------
MIN_YEAR = 1970  # Only include data from this year onwards


def get_government_timeline() -> pd.DataFrame:
    """
    Create a timeline of which party was in government and who the PM was.
    
    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
            start_date
            end_date
            party_in_power
            prime_minister
    """
    # Historical UK governments
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


def get_parliaments_data() -> pd.DataFrame:
    """
    Fetch UK Parliament sessions data from general elections.
    
    Each Parliament runs from the election date until the next dissolution/election.
    
    Returns
    -------
    pd.DataFrame
        DataFrame with parliament dates including:
            parliament_name
            parliament_start_date
            parliament_end_date
    """
    print("Fetching Parliament sessions data...")
    try:
        elections = pdpy.get_general_elections()
        
        # Convert to datetime
        elections['election'] = pd.to_datetime(elections['election'])
        elections['dissolution'] = pd.to_datetime(elections['dissolution'])
        
        # Sort by election date
        elections = elections.sort_values('election').reset_index(drop=True)
        
        # Create parliament records with start/end dates
        parliaments = []
        for i in range(len(elections)):
            parl_start = elections.iloc[i]['election']
            # Parliament ends at the next dissolution or this election
            if i < len(elections) - 1:
                parl_end = elections.iloc[i + 1]['dissolution']
            else:
                # For the most recent parliament, use today's date
                parl_end = pd.Timestamp.now()
            
            parliaments.append({
                'parliament_number': i + 1,
                'parliament_year': elections.iloc[i]['name'],
                'parliament_start_date': parl_start,
                'parliament_end_date': parl_end
            })
        
        parl_df = pd.DataFrame(parliaments)
        return parl_df
    except Exception as e:
        print(f"Note: Could not fetch parliament data: {e}")
        return pd.DataFrame()


def find_prime_minister(start_date, gov_timeline: pd.DataFrame):
    """Find the prime minister at a given date."""
    if pd.isna(start_date):
        return None
    
    matching = gov_timeline[
        (gov_timeline["start_date"] <= start_date) &
        (gov_timeline["end_date"] >= start_date)
    ]
    
    if len(matching) > 0:
        return matching.iloc[0]["prime_minister"]
    return None


def find_parliament_dates(start_date, parliaments_df: pd.DataFrame):
    """
    Find the parliament start date and duration for a given date.
    
    Parameters
    ----------
    start_date : datetime
        The date to find parliament information for
    parliaments_df : pd.DataFrame
        DataFrame with parliament session data
    
    Returns
    -------
    tuple
        (parliament_start_date, parliament_length_days) or (None, None) if not found
    """
    if pd.isna(start_date) or len(parliaments_df) == 0:
        return None, None
    
    start_date = pd.to_datetime(start_date)
    
    matching = parliaments_df[
        (pd.to_datetime(parliaments_df['parliament_start_date']) <= start_date) &
        (pd.to_datetime(parliaments_df['parliament_end_date']) >= start_date)
    ]
    
    if len(matching) > 0:
        row = matching.iloc[0]
        parl_start = pd.to_datetime(row['parliament_start_date'])
        parl_end = pd.to_datetime(row['parliament_end_date'])
        parl_length = (parl_end - parl_start).days
        return parl_start, parl_length
    
    return None, None


def fetch_mps_cabinet_roles() -> pd.DataFrame:
    """
    Fetch government roles for MPs.
    
    Returns
    -------
    pd.DataFrame
        DataFrame with MP government roles
    """
    print("Fetching MP government roles...")
    try:
        gov_roles = pdpy.fetch_mps_government_roles()
        
        # Get party information
        party_df = pdpy.fetch_mps_party_memberships()
        
        # Merge party info - take party that was active during the government role
        def get_party_during_role(row):
            if pd.isna(row['government_incumbency_start_date']):
                return None
            person_id = row['person_id']
            start_date = pd.to_datetime(row['government_incumbency_start_date'])
            matching = party_df[
                (party_df['person_id'] == person_id) &
                (pd.to_datetime(party_df['party_membership_start_date']) <= start_date) &
                ((party_df['party_membership_end_date'].isna()) | 
                 (pd.to_datetime(party_df['party_membership_end_date']) >= start_date))
            ]
            if len(matching) > 0:
                return matching.iloc[0].get('party_name', None)
            return None
        
        gov_roles['party'] = gov_roles.apply(get_party_during_role, axis=1)
        
        # Add source
        gov_roles['member_house'] = 'Commons'
        
        return gov_roles
    except Exception as e:
        print(f"Error fetching MP government roles: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def fetch_lords_cabinet_roles() -> pd.DataFrame:
    """
    Fetch government roles for Lords.
    
    Returns
    -------
    pd.DataFrame
        DataFrame with Lord government roles
    """
    print("Fetching Lord government roles...")
    try:
        gov_roles = pdpy.fetch_lords_government_roles()
        
        # Get party information
        party_df = pdpy.fetch_lords_party_memberships()
        
        # Merge party info - take party that was active during the government role
        def get_party_during_role(row):
            if pd.isna(row['government_incumbency_start_date']):
                return None
            person_id = row['person_id']
            start_date = pd.to_datetime(row['government_incumbency_start_date'])
            matching = party_df[
                (party_df['person_id'] == person_id) &
                (pd.to_datetime(party_df['party_membership_start_date']) <= start_date) &
                ((party_df['party_membership_end_date'].isna()) | 
                 (pd.to_datetime(party_df['party_membership_end_date']) >= start_date))
            ]
            if len(matching) > 0:
                return matching.iloc[0].get('party_name', None)
            return None
        
        gov_roles['party'] = gov_roles.apply(get_party_during_role, axis=1)
        
        # Add source
        gov_roles['member_house'] = 'Lords'
        
        return gov_roles
    except Exception as e:
        print(f"Error fetching Lord government roles: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def get_cabinet_ministers_datafile(
    from_date: str = "1945-01-01",
    to_date: str = "2030-12-31",
    output_file: str = None
) -> pd.DataFrame:
    """
    Generate a comprehensive datafile of all cabinet ministers.
    
    Parameters
    ----------
    from_date : str, optional
        Start date for filtering (default: "1945-01-01")
    to_date : str, optional
        End date for filtering (default: "2030-12-31")
    output_file : str, optional
        Path to save CSV file. If None, saves to extract directory with timestamp.
    
    Returns
    -------
    pd.DataFrame
        DataFrame with cabinet minister data
    """
    print("\n=== Cabinet Ministers Data Extractor ===\n")
    
    # Get government timeline
    gov_timeline = get_government_timeline()
    
    # Get parliament data
    parliaments_df = get_parliaments_data()
    
    # Fetch data from both Houses
    mps_cabinet = fetch_mps_cabinet_roles()
    lords_cabinet = fetch_lords_cabinet_roles()
    
    # Combine data
    if len(mps_cabinet) > 0 and len(lords_cabinet) > 0:
        cabinet_df = pd.concat([mps_cabinet, lords_cabinet], ignore_index=True)
    elif len(mps_cabinet) > 0:
        cabinet_df = mps_cabinet.copy()
    elif len(lords_cabinet) > 0:
        cabinet_df = lords_cabinet.copy()
    else:
        print("No cabinet data retrieved")
        return pd.DataFrame()
    
    # Convert dates
    date_cols = ['government_incumbency_start_date', 'government_incumbency_end_date']
    for col in date_cols:
        if col in cabinet_df.columns:
            cabinet_df[col] = pd.to_datetime(cabinet_df[col])
    
    # Filter by date range
    cabinet_df = cabinet_df[
        (cabinet_df['government_incumbency_start_date'] >= pd.to_datetime(from_date)) |
        cabinet_df['government_incumbency_start_date'].isna()
    ]
    
    # Add prime minister information
    cabinet_df['prime_minister'] = cabinet_df['government_incumbency_start_date'].apply(
        lambda x: find_prime_minister(x, gov_timeline)
    )
    
    # Add parliament start date and parliament duration
    if len(parliaments_df) > 0:
        parliament_info = cabinet_df['government_incumbency_start_date'].apply(
            lambda x: pd.Series(find_parliament_dates(x, parliaments_df))
        )
        cabinet_df['parliament_start_date'] = parliament_info[0]
        cabinet_df['parliament_length_days'] = parliament_info[1]
    else:
        cabinet_df['parliament_start_date'] = None
        cabinet_df['parliament_length_days'] = None
    
    # Calculate tenure length in days
    cabinet_df['tenure_length_days'] = (
        pd.to_datetime(cabinet_df['government_incumbency_end_date']) - 
        pd.to_datetime(cabinet_df['government_incumbency_start_date'])
    ).dt.days
    
    # Select and order key columns
    key_columns = [
        'given_name',
        'family_name',
        'member_house',
        'position_name',
        'government_incumbency_start_date',
        'government_incumbency_end_date',
        'tenure_length_days',
        'parliament_start_date',
        'parliament_length_days',
        'party',
        'prime_minister',
        'person_id',
        'mnis_id'
    ]
    
    # Keep only columns that exist
    available_cols = [col for col in key_columns if col in cabinet_df.columns]
    cabinet_df = cabinet_df[available_cols]
    
    # Rename columns for clarity
    cabinet_df = cabinet_df.rename(columns={
        'position_name': 'post',
        'government_incumbency_start_date': 'start_date',
        'government_incumbency_end_date': 'end_date'
    })
    
    # Sort by date
    cabinet_df = cabinet_df.sort_values('start_date', na_position='last')
    
    # Filter to MIN_YEAR onwards
    cabinet_df['start_date_dt'] = pd.to_datetime(cabinet_df['start_date'])
    pre_filter_count = len(cabinet_df)
    cabinet_df = cabinet_df[cabinet_df['start_date_dt'].dt.year >= MIN_YEAR].reset_index(drop=True)
    cabinet_df = cabinet_df.drop(columns=['start_date_dt'])
    print(f"\nFiltered to {MIN_YEAR} onwards: {len(cabinet_df)} records (removed {pre_filter_count - len(cabinet_df)})")
    
    # Apply classification to posts
    print("Classifying posts...")
    classifications = cabinet_df['post'].apply(lambda p: classify_post(p, {}))
    cabinet_df['post_category'] = classifications.apply(lambda c: c.category)
    cabinet_df['is_senior'] = classifications.apply(lambda c: c.is_senior)
    
    print(f"\nTotal cabinet roles found: {len(cabinet_df)}")
    print(f"  Senior posts: {cabinet_df['is_senior'].sum()}")
    print(f"  Non-senior posts: {(~cabinet_df['is_senior']).sum()}")
    print(f"\nColumns: {list(cabinet_df.columns)}")
    
    if len(cabinet_df) > 0:
        print("\nFirst 10 records:")
        print(cabinet_df.head(10).to_string())
    
    # Save to file
    if output_file is None:
        # Create extract directory with timestamp
        base_dir = Path(__file__).parent
        ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        extract_dir = base_dir / f"extract_{ts}"
        extract_dir.mkdir(parents=True, exist_ok=True)
        output_file = extract_dir / "cabinet_ministers.csv"
    else:
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
    
    cabinet_df.to_csv(output_file, index=False)
    print(f"\n✓ Data saved to: {output_file}")
    
    return cabinet_df


def main():
    """Main entry point."""
    get_cabinet_ministers_datafile()


if __name__ == "__main__":
    main()
