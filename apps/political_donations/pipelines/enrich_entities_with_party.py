import pandas as pd
from _vendor.pdpy as pdpy


def load_mppartymemb_pypd(mppartymemb_fname: str = None):
    """Load MP party memberships data into session state."""
    try:
        # Load MP party memberships data
        mppartymemb_df = pd.read_csv(mppartymemb_fname)
        # Store MP party memberships data in session state
    except Exception as e:
        mppartymemb_df = pd.DataFrame()


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
    # Save final dataset
    mppartymemb_df.to_csv(st.session_state.mppartymemb_fname, index=False)
    return mppartymemb_df


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


def clean_political_party_data():
    # Load MP party memberships data
    load_mppartymemb_pypd()
    # Load original file
    df = pd.read_csv(st.session_state.original_data_fname)
    # Clean names and extract status
    df[["CleanedName", "Status"]] = df["RegulatedEntityName"].apply(
        lambda x: pd.Series(extract_status_and_clean_name(x))
    )
    # Assign PoliticalParty based off UK Parliament data
    # create pdpydf
    pdpydf = get_party_df_from_pdpy()
    # create unified name column on pdpydf
    pdpydf[["First_Last_Name", "Last_First_Name"]] = pdpydf.apply(
        lambda row: pd.Series(
            create_unified_name_column(row["given_name"], row["family_name"])
        ),
        axis=1,
    )
    # Assign PoliticalParty based off PdpY data
    df["PoliticalParty_pdpy"] = df.apply(
        lambda row: get_party_from_pdpy_df(pdpydf, row["CleanedName"]),
        axis=1,
    )
    # Save final dataset
    final_file_path = st.session_state.mp_party_memberships_file_path
    df.to_csv(final_file_path, index=False)
