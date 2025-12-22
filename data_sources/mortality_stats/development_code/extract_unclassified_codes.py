"""
Extract unclassified codes from harmonized crosswalk and format for override CSV.
This helps identify codes that need manual classification review.
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CROSSWALK = BASE_DIR / "icd_harmonization_crosswalk.csv"
OUTPUT = BASE_DIR / "development_code" / "unclassified_codes_for_review.csv"


def main():
    print("=" * 80)
    print("EXTRACTING UNCLASSIFIED CODES FOR REVIEW")
    print("=" * 80)
    
    if not CROSSWALK.exists():
        print(f"❌ Crosswalk file not found: {CROSSWALK}")
        print("   Run 'python regenerate_all_data.py' first to generate the crosswalk.")
        return
    
    # Load the crosswalk
    print(f"\nLoading crosswalk from: {CROSSWALK.name}")
    df = pd.read_csv(CROSSWALK)
    print(f"Total codes in crosswalk: {len(df):,}")
    
    # Filter for unclassified/unknown
    unclassified_categories = [
        "Other and Unclassified",
        "Unknown/Unclassified",
        "other",
        "ill_defined"
    ]
    
    # Check both category name and category ID
    mask = (
        df["harmonized_category_name"].isin(unclassified_categories) |
        df["harmonized_category"].isin(unclassified_categories)
    )
    
    unclassified = df[mask].copy()
    print(f"Unclassified codes found: {len(unclassified):,}")
    
    if len(unclassified) == 0:
        print("✅ No unclassified codes found! All codes are properly categorized.")
        return
    
    # Show breakdown by ICD version
    print("\n📊 Breakdown by ICD version:")
    version_counts = unclassified["icd_version"].value_counts().sort_index()
    for version, count in version_counts.items():
        print(f"  {version:30s}: {count:5,} codes")
    
    # Prepare for override format
    # Columns needed: code, icd_version, harmonized_category, harmonized_category_name, classification_confidence
    override_template = unclassified[[
        "cause",
        "icd_version",
        "cause_description",
        "harmonized_category",
        "harmonized_category_name"
    ]].copy()
    
    # Rename cause to code for consistency with override format
    override_template = override_template.rename(columns={"cause": "code"})
    
    # Add classification_confidence placeholder (user will set this)
    override_template["classification_confidence"] = "override"
    
    # Add a notes column with original description for reference
    override_template["notes"] = (
        "REVIEW NEEDED - Original: " + override_template["cause_description"]
    )
    
    # Reorder columns to match override CSV format
    output_df = override_template[[
        "code",
        "icd_version",
        "harmonized_category",
        "harmonized_category_name",
        "classification_confidence",
        "notes"
    ]]
    
    # Sort by ICD version and code
    output_df = output_df.sort_values(["icd_version", "code"])
    
    # Save to file
    output_df.to_csv(OUTPUT, index=False)
    print(f"\n✅ Saved unclassified codes to: {OUTPUT}")
    print(f"\nNext steps:")
    print(f"  1. Review {OUTPUT.name}")
    print(f"  2. For each code, determine the correct harmonized_category")
    print(f"  3. Copy rows to icd_harmonized_overrides.csv (remove 'notes' column)")
    print(f"  4. Re-run 'python regenerate_all_data.py' to apply overrides")
    
    # Show sample of output
    print(f"\n📋 Sample of unclassified codes (first 10 by ICD version):")
    sample = output_df.head(10)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    print(sample.to_string(index=False))
    
    # Summary by category
    print(f"\n📊 Current incorrect classifications:")
    cat_counts = output_df["harmonized_category_name"].value_counts()
    for cat, count in cat_counts.items():
        print(f"  {cat:50s}: {count:5,} codes")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
