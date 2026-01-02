"""
Generic Lexicon-Based Classification Engine
--------------------------------------------

A domain-agnostic, explainable classification system driven by weighted
lexicons and configurable hard override rules.

All domain-specific knowledge is externalized to a settings module, making this
engine reusable for any text classification task.

Author: (Paul Golder aka Hysnap)
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd


# ------------------------------------------------------------
# Text utilities
# ------------------------------------------------------------

def normalise(text: str, text_normalization: Dict[str, bool]) -> str:
    """
    Normalize text according to settings configuration.

    Args:
        text: Input text string
        text_normalization: Configuration dict for normalization rules

    Returns:
        Normalized text string
    """
    text = str(text)

    if text_normalization.get("lowercase", True):
        text = text.lower()

    if text_normalization.get("replace_dash", True):
        text = text.replace("—", " ").replace("-", " ")

    if text_normalization.get("remove_punctuation", True):
        text = re.sub(r"[^\w\s]", " ", text)

    if text_normalization.get("collapse_whitespace", True):
        text = re.sub(r"\s+", " ", text).strip()

    return text


def matches(text: str, term: str, match_type: str, settings: Any = None) -> bool:
    """
    Check if a term matches text according to the specified match type.

    Args:
        text: Normalized text to search in
        term: Search term/pattern
        match_type: One of "token", "phrase", "substring", "regex"

    Returns:
        True if match found, False otherwise
    """
    if match_type == "token":
        tokens = set(text.split())

        enable_plural = True
        if settings is not None:
            enable_plural = getattr(settings, "TOKEN_MATCH_OPTIONS", {}).get(
                "enable_plural_variants", True
            )

        variants = {term}
        if enable_plural and len(term) > 2:
            if term.endswith("y") and not term.endswith("ay") and not term.endswith("ey"):
                variants.add(term[:-1] + "ies")
            if term.endswith("s"):
                variants.add(term[:-1])
            variants.add(term + "s")
            variants.add(term + "es")

        return any(v in tokens for v in variants)
    elif match_type == "phrase":
        return term in text
    elif match_type == "substring":
        return term in text
    elif match_type == "regex":
        return re.search(term, text) is not None
    else:
        raise ValueError(f"Unknown match_type: {match_type}")


# ------------------------------------------------------------
# Lexicon loading
# ------------------------------------------------------------

def load_lexicons(lex_dir: str, settings: Any) -> Dict[str, List[dict]]:
    """
    Load all lexicon files from the specified directory.

    Args:
        lex_dir: Path to directory containing lexicon CSV files
        settings: Settings module containing TAXONOMY and LEXICON_SCHEMA

    Returns:
        Dictionary mapping category codes to lists of lexicon entries

    Raises:
        ValueError: If lexicons are missing for any taxonomy category
    """
    lexicons: Dict[str, List[dict]] = {}

    if not os.path.exists(lex_dir):
        raise FileNotFoundError(f"Lexicon directory not found: {lex_dir}")

    for fn in os.listdir(lex_dir):
        if not fn.lower().endswith(".csv"):
            continue

        # Extract category code from filename
        match = re.search(settings.LEXICON_FILE_PATTERN, fn)
        if not match:
            continue

        code = match.group(1)

        # Only load lexicons for categories in taxonomy
        if code not in settings.TAXONOMY:
            continue

        df = pd.read_csv(os.path.join(lex_dir, fn))

        rows = []
        for _, r in df.iterrows():
            term = str(r[settings.LEXICON_SCHEMA["term_column"]]).strip()
            weight = int(r[settings.LEXICON_SCHEMA["weight_column"]])
            match_type = str(r[settings.LEXICON_SCHEMA["match_type_column"]]).strip().lower()

            # Validate match type
            if match_type not in settings.VALID_MATCH_TYPES:
                raise ValueError(
                    f"Invalid match_type '{match_type}' in {fn}. "
                    f"Must be one of: {settings.VALID_MATCH_TYPES}"
                )

            # Normalize lexicon terms using the same normalization as input text
            # This ensures phrases like "cirrhosis of liver (alcoholic)" match correctly
            term = normalise(term, settings.TEXT_NORMALIZATION)

            rows.append({
                "term": term,
                "weight": weight,
                "match_type": match_type,
            })

        lexicons[code] = rows

    # Verify all taxonomy categories have lexicons
    missing = set(settings.TAXONOMY.keys()) - set(lexicons.keys())
    if missing:
        raise ValueError(
            f"Missing lexicon files for taxonomy categories: {missing}\n"
            f"Expected files matching pattern: {settings.LEXICON_FILE_PATTERN}"
        )

    return lexicons


# ------------------------------------------------------------
# Scoring logic
# ------------------------------------------------------------

def apply_hard_override(text: str, settings: Any) -> Optional[str]:
    """
    Check if text triggers any hard override rules.

    Hard overrides are checked in priority order defined in settings.

    Args:
        text: Normalized description text
        settings: Settings module containing HARD_OVERRIDES and OVERRIDE_PRIORITY

    Returns:
        Category code if override triggered, None otherwise
    """
    exclusions = getattr(settings, "HARD_OVERRIDE_EXCLUSIONS", {})

    # Check overrides in priority order
    for code in settings.OVERRIDE_PRIORITY:
        if code not in settings.HARD_OVERRIDES:
            continue
        if any(matches(text, ex_term, ex_type, settings) for ex_term, ex_type in exclusions.get(code, [])):
            continue
        for term, mtype in settings.HARD_OVERRIDES[code]:
            if matches(text, term, mtype, settings):
                return code

    # Also check any overrides not in priority list
    for code, patterns in settings.HARD_OVERRIDES.items():
        if code in settings.OVERRIDE_PRIORITY:
            continue
        if any(matches(text, ex_term, ex_type, settings) for ex_term, ex_type in exclusions.get(code, [])):
            continue
        for term, mtype in patterns:
            if matches(text, term, mtype, settings):
                return code

    return None


def score_description(
    description: str, 
    lexicons: Dict[str, List[dict]],
    settings: Any
) -> Tuple[str, Dict[str, int]]:
    """
    Score a description against all category lexicons.

    Args:
        description: Text description to classify
        lexicons: Loaded lexicon data
        settings: Settings module containing configuration

    Returns:
        Tuple of (best_category_code, scores_dict)
    """
    text = normalise(description, settings.TEXT_NORMALIZATION)

    # Check for hard overrides first
    override = apply_hard_override(text, settings)
    if override:
        # Create score dict with override marked
        scores = {c: 0 for c in settings.TAXONOMY}
        scores[override] = settings.CONFIDENCE_THRESHOLDS["hard_override_score"]
        return override, scores

    # Score against all lexicons
    scores = {c: 0 for c in settings.TAXONOMY}

    for code, terms in lexicons.items():
        for t in terms:
            if matches(text, t["term"], t["match_type"], settings):
                scores[code] += t["weight"]

    # Select category with highest score
    best = max(scores.items(), key=lambda kv: kv[1])[0]
    return best, scores


def confidence_from_scores(scores: Dict[str, int], settings: Any) -> str:
    """
    Determine confidence level based on score distribution.

    Args:
        scores: Dictionary of category codes to scores
        settings: Settings module containing CONFIDENCE_THRESHOLDS

    Returns:
        Confidence level: "high", "medium", or "low"
    """
    vals = sorted(scores.values(), reverse=True)
    top = vals[0]
    second = vals[1] if len(vals) > 1 else 0
    margin = top - second

    # Hard override always high confidence
    if top >= settings.CONFIDENCE_THRESHOLDS["hard_override_score"]:
        return "high"

    # High confidence thresholds
    if (top >= settings.CONFIDENCE_THRESHOLDS["high_min_score"] and 
        margin >= settings.CONFIDENCE_THRESHOLDS["high_min_margin"]):
        return "high"

    # Medium confidence thresholds
    if (top >= settings.CONFIDENCE_THRESHOLDS["medium_min_score"] and 
        margin >= settings.CONFIDENCE_THRESHOLDS["medium_min_margin"]):
        return "medium"

    return "low"


# ------------------------------------------------------------
# DataFrame processing
# ------------------------------------------------------------

def find_column(df: pd.DataFrame, column_type: str, settings: Any) -> Optional[str]:
    """
    Find a column in the dataframe based on possible names.

    Args:
        df: Input dataframe
        column_type: Type of column to find (from INPUT_COLUMNS)
        settings: Settings module containing INPUT_COLUMNS

    Returns:
        Actual column name if found, None otherwise
    """
    possible_names = settings.INPUT_COLUMNS.get(column_type, [])
    df_cols_lower = {c.lower(): c for c in df.columns}

    for name in possible_names:
        if name.lower() in df_cols_lower:
            return df_cols_lower[name.lower()]

    return None


def prepare_input_dataframe(df: pd.DataFrame, settings: Any) -> pd.DataFrame:
    """
    Prepare input dataframe with standardized column names.

    Args:
        df: Raw input dataframe
        settings: Settings module containing column configuration

    Returns:
        Dataframe with standardized columns

    Raises:
        ValueError: If required columns cannot be found
    """
    # Make a copy to avoid modifying original
    df = df.copy()

    # Normalize column names
    df.columns = [c.lower().strip() for c in df.columns]

    # Find code column
    code_col = find_column(df, "code", settings)
    if code_col:
        df.rename(columns={code_col: settings.DEFAULT_COLUMNS["code"]}, inplace=True)
    elif settings.DEFAULT_COLUMNS["code"] not in df.columns:
        raise ValueError(
            f"Could not find code column. Expected one of: {settings.INPUT_COLUMNS['code']}"
        )

    # Find or create description column
    desc_col = find_column(df, "description", settings)
    if desc_col:
        df.rename(columns={desc_col: settings.DEFAULT_COLUMNS["description"]}, inplace=True)
    elif settings.DEFAULT_COLUMNS["description"] not in df.columns:
        # Try to concatenate multiple text columns
        other_cols = [
            c for c in df.columns 
            if c not in (settings.DEFAULT_COLUMNS["code"], settings.DEFAULT_COLUMNS["version"])
        ]
        if len(other_cols) >= 1:
            # Concatenate all non-code/version columns
            df[settings.DEFAULT_COLUMNS["description"]] = df[other_cols].astype(str).agg(
                " — ".join, axis=1
            )
        else:
            raise ValueError(
                f"Could not find or create description column. "
                f"Expected one of: {settings.INPUT_COLUMNS['description']}"
            )

    # Find or create version column
    version_col = find_column(df, "version", settings)
    if version_col:
        df.rename(columns={version_col: settings.DEFAULT_COLUMNS["version"]}, inplace=True)
    elif settings.DEFAULT_COLUMNS["version"] not in df.columns:
        df[settings.DEFAULT_COLUMNS["version"]] = settings.DEFAULT_VERSION

    return df


def split_multi_codes(df: pd.DataFrame, settings: Any) -> pd.DataFrame:
    """
    Split rows with comma-separated codes into multiple rows.

    Args:
        df: Input dataframe
        settings: Settings module containing DEFAULT_COLUMNS

    Returns:
        Dataframe with one code per row
    """
    code_col = settings.DEFAULT_COLUMNS["code"]

    rows = []
    for _, r in df.iterrows():
        codes = [c.strip() for c in str(r[code_col]).split(",")]
        for c in codes:
            rr = r.copy()
            rr[code_col] = c
            rows.append(rr)

    return pd.DataFrame(rows)


def classify_dataframe(df: pd.DataFrame, lex_dir: str, settings: Any) -> pd.DataFrame:
    """
    Classify all rows in a dataframe.

    Args:
        df: Input dataframe with standardized columns
        lex_dir: Path to lexicon directory
        settings: Settings module containing all configuration

    Returns:
        Dataframe with classification results
    """
    lexicons = load_lexicons(lex_dir, settings)

    code_col = settings.DEFAULT_COLUMNS["code"]
    desc_col = settings.DEFAULT_COLUMNS["description"]
    version_col = settings.DEFAULT_COLUMNS["version"]

    out = []
    for _, r in df.iterrows():
        category, scores = score_description(r[desc_col], lexicons, settings)

        out.append({
            settings.OUTPUT_COLUMNS["version"]: r[version_col],
            settings.OUTPUT_COLUMNS["code"]: r[code_col],
            settings.OUTPUT_COLUMNS["description"]: r[desc_col],
            settings.OUTPUT_COLUMNS["category_code"]: category,
            settings.OUTPUT_COLUMNS["category_name"]: settings.TAXONOMY[category],
            settings.OUTPUT_COLUMNS["confidence"]: confidence_from_scores(scores, settings),
        })

    return pd.DataFrame(out)
