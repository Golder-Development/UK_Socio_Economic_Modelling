from ._vendor.pdpy import pdpy

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
