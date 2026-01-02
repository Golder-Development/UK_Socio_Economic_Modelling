"""
Lexicon Validation Utility
---------------------------

Validates lexicon files for conflicts, duplicates, and potential issues.
Can be run as a standalone script or imported for use in tests.

Usage:
    python validate_lexicons.py --lex_dir path/to/lexicons --settings_module your.settings
"""

import os
import sys
import argparse
import pandas as pd
from collections import defaultdict
from typing import Dict, List, Tuple, Any


def validate_lexicons(lex_dir: str, settings: Any) -> Dict[str, List[str]]:
    """
    Validate lexicon files for conflicts and issues.
    
    Args:
        lex_dir: Path to lexicon directory
        settings: Settings module with TAXONOMY and LEXICON_SCHEMA
        
    Returns:
        Dictionary with issue categories as keys and lists of issues as values
    """
    issues = {
        "critical": [],
        "warnings": [],
        "info": []
    }
    
    # Load all lexicons
    lexicons = {}
    for fn in os.listdir(lex_dir):
        if not fn.lower().endswith(".csv"):
            continue
            
        code = None
        for cat_code in settings.TAXONOMY.keys():
            if cat_code in fn:
                code = cat_code
                break
                
        if not code:
            continue
            
        df = pd.read_csv(os.path.join(lex_dir, fn))
        lexicons[code] = {
            "filename": fn,
            "terms": []
        }
        
        for _, r in df.iterrows():
            term = str(r[settings.LEXICON_SCHEMA["term_column"]]).strip().lower()
            weight = int(r[settings.LEXICON_SCHEMA["weight_column"]])
            match_type = str(r[settings.LEXICON_SCHEMA["match_type_column"]]).strip().lower()
            
            lexicons[code]["terms"].append({
                "term": term,
                "weight": weight,
                "match_type": match_type
            })
    
    # Check 1: Duplicate terms within same lexicon
    for code, data in lexicons.items():
        term_counts = defaultdict(list)
        for entry in data["terms"]:
            key = (entry["term"], entry["match_type"])
            term_counts[key].append(entry["weight"])
            
        for (term, mtype), weights in term_counts.items():
            if len(weights) > 1:
                issues["critical"].append(
                    f"DUPLICATE in {code}: '{term}' ({mtype}) appears {len(weights)} times with weights {weights}"
                )
    
    # Check 2: Same term across multiple lexicons
    term_locations = defaultdict(list)
    for code, data in lexicons.items():
        for entry in data["terms"]:
            key = (entry["term"], entry["match_type"])
            term_locations[key].append((code, entry["weight"]))
    
    for (term, mtype), locations in term_locations.items():
        if len(locations) > 1:
            # Skip if one is negative (exclusion) - that's intentional
            weights = [w for _, w in locations]
            if all(w > 0 for w in weights):
                codes = [c for c, _ in locations]
                weight_str = ", ".join([f"{c}:{w}" for c, w in locations])
                issues["warnings"].append(
                    f"CROSS-LEXICON: '{term}' ({mtype}) in {len(locations)} lexicons: {weight_str}"
                )
    
    # Check 3: Substring/token overlap within same lexicon
    for code, data in lexicons.items():
        tokens = [e for e in data["terms"] if e["match_type"] == "token"]
        substrings = [e for e in data["terms"] if e["match_type"] == "substring"]
        
        for substr_entry in substrings:
            for token_entry in tokens:
                if substr_entry["term"] in token_entry["term"] or token_entry["term"] in substr_entry["term"]:
                    issues["warnings"].append(
                        f"SUBSTRING/TOKEN overlap in {code}: '{substr_entry['term']}' (substring) and '{token_entry['term']}' (token) may double-count"
                    )
    
    # Check 4: Positive and negative weights for related terms in same lexicon
    for code, data in lexicons.items():
        pos_terms = {e["term"] for e in data["terms"] if e["weight"] > 0}
        neg_terms = {e["term"] for e in data["terms"] if e["weight"] < 0}
        
        # Look for semantic overlaps
        for pos_term in pos_terms:
            for neg_term in neg_terms:
                if pos_term in neg_term or neg_term in pos_term:
                    issues["info"].append(
                        f"EXCLUSION PATTERN in {code}: positive '{pos_term}' and negative '{neg_term}'"
                    )
    
    # Check 5: Regex wildcards
    for code, data in lexicons.items():
        regex_terms = [e for e in data["terms"] if e["match_type"] == "regex"]
        if regex_terms:
            issues["info"].append(
                f"REGEX in {code}: {len(regex_terms)} regex patterns - ensure specificity"
            )
    
    return issues


def print_report(issues: Dict[str, List[str]]):
    """Print formatted validation report."""
    print("\n" + "=" * 70)
    print("LEXICON VALIDATION REPORT")
    print("=" * 70)
    
    if issues["critical"]:
        print(f"\n❌ CRITICAL ISSUES ({len(issues['critical'])}):")
        for issue in issues["critical"]:
            print(f"  • {issue}")
    else:
        print("\n✅ No critical issues found")
    
    if issues["warnings"]:
        print(f"\n⚠️  WARNINGS ({len(issues['warnings'])}):")
        for issue in issues["warnings"]:
            print(f"  • {issue}")
    else:
        print("\n✅ No warnings")
    
    if issues["info"]:
        print(f"\nℹ️  INFO ({len(issues['info'])}):")
        for issue in issues["info"]:
            print(f"  • {issue}")
    
    print("\n" + "=" * 70)
    
    # Summary
    total_issues = len(issues["critical"]) + len(issues["warnings"])
    if total_issues == 0:
        print("✅ All lexicons validated successfully - no conflicts found")
    else:
        print(f"⚠️  Found {total_issues} issues requiring attention")
    print("=" * 70 + "\n")


def main():
    """Main entry point for standalone execution."""
    parser = argparse.ArgumentParser(
        description="Validate lexicon files for conflicts and issues"
    )
    parser.add_argument(
        "--lex_dir",
        required=True,
        help="Path to lexicon directory"
    )
    parser.add_argument(
        "--settings_module",
        required=True,
        help="Python module path for settings (e.g., 'settings' or 'my.module.settings')"
    )
    
    args = parser.parse_args()
    
    # Import settings module
    sys.path.insert(0, os.path.dirname(os.path.abspath(args.lex_dir)))
    settings = __import__(args.settings_module)
    
    # Validate
    issues = validate_lexicons(args.lex_dir, settings)
    
    # Print report
    print_report(issues)
    
    # Exit with error code if critical issues found
    sys.exit(1 if issues["critical"] else 0)


if __name__ == "__main__":
    main()
