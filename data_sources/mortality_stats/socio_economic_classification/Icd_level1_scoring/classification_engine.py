"""
Generic Lexicon-Based Classification Engine
--------------------------------------------

A domain-agnostic, explainable classification system driven by weighted
lexicons and configurable hard override rules.

All domain-specific knowledge is externalized to settings.py, making this
engine reusable for any text classification task.

Author: (Paul Golder aka Hysnap)
"""

from __future__ import annotations

import os
import re
import argparse
from typing import Dict, List, Tuple, Optional
import pandas as pd

# Import all configuration from settings
from settings import (
    TAXONOMY,
    HARD_OVERRIDES,
    OVERRIDE_PRIORITY,
    CONFIDENCE_THRESHOLDS,
    INPUT_COLUMNS,
    DEFAULT_COLUMNS,
    DEFAULT_VERSION,
    OUTPUT_COLUMNS,
    DEFAULT_PATHS,
    LEXICON_SCHEMA,
    LEXICON_FILE_PATTERN,
    VALID_MATCH_TYPES,
    TEXT_NORMALIZATION,
)


# ------------------------------------------------------------
# Text utilities
# ------------------------------------------------------------

def normalise(text: str) -> str:
    """
    Normalize text according to settings configuration.

    Args:
        text: Input text string

    Returns:
        Normalized text string
    """
    text = str(text)

    if TEXT_NORMALIZATION.get("lowercase", True):
        text = text.lower()

    if TEXT_NORMALIZATION.get("replace_dash", True):
        text = text.replace("—", " ").replace("-", " ")

    if TEXT_NORMALIZATION.get("remove_punctuation", True):
        text = re.sub(r"[^\w\s]", " ", text)

    if TEXT_NORMALIZATION.get("collapse_whitespace", True):
        text = re.sub(r"\s+", " ", text).strip()

    return text


def matches(text: str, term: str, match_type: str) -> bool:
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
        return term in text.split()
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

def load_lexicons(lex_dir: str) -> Dict[str, List[dict]]:
    """
    Load all lexicon files from the specified directory.

    Args:
        lex_dir: Path to directory containing lexicon CSV files

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
        match = re.search(LEXICON_FILE_PATTERN, fn)
        if not match:
            continue

        code = match.group(1)

        # Only load lexicons for categories in taxonomy
        if code not in TAXONOMY:
            continue

        df = pd.read_csv(os.path.join(lex_dir, fn))

        rows = []
        for _, r in df.iterrows():
            term = str(r[LEXICON_SCHEMA["term_column"]]).strip().lower()
            weight = int(r[LEXICON_SCHEMA["weight_column"]])
            match_type = str(r[LEXICON_SCHEMA["match_type_column"]]).strip().lower()

            # Validate match type
            if match_type not in VALID_MATCH_TYPES:
                raise ValueError(
                    f"Invalid match_type '{match_type}' in {fn}. "
                    f"Must be one of: {VALID_MATCH_TYPES}"
                )

            rows.append({
                "term": term,
                "weight": weight,
                "match_type": match_type,
            })

        lexicons[code] = rows

    # Verify all taxonomy categories have lexicons
    missing = set(TAXONOMY.keys()) - set(lexicons.keys())
    if missing:
        raise ValueError(
            f"Missing lexicon files for taxonomy categories: {missing}\n"
            f"Expected files matching pattern: {LEXICON_FILE_PATTERN}"
        )

    return lexicons


# ------------------------------------------------------------
# Scoring logic
# ------------------------------------------------------------

def apply_hard_override(text: str) -> Optional[str]:
    """
    Check if text triggers any hard override rules.

    Hard overrides are checked in priority order defined in settings.

    Args:
        text: Normalized description text

    Returns:
        Category code if override triggered, None otherwise
    """
    # Check overrides in priority order
    for code in OVERRIDE_PRIORITY:
        if code not in HARD_OVERRIDES:
            continue

        for term, mtype in HARD_OVERRIDES[code]:
            if matches(text, term, mtype):
                return code

    # Also check any overrides not in priority list
    for code, patterns in HARD_OVERRIDES.items():
        if code in OVERRIDE_PRIORITY:
            continue
        for term, mtype in patterns:
            if matches(text, term, mtype):
                return code

    return None


def score_description(
    description: str, 
    lexicons: Dict[str, List[dict]]
) -> Tuple[str, Dict[str, int]]:
    """
    Score a description against all category lexicons.

    Args:
        description: Text description to classify
        lexicons: Loaded lexicon data

    Returns:
        Tuple of (best_category_code, scores_dict)
    """
    text = normalise(description)

    # Check for hard overrides first
    override = apply_hard_override(text)
    if override:
        # Create score dict with override marked
        scores = {c: 0 for c in TAXONOMY}
        scores[override] = CONFIDENCE_THRESHOLDS["hard_override_score"]
        return override, scores

    # Score against all lexicons
    scores = {c: 0 for c in TAXONOMY}

    for code, terms in lexicons.items():
        for t in terms:
            if matches(text, t["term"], t["match_type"]):
                scores[code] += t["weight"]

    # Select category with highest score
    best = max(scores.items(), key=lambda kv: kv[1])[0]
    return best, scores


def confidence_from_scores(scores: Dict[str, int]) -> str:
    """
    Determine confidence level based on score distribution.

    Args:
        scores: Dictionary of category codes to scores

    Returns:
        Confidence level: "high", "medium", or "low"
    """
    vals = sorted(scores.values(), reverse=True)
    top = vals[0]
    second = vals[1] if len(vals) > 1 else 0
    margin = top - second

    # Hard override always high confidence
    if top >= CONFIDENCE_THRESHOLDS["hard_override_score"]:
        return "high"

    # High confidence thresholds
    if (top >= CONFIDENCE_THRESHOLDS["high_min_score"] and 
        margin >= CONFIDENCE_THRESHOLDS["high_min_margin"]):
        return "high"

    # Medium confidence thresholds
    if (top >= CONFIDENCE_THRESHOLDS["medium_min_score"] and 
        margin >= CONFIDENCE_THRESHOLDS["medium_min_margin"]):
        return "medium"

    return "low"


# ------------------------------------------------------------
# DataFrame processing
# ------------------------------------------------------------

def find_column(df: pd.DataFrame, column_type: str) -> Optional[str]:
    """
    Find a column in the dataframe based on possible names.

    Args:
        df: Input dataframe
        column_type: Type of column to find (from INPUT_COLUMNS)

    Returns:
        Actual column name if found, None otherwise
    """
    possible_names = INPUT_COLUMNS.get(column_type, [])
    df_cols_lower = {c.lower(): c for c in df.columns}

    for name in possible_names:
        if name.lower() in df_cols_lower:
            return df_cols_lower[name.lower()]

    return None


def prepare_input_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare input dataframe with standardized column names.

    Args:
        df: Raw input dataframe

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
    code_col = find_column(df, "code")
    if code_col:
        df.rename(columns={code_col: DEFAULT_COLUMNS["code"]}, inplace=True)
    elif DEFAULT_COLUMNS["code"] not in df.columns:
        raise ValueError(
            f"Could not find code column. Expected one of: {INPUT_COLUMNS['code']}"
        )

    # Find or create description column
    desc_col = find_column(df, "description")
    if desc_col:
        df.rename(columns={desc_col: DEFAULT_COLUMNS["description"]}, inplace=True)
    elif DEFAULT_COLUMNS["description"] not in df.columns:
        # Try to concatenate multiple text columns
        other_cols = [
            c for c in df.columns 
            if c not in (DEFAULT_COLUMNS["code"], DEFAULT_COLUMNS["version"])
        ]
        if len(other_cols) >= 1:
            # Concatenate all non-code/version columns
            df[DEFAULT_COLUMNS["description"]] = df[other_cols].astype(str).agg(
                " — ".join, axis=1
            )
        else:
            raise ValueError(
                f"Could not find or create description column. "
                f"Expected one of: {INPUT_COLUMNS['description']}"
            )

    # Find or create version column
    version_col = find_column(df, "version")
    if version_col:
        df.rename(columns={version_col: DEFAULT_COLUMNS["version"]}, inplace=True)
    elif DEFAULT_COLUMNS["version"] not in df.columns:
        df[DEFAULT_COLUMNS["version"]] = DEFAULT_VERSION

    return df


def split_multi_codes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Split rows with comma-separated codes into multiple rows.

    Args:
        df: Input dataframe

    Returns:
        Dataframe with one code per row
    """
    code_col = DEFAULT_COLUMNS["code"]

    rows = []
    for _, r in df.iterrows():
        codes = [c.strip() for c in str(r[code_col]).split(",")]
        for c in codes:
            rr = r.copy()
            rr[code_col] = c
            rows.append(rr)

    return pd.DataFrame(rows)


def classify_dataframe(df: pd.DataFrame, lex_dir: str) -> pd.DataFrame:
    """
    Classify all rows in a dataframe.

    Args:
        df: Input dataframe with standardized columns
        lex_dir: Path to lexicon directory

    Returns:
        Dataframe with classification results
    """
    lexicons = load_lexicons(lex_dir)

    code_col = DEFAULT_COLUMNS["code"]
    desc_col = DEFAULT_COLUMNS["description"]
    version_col = DEFAULT_COLUMNS["version"]

    out = []
    for _, r in df.iterrows():
        category, scores = score_description(r[desc_col], lexicons)

        out.append({
            OUTPUT_COLUMNS["version"]: r[version_col],
            OUTPUT_COLUMNS["code"]: r[code_col],
            OUTPUT_COLUMNS["description"]: r[desc_col],
            OUTPUT_COLUMNS["category_code"]: category,
            OUTPUT_COLUMNS["category_name"]: TAXONOMY[category],
            OUTPUT_COLUMNS["confidence"]: confidence_from_scores(scores),
        })

    return pd.DataFrame(out)


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------

def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Generic lexicon-based text classification engine"
    )
    parser.add_argument(
        "--input_csv",
        default=DEFAULT_PATHS["input_csv"],
        help="Path to input CSV file"
    )
    parser.add_argument(
        "--lex_dir",
        default=DEFAULT_PATHS["lexicon_dir"],
        help="Path to directory containing lexicon CSV files"
    )
    parser.add_argument(
        "--output_csv",
        default=DEFAULT_PATHS["output_csv"],
        help="Path for output CSV file"
    )
    args = parser.parse_args()

    print(f"Loading input from: {args.input_csv}")
    df = pd.read_csv(args.input_csv)

    print("Preparing input data...")
    df = prepare_input_dataframe(df)

    print("Splitting multi-codes...")
    df = split_multi_codes(df)

    print(f"Classifying {len(df)} records...")
    result = classify_dataframe(df, args.lex_dir)

    # Create output directory if needed
    output_dir = os.path.dirname(args.output_csv)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Writing results to: {args.output_csv}")
    result.to_csv(args.output_csv, index=False)

    # Print summary
    print("\n=== Classification Summary ===")
    print(f"Total records classified: {len(result)}")
    print("\nCategory distribution:")
    print(result[OUTPUT_COLUMNS["category_code"]].value_counts().to_string())
    print("\nConfidence distribution:")
    print(result[OUTPUT_COLUMNS["confidence"]].value_counts().to_string())
    print("\n✓ Classification complete")


if __name__ == "__main__":
    main()
