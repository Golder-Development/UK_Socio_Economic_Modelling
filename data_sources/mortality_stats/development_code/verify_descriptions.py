import pandas as pd

df = pd.read_csv("uk_mortality_by_cause_1901_2025_with_descriptions.csv")

print("=" * 80)
print("Sample with descriptions from 1901-1910 (ICD-1):")
print("=" * 80)
sample = (
    df[df["year"].between(1901, 1910)][["year", "cause", "cause_description", "deaths"]]
    .drop_duplicates(subset=["cause"])
    .head(20)
)
print(sample.to_string(index=False))

print("\n" + "=" * 80)
print("Verification: Check if code 10.0 means same thing across different ICD versions")
print("=" * 80)

desc_df = pd.read_csv("icd_code_descriptions.csv")
code_10_desc = desc_df[desc_df["code"] == "10.0"][
    ["code", "description", "icd_version"]
]
print(code_10_desc.to_string(index=False))
