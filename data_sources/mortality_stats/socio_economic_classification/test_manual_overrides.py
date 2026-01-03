"""
Test Manual Overrides System
-----------------------------

Quick test to demonstrate the manual overrides functionality.
"""

import os
import sys
import pandas as pd

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)

from classifiers.lexicon_classifier.manual_overrides_handler import ManualOverridesHandler
import settings


def test_manual_overrides():
    """Test the manual overrides system."""
    
    print("=" * 70)
    print("Testing Manual Overrides System")
    print("=" * 70)
    
    # Create test data with missing descriptions
    test_data = pd.DataFrame({
        'icd_version': ['ICD-3', 'ICD-3', 'ICD-4', 'ICD-5'],
        'icd_code': ['999', '123', '456', '789'],
        'cause_description': ['', 'Existing description', '', ''],
    })
    
    print("\nTest Data (BEFORE manual overrides):")
    print(test_data)
    
    # Path to manual overrides
    overrides_path = os.path.join(
        os.path.dirname(__file__), 
        'inputs', 
        'manual_overrides.csv'
    )
    
    # Initialize handler
    print(f"\nLoading manual overrides from: {overrides_path}")
    handler = ManualOverridesHandler(overrides_path, settings)
    
    # Apply overrides (fill missing only)
    print("\nApplying manual overrides (fill missing only)...")
    result = handler.apply_to_dataframe(test_data, fill_missing_only=True)
    
    print("\nTest Data (AFTER manual overrides):")
    print(result)
    
    # Show statistics
    handler.print_summary()
    
    # Test that existing data is NOT overwritten
    print("\n" + "=" * 70)
    print("Validation Tests")
    print("=" * 70)
    
    existing_row = result[result['icd_code'] == '123'].iloc[0]
    if existing_row['cause_description'] == 'Existing description':
        print("✓ PASS: Existing description was NOT overwritten")
    else:
        print("✗ FAIL: Existing description was overwritten (should not happen!)")
    
    missing_row = result[result['icd_code'] == '999'].iloc[0]
    if pd.notna(missing_row.get('_manual_override')) and missing_row['_manual_override']:
        print("✓ PASS: Missing description was filled with manual override")
    else:
        print("✗ FAIL: Missing description was not filled")
    
    print("\n" + "=" * 70)
    print("Test Complete")
    print("=" * 70)


if __name__ == "__main__":
    test_manual_overrides()
