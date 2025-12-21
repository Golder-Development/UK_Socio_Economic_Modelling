#!/usr/bin/env python3
"""
Regenerate all harmonized mortality data following the recommended workflow.

This script orchestrates the complete data regeneration pipeline:
1. Generate harmonized categories from keywords
2. Rebuild harmonized dataset from archive with override support
3. Generate audit crosswalk for review
4. Create interactive Plotly dashboards

Usage:
    python regenerate_all_data.py [--verbose] [--skip-rebuild] [--skip-dashboards]

Options:
    --verbose           Print detailed progress messages
    --skip-rebuild      Skip rebuilding harmonized dataset (fast iteration)
    --skip-dashboards   Skip dashboard generation (fastest)
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


def get_script_dir():
    """Get the development_code directory path."""
    return Path(__file__).parent


def get_parent_dir():
    """Get the mortality_stats parent directory."""
    return get_script_dir().parent


def run_script(script_name, description, verbose=False):
    """Run a Python script and report status."""
    script_path = get_script_dir() / script_name
    
    print(f"\n{'='*70}")
    print(f"STEP: {description}")
    print(f"{'='*70}")
    print(f"Running: {script_path.name}")
    
    if not script_path.exists():
        print(f"❌ ERROR: Script not found: {script_path}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(get_script_dir()),
            capture_output=not verbose,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if verbose and result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} failed with exit code {result.returncode}")
            if result.stderr:
                print("Error output:")
                print(result.stderr)
            if result.stdout:
                print("Standard output:")
                print(result.stdout)
            return False
    except Exception as e:
        print(f"❌ Exception running {script_name}: {e}")
        return False

def summarize_harmonized_output():
    """Print a quick summary of the harmonized output to verify categories."""
    try:
        out_path = get_parent_dir() / "uk_mortality_by_cause_1901_2000_harmonized.csv"
        if not out_path.exists():
            print(f"⚠️  Harmonized output not found: {out_path}")
            return
        import pandas as pd
        df = pd.read_csv(out_path)
        total = len(df)
        nulls = df['harmonized_category_name'].isna().sum() if 'harmonized_category_name' in df.columns else total
        uniq = df['harmonized_category_name'].nunique() if 'harmonized_category_name' in df.columns else 0
        print("\nHarmonized output summary:")
        print(f"  Rows: {total:,}")
        print(f"  Years: {df['year'].min()}–{df['year'].max()}")
        print(f"  Null category rows: {nulls:,}")
        print(f"  Unique categories: {uniq}")
        if 'harmonized_category_name' in df.columns:
            print("  Top categories:")
            print(df['harmonized_category_name'].value_counts().head(10))
    except Exception as e:
        print(f"⚠️  Could not summarize harmonized output: {e}")

def summarize_mapping_file():
    """Summarize the icd_harmonized_categories.csv to confirm category count."""
    try:
        mapping_path = get_parent_dir() / "icd_harmonized_categories.csv"
        if not mapping_path.exists():
            print(f"⚠️  Mapping file not found: {mapping_path}")
            return
        import pandas as pd
        m = pd.read_csv(mapping_path)
        cat_col = "harmonized_category_name" if "harmonized_category_name" in m.columns else None
        if cat_col:
            uniq = m[cat_col].nunique()
            print("\nHarmonized mapping summary:")
            print(f"  Total mappings: {len(m):,}")
            print(f"  Unique categories in mapping: {uniq}")
            print(m[cat_col].value_counts().head(10))
        else:
            print("⚠️  Mapping file missing 'harmonized_category_name' column")
    except Exception as e:
        print(f"⚠️  Could not summarize mapping file: {e}")


def check_prerequisites():
    """Verify required files exist."""
    print("\n" + "="*70)
    print("CHECKING PREREQUISITES")
    print("="*70)
    
    required_files = [
        "build_code_descriptions.py",
        "build_harmonized_categories.py",
        "rebuild_harmonized_from_archive.py",
        "build_crosstab_icd_harmonization.py",
        "create_interactive_mortality_dashboard.py",
    ]
    
    parent_dir = get_parent_dir()
    required_input_files = [
        parent_dir / "uk_mortality_comprehensive_1901_2019.csv",
        get_script_dir() / "icd_code_descriptions.csv",
    ]
    
    all_ok = True
    
    for fname in required_files:
        fpath = get_script_dir() / fname
        if fpath.exists():
            print(f"✅ {fname}")
        else:
            print(f"❌ {fname} - NOT FOUND")
            all_ok = False
    
    print()
    for fpath in required_input_files:
        if fpath.exists():
            print(f"✅ {fpath.name}")
        else:
            print(f"⚠️  {fpath.name} - NOT FOUND (may be generated or required)")
    
    return all_ok


def main():
    parser = argparse.ArgumentParser(
        description="Regenerate all harmonized mortality data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python regenerate_all_data.py                    # Full pipeline
  python regenerate_all_data.py --verbose          # With detailed output
  python regenerate_all_data.py --skip-dashboards  # Skip dashboards (faster)
  python regenerate_all_data.py --skip-rebuild     # Categories + dashboards only
        """
    )
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print detailed progress messages")
    parser.add_argument("--skip-rebuild", action="store_true",
                        help="Skip harmonized dataset rebuild")
    parser.add_argument("--skip-dashboards", action="store_true",
                        help="Skip dashboard generation")
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("MORTALITY DATA REGENERATION PIPELINE")
    print("="*70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Verbose: {args.verbose}")
    print(f"Skip rebuild: {args.skip_rebuild}")
    print(f"Skip dashboards: {args.skip_dashboards}")
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n⚠️  Some prerequisites missing, but continuing...")
    
    steps_completed = 0
    steps_failed = 0
    
    # STEP 1: Build harmonized categories
    # Ensure code descriptions exist; if missing, build them first
    desc_path = get_script_dir() / "icd_code_descriptions.csv"
    if not desc_path.exists():
        print("\nRunning prerequisite: build_code_descriptions.py (icd_code_descriptions.csv)")
        run_script(
            "build_code_descriptions.py",
            "Build ICD code descriptions",
            args.verbose
        )
    if not run_script(
        "build_harmonized_categories.py",
        "Generate 23-category harmonized mapping from keywords",
        args.verbose
    ):
        steps_failed += 1
    else:
        steps_completed += 1
        summarize_mapping_file()
    
    # STEP 2: Rebuild harmonized dataset
    if args.skip_rebuild:
        print("\n⏭️  SKIPPING: Rebuild harmonized dataset (--skip-rebuild)")
    else:
        if not run_script(
            "rebuild_harmonized_from_archive.py",
            "Rebuild harmonized dataset from archive with override support",
            args.verbose
        ):
            steps_failed += 1
        else:
            steps_completed += 1
            summarize_harmonized_output()
    
    # STEP 3: Generate audit crosswalk
    if not run_script(
        "build_crosstab_icd_harmonization.py",
        "Generate audit crosswalk table for code→category mappings",
        args.verbose
    ):
        steps_failed += 1
    else:
        steps_completed += 1
    
    # STEP 4: Create interactive dashboards
    if args.skip_dashboards:
        print("\n⏭️  SKIPPING: Create interactive dashboards (--skip-dashboards)")
    else:
        if not run_script(
            "create_interactive_mortality_dashboard.py",
            "Create interactive Plotly dashboards",
            args.verbose
        ):
            steps_failed += 1
        else:
            steps_completed += 1
    
    # Summary
    print("\n" + "="*70)
    print("REGENERATION PIPELINE COMPLETE")
    print("="*70)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Steps completed: {steps_completed}")
    if steps_failed > 0:
        print(f"Steps failed: {steps_failed} ❌")
    else:
        print(f"Steps failed: {steps_failed} ✅")
    
    # Output location summary
    parent_dir = get_parent_dir()
    print(f"\nOutput files written to: {parent_dir}")
    print("\nKey outputs:")
    print("  - icd_harmonized_categories.csv (mapping from build step 1)")
    print("  - uk_mortality_by_cause_1901_2000_harmonized.csv (from step 2)")
    print("  - icd_harmonization_crosswalk.csv (from step 3)")
    print("  - generated_charts/*.html (from step 4)")
    
    print("\nNext steps:")
    print("  1. Review icd_harmonization_crosswalk.csv to audit mappings")
    print("  2. Edit icd_harmonized_overrides.csv if adjustments needed")
    print("  3. Re-run this script to apply changes")
    print("  4. View dashboards in generated_charts/ folder")
    
    return 0 if steps_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
