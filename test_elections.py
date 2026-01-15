import pdpy
import pandas as pd

# Try get_general_elections
print("=== Testing get_general_elections ===")
try:
    elections = pdpy.get_general_elections()
    print("Type:", type(elections))
    if isinstance(elections, dict):
        print("Keys:", list(elections.keys())[:10])
        # Show first few items
        for key in list(elections.keys())[:2]:
            val = elections[key]
            print(f"\n{key}: {val}")
    else:
        print("Shape:", elections.shape if hasattr(elections, 'shape') else 'N/A')
        print("Columns:", list(elections.columns) if hasattr(elections, 'columns') else 'N/A')
        if len(elections) > 0:
            print("\nFirst row:")
            for col in elections.columns:
                print(f"  {col}: {elections.iloc[0][col]}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Try fetch_commons_memberships which might have parliament dates
print("\n" + "="*80)
print("Checking fetch_commons_memberships...")
try:
    commons = pdpy.fetch_commons_memberships()
    print("Columns:", list(commons.columns))
    if len(commons) > 0:
        print("\nFirst row:")
        for col in commons.columns[:15]:
            print(f"  {col}: {commons.iloc[0][col]}")
except Exception as e:
    print(f"Error: {e}")
