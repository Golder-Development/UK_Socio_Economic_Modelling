import pandas as pd
import streamlit as st
from sl_core.components.calculations import (
    count_unique_records,
    count_missing_values,
    count_null_values,
    get_top_or_bottom_entity_by_column
    )
from sl_core.components.filters import apply_filters
from sl_core.utils.logger import logger


# Convert placeholder date to datetime once
PLACEHOLDER_DATE = st.session_state.get("PLACEHOLDER_DATE")
PLACEHOLDER_ID = st.session_state.get("PLACEHOLDER_ID")


def count_donation_eventcout_values(df, column, filters=None):
    """Counts donations where a specific column has null (NaN) values."""
    df = apply_filters(df, filters)
    return df[column]["EventCount"].sum()


# Specific functions using the generic ones
def count_unique_donors(df, filters=None):
    """Counts unique donors based on a specific DonationType."""
    return count_unique_records(df, "DonorId", filters)


def get_impermissible_donors_ct(df, filters=None):
    return count_unique_donors(df, "Impermissible Donor", filters)


def get_unidentified_donors_ct(df, filters=None):
    return count_unique_donors(df, "Unidentified Donor", filters)


def get_blank_received_date_ct(df, filters=None):
    return count_missing_values(df, "ReceivedDate", PLACEHOLDER_DATE, filters)


def get_blank_regulated_entity_id_ct(df, filters=None):
    return count_missing_values(df, "PartyId", PLACEHOLDER_ID,
                                filters)


def get_blank_donor_id_ct(df, filters=None):
    return count_missing_values(df, "DonorId", PLACEHOLDER_ID, filters)


def get_blank_donor_name_ct(df, filters=None):
    return count_null_values(df, "DonorName", filters)


def get_dubious_donors(df, filters=None):
    filters = st.session_state["filter_def"].get("DubiousDonor_ftr")
    return apply_filters(df, filters)


def get_dubious_donors_ct(df, filters=None):
    """Calculates total dubious donors (impermissible + missing ID/name)."""
    return get_dubious_donors(df, filters)["EventCount"].sum()


def get_dubious_donors_value(df, filters=None):
    """Calculates total dubious donors (impermissible + missing ID/name)."""
    return get_dubious_donors(df, filters)["Value"].sum()


def get_dubious_donations(df, filters=None):
    filters = st.session_state["filter_def"].get("DubiousDonor_ftr")
    return apply_filters(df, filters)


def get_dubious_donation_actions(df, filters=None):
    return get_dubious_donations(df, filters)["EventCount"].sum()


def get_dubious_donation_value(df, filters=None):
    return get_dubious_donations(df, filters)["Value"].sum()


def get_donors_ct(df, filters=None):
    """Counts unique donors"""
    df = apply_filters(df, filters)
    return df["DonorId"].nunique()


def get_value_total(df, filters=None):
    """Sums total value of donations"""
    df = apply_filters(df, filters)
    return df["Value"].sum()


def get_value_mean(df, filters=None):
    """Mean of value of donations"""
    df = apply_filters(df, filters)
    return df["Value"].mean()


def get_donations_ct(df, filters=None):
    """Count of Donations"""
    df = apply_filters(df, filters)
    return df["EventCount"].sum()


def get_regentity_ct(df, filters=None):
    """Count of Regulated Entities"""
    df = apply_filters(df, filters)
    return df["PartyName"].nunique()


def get_mindate(df, filters=None):
    """Earliest date from data subset"""
    df = apply_filters(df, filters)
    df = df[df["ReceivedDate"] != pd.to_datetime(PLACEHOLDER_DATE)]
    return df["ReceivedDate"].min()


def get_maxdate(df, filters=None):
    """Most recent date from data subset"""
    df = apply_filters(df, filters)
    return df["ReceivedDate"].max()


def get_returned_donations_ct(df, filters=None):
    """Counts donations that have been returned."""
    retfilters = st.session_state["filter_def"].get("ReturnedDonation_ftr")
    df = apply_filters(df, retfilters)
    return df["EventCount"].sum()


def get_returned_donations_value(df, filters=None):
    """Calculates the total value of all returned donations."""
    df = apply_filters(df, filters)
    return df[df["DonationAction"] == "Returned"]["Value"].sum()


def get_datamindate():
    """Earliest date from full data"""
    df = st.session_state.get("data_clean", None)
    df = df[df["ReceivedDate"] != pd.to_datetime(PLACEHOLDER_DATE)]
    return df["ReceivedDate"].min()


def get_datamaxdate():
    """Most recent date from full data"""
    df = st.session_state.get("data_clean", None)
    return df["ReceivedDate"].max()


def get_donationtype_ct(df, filters=None):
    """Counts donations of a specified DonationType."""
    filtered_df = apply_filters(df, filters)
    return len(filtered_df)  # Ensure this returns an integer


def get_donationtype_value(df, filters=None):
    """Calculates the total value of all returned donations."""
    df = apply_filters(df, filters)
    return df.groupby("DonationType")["Value"].sum()


def get_donation_isanaggregate_ct(df, filters=None):
    """Counts donations are aggregated donations"""
    df = apply_filters(df, filters)
    return df["IsAnAggregate"]["EventCount"].sum()


def get_donation_isanaggregate_value(df, filters=None):
    """Calculates the total value of all aggregated donations."""
    df = apply_filters(df, filters)
    return df.groupby("IsAnAggregate")["Value"].sum()


def get_median_donation(df, filters=None):
    """Calculates the median donation value."""
    df = apply_filters(df, filters)
    return df["Value"].median()


def get_avg_donations_per_entity(df, filters=None):
    """Calculates the average number of donations per entity."""
    df = apply_filters(df, filters)
    return df.groupby("PartyId").size().mean()


def get_avg_value_per_entity(df, filters=None):
    """Calculates the average value of donations per entity."""
    df = apply_filters(df, filters)
    return df.groupby("PartyId")["Value"].mean().mean()


def get_avg_donors_per_entity(df, filters=None):
    """Calculates the average number of donors per entity."""
    df = apply_filters(df, filters)
    return df.groupby("PartyId")["DonorId"].nunique().mean()


def get_donors_stdev(df, filters=None):
    """Calculates the standard deviation of donors per entity."""
    df = apply_filters(df, filters)
    return df.groupby("PartyId").size().std()


def get_value_stdev(df, filters=None):
    """Calculates the standard deviation of value per entity."""
    df = apply_filters(df, filters)
    return df.groupby("PartyId")["Value"].mean().std()


def get_noofdonors_per_ent_stdev(df, filters=None):
    """Calculates the standard deviation of donors per entity."""
    df = apply_filters(df, filters)
    return df.groupby("PartyId")["DonorId"].nunique().std()


# Function to calculate key values
def compute_summary_statistics(df, filters):
    """Compute key statistics like total donations, mean, std, etc."""
    try:
        df = apply_filters(df, filters)
    except Exception as e:
        logger.error(f"Error applying filters: {e}")
        return {
            "unique_reg_entities": 0,
            "unique_donors": 0,
            "unique_donations": 0,
            "total_value": 0.0,
            "mean_value": 0.0,
            "avg_donations_per_entity": 0.0,
            "avg_value_per_entity": 0.0,
            "avg_donors_per_entity": 0.0,
            "donors_stdev": 0.0,
            "value_stdev": 0.0,
            "noofdonors_per_ent_stdev": 0.0,
            "most_common_entity": ("", 0.0),
            "most_valuable_entity": ("", 0.0),
            "least_common_entity": ("", 0.0),
            "least_valuable_entity": ("", 0.0),
            "most_common_donor": ("", 0.0),
            "most_valuable_donor": ("", 0.0)
            }

    if not isinstance(df, pd.DataFrame):
        raise ValueError("Filtered result is not a DataFrame")

    if df is None or df.empty:
        return {
            "unique_reg_entities": 0,
            "unique_donors": 0,
            "unique_donations": 0,
            "total_value": 0.0,
            "mean_value": 0.0,
            "avg_donations_per_entity": 0.0,
            "avg_value_per_entity": 0.0,
            "avg_donors_per_entity": 0.0,
            "donors_stdev": 0.0,
            "value_stdev": 0.0,
            "noofdonors_per_ent_stdev": 0.0,
            "most_common_entity": ("", 0.0),
            "most_valuable_entity": ("", 0.0),
            "least_common_entity": ("", 0.0),
            "least_valuable_entity": ("", 0.0),
            "most_common_donor": ("", 0.0),
            "most_valuable_donor": ("", 0.0),
        }

    regentity_ct = get_regentity_ct(df, filters)
    donors_ct = get_donors_ct(df, filters)
    donations_ct = get_donations_ct(df, filters)
    value_total = get_value_total(df, filters)
    value_mean = get_value_mean(df, filters)
    avg_donations_per_entity = get_avg_donations_per_entity(df, filters)
    avg_value_per_entity = get_avg_value_per_entity(df, filters)
    avg_donors_per_entity = get_avg_donors_per_entity(df, filters)
    donors_stdev = get_donors_stdev(df, filters)
    value_stdev = get_value_stdev(df, filters)
    noofdonors_per_ent_stdev = get_noofdonors_per_ent_stdev(df, filters)
    most_common_entity = get_top_or_bottom_entity_by_column(df=df,
                                                            column="PartyName",
                                                            value_column="EventCount",
                                                            top=True,
                                                            filters=filters)
    most_valuable_entity = get_top_or_bottom_entity_by_column(df=df,
                                                              column="PartyName",
                                                              value_column="Value",
                                                              top=True,
                                                              filters=filters)
    least_common_entity = get_top_or_bottom_entity_by_column(df=df,
                                                             column="PartyName",
                                                             value_column="EventCount",
                                                             top=False,
                                                             filters=filters)
    least_valuable_entity = get_top_or_bottom_entity_by_column(df=df,
                                                               column="PartyName",
                                                               value_column="Value",
                                                               top=False,
                                                               filters=filters)
    most_common_donor = get_top_or_bottom_entity_by_column(df=df,
                                                           column="DonorName",
                                                           value_column="EventCount",
                                                           top=True,
                                                           filters=filters)
    most_valuable_donor = get_top_or_bottom_entity_by_column(df=df,
                                                             column="DonorName",
                                                             value_column="Value",
                                                             top=True,
                                                             filters=filters)
    return {
        "unique_reg_entities": regentity_ct,
        "unique_donors": donors_ct,
        "unique_donations": donations_ct,
        "total_value": value_total,
        "mean_value": value_mean,
        "avg_donations_per_entity": avg_donations_per_entity,
        "avg_value_per_entity": avg_value_per_entity,
        "avg_donors_per_entity": avg_donors_per_entity,
        "donors_stdev": donors_stdev,
        "value_stdev": value_stdev,
        "noofdonors_per_ent_stdev": noofdonors_per_ent_stdev,
        "most_common_entity": most_common_entity,
        "most_valuable_entity": most_valuable_entity,
        "least_common_entity": least_common_entity,
        "least_valuable_entity": least_valuable_entity,
        "most_common_donor": most_common_donor,
        "most_valuable_donor": most_valuable_donor,
    }
