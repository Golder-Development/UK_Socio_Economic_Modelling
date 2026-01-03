"""
ICD Mortality Classification Script
------------------------------------

Convenience wrapper for classifying ICD mortality codes using the
centralized lexicon classification engine.

This script uses the generic classification engine with mortality-specific
settings and lexicons.

Usage:
    python classify_mortality.py --input_csv data.csv --output_csv results.csv
    python classify_mortality.py --input_csv data.csv --version ICD-1

    Or use defaults from settings:
    python classify_mortality.py
"""

import os
import sys
import argparse
import pandas as pd

# Add the project root to path to import centralized classifier
# Path: from socio_economic_classification up to project root (3 levels up)
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../..')
)
sys.path.insert(0, project_root)

from classifiers.lexicon_classifier import engine  # noqa: E402
from classifiers.lexicon_classifier.manual_overrides_handler import (
    ManualOverridesHandler  # noqa: E402
)

# Import local mortality-specific settings
import settings  # noqa: E402


def main():
    """Main entry point for mortality classification."""
    parser = argparse.ArgumentParser(
        description="Classify ICD mortality codes using lexicon-based engine"
    )
    parser.add_argument(
        "--input_csv",
        default=settings.DEFAULT_PATHS.get("input_csv", "data/input.csv"),
        help="Path to input CSV file containing ICD codes"
    )
    parser.add_argument(
        "--lex_dir",
        default=os.path.join(os.path.dirname(__file__), "lexicons"),
        help="Path to directory containing lexicon CSV files"
    )
    parser.add_argument(
        "--output_csv",
        default=settings.DEFAULT_PATHS.get("output_csv", "output/classified.csv"),
        help="Path for output CSV file"
    )
    parser.add_argument(
        "--version",
        default=None,
        help=(
            "Override version for all records (e.g., ICD-1, ICD-8, ICD-10). "
            "If not specified, uses version column from input or 'UNK'"
        )
    )
    parser.add_argument(
        "--manual_overrides",
        default=os.path.join(os.path.dirname(__file__), "inputs", "manual_overrides.csv"),
        help="Path to manual overrides CSV file for missing codes"
    )
    parser.add_argument(
        "--skip_manual_overrides",
        action="store_true",
        help="Skip loading and applying manual overrides"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("ICD Mortality Code Classification")
    print("=" * 60)
    print(f"\nLoading input from: {args.input_csv}")
    
    try:
        df = pd.read_csv(args.input_csv)
        print(f"Loaded {len(df)} records")
    except FileNotFoundError:
        print(f"ERROR: Input file not found: {args.input_csv}")
        sys.exit(1)

    print("\nPreparing input data...")
    df = engine.prepare_input_dataframe(df, settings)

    # Apply version override if specified
    if args.version:
        df[settings.DEFAULT_COLUMNS["version"]] = args.version
        print(f"Setting version to: {args.version}")

    # Load and apply manual overrides BEFORE classification
    manual_handler = None
    if not args.skip_manual_overrides:
        print("\nApplying manual overrides for missing codes...")
        manual_handler = ManualOverridesHandler(args.manual_overrides, settings)
        df = manual_handler.apply_to_dataframe(df, fill_missing_only=True)

        if manual_handler.applied_count > 0:
            print(f"  → {manual_handler.applied_count} missing code(s) filled with manual overrides")
        if manual_handler.skipped_count > 0:
            print(f"  → {manual_handler.skipped_count} override(s) skipped (code exists in source data)")

    print("\nSplitting multi-codes...")
    df = engine.split_multi_codes(df, settings)
    print(f"Expanded to {len(df)} records after splitting")

    print(f"\nClassifying against {len(settings.TAXONOMY)} categories...")
    print(f"Using lexicons from: {args.lex_dir}")

    result = None
    try:
        result = engine.classify_dataframe(df, args.lex_dir, settings)

        # Apply manual classifications for codes that were filled with manual overrides
        if manual_handler is not None:
            result = manual_handler.apply_classifications(result)
    except Exception as e:
        print(f"ERROR during classification: {e}")
        sys.exit(1)

    if result is None:
        print("ERROR: Classification produced no results")
        sys.exit(1)

    # Create output directory if needed
    output_dir = os.path.dirname(args.output_csv)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    print(f"\nWriting results to: {args.output_csv}")
    result.to_csv(args.output_csv, index=False)

    # Print summary
    print("\n" + "=" * 60)
    print("Classification Summary")
    print("=" * 60)
    print(f"\nTotal records classified: {len(result)}")
    
    print("\nCategory distribution:")
    category_counts = result[settings.OUTPUT_COLUMNS["category_code"]].value_counts()
    for code, count in category_counts.items():
        category_name = settings.TAXONOMY[code]
        print(f"  {code}: {count:4d} - {category_name}")
    
    print("\nConfidence distribution:")
    confidence_counts = result[settings.OUTPUT_COLUMNS["confidence"]].value_counts()
    # Show manual override statistics if applicable
    if manual_handler is not None and 'manual_classification' in result.columns:
        manual_count = result['manual_classification'].sum()
        if manual_count > 0:
            print(f"\nManual classifications applied: {manual_count}")
    
    for conf, count in confidence_counts.items():
        pct = 100 * count / len(result)
        print(f"  {conf:6s}: {count:4d} ({pct:5.1f}%)")
    
    print("\n" + "=" * 60)
    print("[OK] Classification complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
