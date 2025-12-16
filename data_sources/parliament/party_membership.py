from ._vendor.pdpy import pdpy
import pandas as pd
from pathlib import Path

""" Given dates returns a tidy DataFrame
of UK MP's and their parties over time"""


# Function to query PdPy api
def get_party_df_from_pdpy(
    from_date="2001-01-01",
    to_date="2024-12-31",
    while_mp=False,
    collapse=True
        ):
    mppartymemb_df = pdpy.fetch_mps_party_memberships(
        from_date=from_date,
        to_date=to_date,
        while_mp=while_mp,
        collapse=collapse
    )
    # feedback
    mppartymemb_df = mppartymemb_df.drop(columns=["person_id", "party_id"])
    return mppartymemb_df


# procedure to create unified name column for mp party membership data
def create_unified_name_column(given_name, family_name):
    First_Last_Name = given_name + " " + family_name
    Last_First_Name = family_name + " " + given_name
    return First_Last_Name, Last_First_Name


# Function to determine party based on name
def get_party_from_pdpy_df(pdpydf, name):
    if pdpydf is not None:
        party = pdpydf.loc[pdpydf["First_Last_Name"] == name,
                           "party_name"].values
        if party.size > 0:
            return party[0]
        else:
            party = pdpydf.loc[pdpydf["display_name"] == name,
                               "party_name"].values
            if party.size > 0:
                return party[0]
        return "Unknown"
    else:
        return "Issue with PdPy data"


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
    """Demo: fetch and save MP party memberships data."""
    print("Fetching MP party memberships...")
    try:
        party_df = get_party_df_from_pdpy()
        print(f"Retrieved {len(party_df)} party memberships")
        
        if len(party_df) > 0:
            extract_dir = _most_recent_extract_dir()
            output_file = extract_dir / "mps_party_memberships.csv"
            party_df.to_csv(output_file, index=False)
            print(f"✓ Data saved to: {output_file}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
