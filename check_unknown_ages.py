import pandas as pd
import zipfile
from pathlib import Path

def categorize_age(age_str):
    """Map age ranges to standard demographic groups."""
    if pd.isna(age_str):
        return "Unknown"
    
    age_str = str(age_str).strip().replace('T', '')
    
    # Handle special cases
    if age_str == '<1' or age_str == '00' or age_str == '0':
        return "0-4"
    if age_str in ['85+', '80+', '90+']:
        return "85+"
    
    # Extract starting age from range (e.g., "01-04" -> 1, "25-29" -> 25)
    try:
        if '-' in age_str:
            start_age = int(age_str.split('-')[0])
        else:
            start_age = int(age_str)
        
        # Categorize based on starting age
        if start_age <= 4:
            return "0-4"
        elif start_age <= 14:
            return "5-14"
        elif start_age <= 24:
            return "15-24"
        elif start_age <= 34:
            return "25-34"
        elif start_age <= 44:
            return "35-44"
        elif start_age <= 54:
            return "45-54"
        elif start_age <= 64:
            return "55-64"
        elif start_age <= 74:
            return "65-74"
        elif start_age <= 84:
            return "75-84"
        else:
            return "85+"
    except (ValueError, IndexError):
        return "Unknown"

# Load data
zip_path = Path('data_sources/mortality_stats/uk_mortality_by_cause_1901_onwards.zip')
with zipfile.ZipFile(zip_path) as zf:
    df = pd.read_csv(zf.open('uk_mortality_by_cause_1901_onwards.csv'))

# Apply categorization
df['age_group'] = df['age'].apply(categorize_age)

# Check for Unknown
unknown_count = (df['age_group'] == 'Unknown').sum()
total_count = len(df)

print(f"Total records: {total_count:,}")
print(f"Records with 'Unknown' age group: {unknown_count:,}")
print(f"Percentage: {(unknown_count / total_count * 100):.4f}%")

print("\nAge group distribution:")
print(df['age_group'].value_counts().sort_index())

if unknown_count > 0:
    print("\nOriginal age values that mapped to 'Unknown':")
    unknown_ages = df[df['age_group'] == 'Unknown']['age'].unique()
    print(unknown_ages)
