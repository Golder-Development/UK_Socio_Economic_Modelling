"""
Build harmonized population data matching mortality_stats age group bins.

Input: 
  - combined_population_data.csv (1901-2000, detailed age ranges)
  - populations20012016.xls (2001-2016, age group format)
Output: uk_population_harmonized_age_groups.csv (1901-2016, standardized age bins)

Age groups: 0-4, 5-14, 15-24, 25-34, 35-44, 45-54, 55-64, 65-74, 75-84, 85+
This matches mortality_stats outputs for easy rate calculations.
"""

import pandas as pd
from pathlib import Path

def categorize_age(age_str):
    """Map detailed age ranges to standard demographic groups."""
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

def build_harmonized_population():
    """Load population data from CSV (1901-2000) and XLS (2001-2016) and aggregate to harmonized age groups."""
    
    print("\n" + "="*80)
    print("Loading 1901-2000 data from CSV...")
    print("="*80)
    
    # Load 1901-2000 from CSV
    csv_path = Path('data_sources/population/development_code/downloaded_sourcefiles/combined_population_data.csv')
    df_csv = pd.read_csv(csv_path)
    df_csv = df_csv[df_csv['YR'] <= 2000].copy()  # Keep only up to 2000
    
    print(f"  Loaded {len(df_csv):,} CSV records (1901-2000)")
    
    # Apply age group mapping to CSV data
    df_csv['age_group'] = df_csv['AGE'].apply(categorize_age)
    
    # Check for any "Unknown" mappings
    unknown_count = (df_csv['age_group'] == 'Unknown').sum()
    if unknown_count > 0:
        print(f"  ⚠️  {unknown_count} CSV records have unknown age mapping (will be excluded)")
    
    # Remove unknown age mappings
    df_csv_clean = df_csv[df_csv['age_group'] != 'Unknown'].copy()
    
    # Aggregate CSV data by year, sex, and age_group
    harmonized_csv = df_csv_clean.groupby(['YR', 'SEX', 'age_group'])['POP'].sum().reset_index()
    
    print("\n" + "="*80)
    print("Loading 2001-2016 data from XLS...")
    print("="*80)
    
    # Load 2001-2016 from XLS
    xls_path = Path('data_sources/population/development_code/downloaded_sourcefiles/populations20012016.xls')
    df_xls = pd.read_excel(xls_path, sheet_name='pops01-16')
    
    print(f"  Loaded {len(df_xls):,} XLS records (2001-2016)")
    
    # Apply age group mapping to XLS data (Agegroup is already in correct format)
    df_xls['age_group'] = df_xls['Agegroup'].apply(categorize_age)
    
    # Aggregate XLS data by year, sex, and age_group
    harmonized_xls = df_xls.groupby(['Year', 'Sex', 'age_group'])['Pops'].sum().reset_index()
    
    # Rename XLS columns to match CSV
    harmonized_xls = harmonized_xls.rename(columns={
        'Year': 'YR',
        'Sex': 'SEX',
        'Pops': 'POP'
    })
    
    print("\n" + "="*80)
    print("Combining 1901-2000 and 2001-2016 data...")
    print("="*80)
    
    # Combine both datasets
    harmonized = pd.concat([harmonized_csv, harmonized_xls], ignore_index=True)
    
    print(f"  Total records after combining: {len(harmonized):,}")
    print(f"  Year range: {harmonized['YR'].min()} - {harmonized['YR'].max()}")
    
    # Rename columns to match mortality_stats naming conventions
    harmonized = harmonized.rename(columns={
        'YR': 'year',
        'SEX': 'sex',
        'POP': 'population'
    })
    
    # Map sex codes to labels
    harmonized['sex'] = harmonized['sex'].map({1: 'Male', 2: 'Female'})
    
    # Order age groups logically
    age_group_order = ['0-4', '5-14', '15-24', '25-34', '35-44', '45-54', '55-64', '65-74', '75-84', '85+']
    harmonized['age_group'] = pd.Categorical(harmonized['age_group'], categories=age_group_order, ordered=True)
    
    # Sort by year, sex, age_group
    harmonized = harmonized.sort_values(['year', 'sex', 'age_group']).reset_index(drop=True)
    
    # Reorder columns
    harmonized = harmonized[['year', 'age_group', 'sex', 'population']]
    
    return harmonized

def main():
    print("="*80)
    print("Building Harmonized UK Population Data (Age Groups)")
    print("="*80)
    
    # Build harmonized data
    harmonized = build_harmonized_population()
    
    print(f"\nHarmonized data shape: {harmonized.shape}")
    print(f"Years: {harmonized['year'].min()} - {harmonized['year'].max()}")
    print(f"Age groups: {', '.join(str(ag) for ag in harmonized['age_group'].unique())}")
    print(f"Sex categories: {', '.join(harmonized['sex'].unique())}")
    
    # Save to population root folder
    output_path = Path('data_sources/population/uk_population_harmonized_age_groups.csv')
    print(f"\nSaving harmonized data to: {output_path}")
    harmonized.to_csv(output_path, index=False)
    
    print(f"✅ Successfully created harmonized population file ({len(harmonized):,} records)")
    
    # Display sample
    print("\nSample data (1901, all age groups, both sexes):")
    sample = harmonized[harmonized['year'] == 1901].sort_values(['sex', 'age_group'])
    print(sample.to_string(index=False))
    
    print("\nSample data (2016, all age groups, both sexes):")
    sample = harmonized[harmonized['year'] == 2016].sort_values(['sex', 'age_group'])
    print(sample.to_string(index=False))
    
    # Calculate totals by year (sample)
    print("\nTotal population by year (5-year intervals):")
    totals = harmonized.groupby('year')['population'].sum()
    for year in range(1901, 2017, 5):
        if year in totals.index:
            print(f"  {year}: {totals[year]:,}")
    
    # Final summary
    print("\n" + "="*80)
    print("✅ Harmonized population file creation complete!")
    print(f"   Coverage: 1901-2016 ({harmonized['year'].max() - harmonized['year'].min() + 1} years)")
    print(f"   Records: {len(harmonized):,}")
    print(f"   Age groups: {harmonized['age_group'].nunique()}")
    print("="*80)

if __name__ == '__main__':
    main()
