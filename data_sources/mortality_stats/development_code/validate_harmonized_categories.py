"""
Validate harmonized categories against documentation.

This script:
1. Reads the icd_harmonized_categories.csv mapping
2. Extracts actual category count and list
3. Compares against documented values in README files
4. Reports discrepancies and updates recommendations

Run as part of the regeneration pipeline to ensure docs stay in sync.
"""

import pandas as pd
import logging
from pathlib import Path
import re
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent
REPO_ROOT = DATA_DIR.parent.parent

MAPPING_FILE = DATA_DIR / "icd_harmonized_categories.csv"
README_FILE = DATA_DIR / "HARMONIZED_CATEGORIES_README.md"
DEV_README_FILE = DATA_DIR / "development_code" / "README.md"


def extract_actual_categories() -> dict:
    """Extract actual categories from the harmonized mapping file."""
    if not MAPPING_FILE.exists():
        logger.error(f"Mapping file not found: {MAPPING_FILE}")
        return {}

    df = pd.read_csv(MAPPING_FILE)
    if "harmonized_category_name" not in df.columns:
        logger.error("No 'harmonized_category_name' column found in mapping file")
        return {}

    categories = sorted(df["harmonized_category_name"].unique())
    return {"count": len(categories), "list": categories}


def check_readme_categories() -> bool:
    """Check if README documents the correct number and list of categories."""
    actual = extract_actual_categories()
    if not actual:
        return False

    actual_count = actual["count"]
    actual_list = actual["list"]

    if not README_FILE.exists():
        logger.warning(f"README file not found: {README_FILE}")
        return False

    readme_text = README_FILE.read_text(encoding="utf-8")

    # Extract documented count from "### The 24 Standard Categories" or similar
    count_matches = re.findall(
        r"###\s+The\s+(\d+)\s+Standard Categories", readme_text
    )
    documented_count = int(count_matches[0]) if count_matches else None

    if documented_count is None:
        logger.warning("Could not find documented category count in README")
    elif documented_count != actual_count:
        logger.error(
            f"Category count mismatch: README says {documented_count}, actual is {actual_count}"
        )
        return False
    else:
        logger.info(f"✅ Category count matches: {actual_count}")

    # Check that each category is documented in the list
    readme_list_section = readme_text[readme_text.find("1. **") : readme_text.find("## Files Generated")]
    missing = []
    for i, cat in enumerate(actual_list, 1):
        if cat not in readme_text:
            missing.append((i, cat))

    if missing:
        logger.error(f"Categories in data but not in README: {missing}")
        return False
    else:
        logger.info(f"✅ All {actual_count} categories documented in README")

    return True


def check_dev_readme_categories() -> bool:
    """Check if development README mentions the correct category count."""
    actual = extract_actual_categories()
    if not actual:
        return False

    actual_count = actual["count"]

    if not DEV_README_FILE.exists():
        logger.warning(f"Dev README not found: {DEV_README_FILE}")
        return False

    readme_text = DEV_README_FILE.read_text(encoding="utf-8")

    # Look for "24-category" or similar
    count_matches = re.findall(r"(\d+)-category", readme_text)
    documented_counts = set(int(m) for m in count_matches)

    if not documented_counts:
        logger.warning("Could not find category count mention in dev README")
        return True

    if actual_count not in documented_counts:
        logger.error(
            f"Dev README mentions categories {documented_counts}, but actual is {actual_count}"
        )
        return False
    else:
        logger.info(f"✅ Dev README correctly references {actual_count} categories")

    return True


def generate_category_list() -> str:
    """Generate markdown-formatted list of actual categories."""
    actual = extract_actual_categories()
    if not actual:
        return ""

    categories = actual["list"]
    lines = [f"## The {len(categories)} Standard Categories\n"]
    for i, cat in enumerate(categories, 1):
        lines.append(f"{i}. **{cat}**")
    return "\n".join(lines)


def main():
    print("\n" + "=" * 70)
    print("HARMONIZED CATEGORIES VALIDATION")
    print("=" * 70)

    actual = extract_actual_categories()
    if not actual:
        logger.error("Failed to extract actual categories")
        return 1

    logger.info(f"\nActual categories in data: {actual['count']}")
    for i, cat in enumerate(actual["list"], 1):
        logger.info(f"  {i:2d}. {cat}")

    print("\n" + "-" * 70)
    print("Checking README documentation...")
    print("-" * 70)
    readme_ok = check_readme_categories()

    print("\n" + "-" * 70)
    print("Checking development README...")
    print("-" * 70)
    dev_readme_ok = check_dev_readme_categories()

    print("\n" + "=" * 70)
    if readme_ok and dev_readme_ok:
        logger.info("✅ ALL VALIDATIONS PASSED")
        print("=" * 70)
        return 0
    else:
        logger.error("❌ VALIDATION FAILED - Documentation needs update")
        print("=" * 70)
        print("\nTo fix discrepancies, regenerate with updated category counts:")
        print(f"  - Update {README_FILE} with actual count and list")
        print(f"  - Update {DEV_README_FILE} with correct count mention")
        print("\nExample category list for README:")
        print(generate_category_list())
        return 1


if __name__ == "__main__":
    sys.exit(main())
