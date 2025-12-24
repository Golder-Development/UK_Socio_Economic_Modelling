"""
Shared utilities for building population identity extracts from ONS datasets.

Relies on helper functions in fetch_ons_data.py to discover datasets,
inspect dimensions, and retrieve observations.
"""
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd

from fetch_ons_data import (
    find_dataset_by_name,
    get_dimensions,
    get_latest_version_url,
    get_observations,
    load_datasets_csv,
    observations_to_dataframe,
)

logger = logging.getLogger(__name__)


@dataclass
class IdentityDataset:
    domain: str
    search_name: str
    category_keywords: List[str]
    geography_labels: List[str]
    notes: str


def _pick_dimension_name(dimensions: Dict[str, Dict[str, str]], keywords: List[str]) -> Optional[str]:
    lowered = {k.lower(): k for k in dimensions.keys()}
    for key_lower, original in lowered.items():
        if any(word in key_lower for word in keywords):
            return original
    return None


def _pick_option_id(options: Dict[str, str], preferred_labels: List[str]) -> str:
    for opt_id, label in options.items():
        label_lower = label.lower()
        if any(fragment.lower() in label_lower for fragment in preferred_labels):
            return opt_id
    return next(iter(options.keys()))


def _build_dimension_query(
    dimensions: Dict[str, Dict[str, str]],
    category_dim: str,
    geography_labels: List[str],
) -> Dict[str, str]:
    query: Dict[str, str] = {}
    for dim_name, options in dimensions.items():
        dim_lower = dim_name.lower()
        if dim_name == category_dim:
            query[dim_name] = "*"
        elif "time" in dim_lower:
            query[dim_name] = "*"
        elif "geo" in dim_lower or "area" in dim_lower or "region" in dim_lower:
            query[dim_name] = _pick_option_id(options, geography_labels)
        else:
            query[dim_name] = _pick_option_id(options, ["total", "all categories", "all persons"])
    return query


def _label_columns(df: pd.DataFrame, dimensions: Dict[str, Dict[str, str]]) -> pd.DataFrame:
    labelled = df.copy()
    for dim_name, options in dimensions.items():
        label_col = f"{dim_name}_label"
        labelled[label_col] = labelled[dim_name].map(options)
    return labelled


def _first_matching_column(columns: List[str], tokens: List[str]) -> Optional[str]:
    for col in columns:
        col_lower = col.lower()
        if any(token in col_lower for token in tokens):
            return col
    return None


def fetch_identity_split(
    dataset_cfg: IdentityDataset,
    datasets_df: pd.DataFrame,
    geo_dim_override: Optional[str] = None,
    geo_code_override: Optional[str] = None,
) -> Optional[pd.DataFrame]:
    dataset_row = find_dataset_by_name(datasets_df, dataset_cfg.search_name)
    if not dataset_row:
        return None

    edition_url = get_latest_version_url(dataset_row["url"])
    if not edition_url:
        return None

    dimensions = get_dimensions(edition_url)
    if not dimensions:
        logger.error("No dimensions available")
        return None

    category_dim = _pick_dimension_name(dimensions, dataset_cfg.category_keywords)
    if not category_dim:
        logger.error("Could not identify category dimension for %s", dataset_cfg.domain)
        return None

    query = _build_dimension_query(dimensions, category_dim, dataset_cfg.geography_labels)
    # Apply optional geography overrides
    if geo_dim_override and geo_code_override:
        if geo_dim_override in dimensions:
            query[geo_dim_override] = geo_code_override
            # Remove auto-selected geo dims to avoid conflicts
            for dim_name in list(query.keys()):
                if dim_name != category_dim and dim_name != geo_dim_override:
                    if any(tok in dim_name.lower() for tok in ("geo", "area", "region")):
                        query.pop(dim_name, None)
        else:
            logger.warning("Override geo dim '%s' not found in dimensions; using default selection", geo_dim_override)
    observations = get_observations(edition_url, query)
    if not observations:
        logger.error("No observations returned for %s", dataset_cfg.domain)
        return None

    df_raw = observations_to_dataframe(observations)
    df = _label_columns(df_raw, dimensions)

    df["domain"] = dataset_cfg.domain
    df["category_code"] = df[category_dim]
    df["category_label"] = df[f"{category_dim}_label"]

    geo_code_col = _first_matching_column(list(df.columns), ["geo", "region", "area"])
    geo_label_col = _first_matching_column([c for c in df.columns if c.endswith("_label")], ["geo", "region", "area"])
    time_col = _first_matching_column(list(df.columns), ["time"])

    if not geo_code_col or not geo_label_col:
        logger.error("Could not locate geography columns for %s", dataset_cfg.domain)
        return None

    df["geography_code"] = df[geo_code_col]
    df["geography_label"] = df[geo_label_col]
    df["time"] = df[time_col] if time_col else "2021"
    df["value"] = df["observation"].astype(float)
    df["share"] = df["value"] / df["value"].sum()

    columns = [
        "domain",
        "time",
        "geography_code",
        "geography_label",
        "category_code",
        "category_label",
        "value",
        "share",
    ]

    return df[columns]
