import pdpy
import pandas as pd

print("=== Testing pdpy government roles ===\n")

try:
    print("Fetching MPs...")
    mps = pdpy.fetch_mps()
    print(f"MPs columns: {list(mps.columns)}")
    print(f"MPs shape: {mps.shape}")
    print("\nFirst MP:")
    print(mps.iloc[0])
    print("\n" + "="*80 + "\n")
except Exception as e:
    print(f"Error fetching MPs: {e}\n")

try:
    print("Fetching MP government roles...")
    gov_roles = pdpy.fetch_mps_government_roles()
    print(f"Government roles columns: {list(gov_roles.columns)}")
    print(f"Government roles shape: {gov_roles.shape}")
    print("\nFirst government role:")
    print(gov_roles.iloc[0])
    print("\n" + "="*80 + "\n")
except Exception as e:
    print(f"Error fetching government roles: {e}\n")

try:
    print("Fetching MP party memberships...")
    party = pdpy.fetch_mps_party_memberships()
    print(f"Party memberships columns: {list(party.columns)}")
    print(f"Party memberships shape: {party.shape}")
    print("\nFirst party membership:")
    print(party.iloc[0])
except Exception as e:
    print(f"Error fetching party memberships: {e}\n")
