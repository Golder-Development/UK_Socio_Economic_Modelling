from sl_core.utils.logger import logger


def determine_groups_optimized(df,
                               entity,
                               measure,
                               thresholds_dict,
                               exception_dict=None,
                               groupby_column=None):
    """
    Optimized version of group determination.

    Parameters:
        df (pd.DataFrame): DataFrame containing entity and measure columns.
        entity (str): Column name representing the entity.
        measure (str): Column name representing the numeric measure.
        thresholds_dict (dict): Dictionary mapping (low, high)
        tuples to group labels.
        exception_dict(dict): Dictionary mapping entity values to
            exception groups.
        groupby_column (str): Optional column to group by
            (e.g., 'parliamentary_sitting')
                             to calculate thresholds per group instead
                             of lifetime totals.
    Returns:
        pd.Series: A Series containing assigned groups for each row.
    """
    # Step 1: Compute total measure per entity (and optionally
    #   per groupby_column)
    if groupby_column and groupby_column in df.columns:
        entity_totals = df.groupby([entity, groupby_column],
                                   as_index=False)[measure].sum()
        merge_columns = [entity, groupby_column]
    else:
        entity_totals = df.groupby(entity, as_index=False)[measure].sum()
        merge_columns = [entity]
    entity_totals.rename(columns={measure: "total_measure"}, inplace=True)

    # Step 2: Assign groups based on thresholds or (exceptions)
    # if exception_dict is provided, use assign_group_with_exceptions
    # other wise use assign_group
    if exception_dict:
        # logger to show exception dict being used
        logger.debug(f"Group assignment with exceptions: {exception_dict}")
        entity_totals["group"] = entity_totals.apply(
            lambda row: assign_group_with_exceptions(
                row,
                thresholds_dict,
                row[entity],
                exception_dict
            ), axis=1
        )
    else:
        entity_totals["group"] = entity_totals.apply(
            lambda row: assign_group(
                row["total_measure"],
                thresholds_dict,
                row[entity]
            ),
            axis=1
        )

    # Step 3: Merge back into the original DataFrame
    merge_cols = merge_columns + ["group"]
    df = df.merge(entity_totals[merge_cols], on=merge_columns, how="left")
    logger.debug(f"Group assignment: {df['group'].value_counts()}")
    logger.debug(f"Group assignment: {entity_totals['group'].value_counts()}")

    # Step 4: Validate row count consistency
    if len(df) != len(df):
        logger.error(f"Length mismatch: original {len(df)}, merged {len(df)}")
        df.drop_duplicates(inplace=True)

        if len(df) != len(df):
            logger.critical(f"Mismatch after deduplication: original"
                            f" {len(df)}, merged {len(df)}")
            return None

    # Step 5: Return the group column
    return df["group"]


def assign_group(total, thresholds_dict, entity_value):
    """
    Assigns a group based on thresholds.
    If above the max threshold, returns the entity name.
    """
    for (low, high), group_name in thresholds_dict.items():
        if low <= total <= high:
            return group_name
    return entity_value  # Assign entity name if above max threshold


def assign_group_with_exceptions(row,
                                 thresholds_dict,
                                 entity_value,
                                 exception_dict):
    """
    Assigns a group based on thresholds and exceptions.
    If entity_value is a key in exception_dict, return the entity name
    instead of a threshold category (party exception).
    """
    # Check if this entity is in the exception dict (exact match)
    if exception_dict and entity_value in exception_dict:
        return entity_value

    # Otherwise, use threshold-based grouping
    return assign_group(row["total_measure"], thresholds_dict, entity_value)
