"""
Merge PUSF and PublicFinances datasets into a single comprehensive economic dataset

Strategy:
- PublicFinances: 1801-1937 (before PUSF starts)
- PUSF: 1938-2024 (full PUSF coverage)
- Overlap: 1938-2023 (use PUSF as primary for common years)

Creates economic_data_combined_1800_2024.csv spanning 224 years with consistent schema:
  date_period | measure | cdid | value | unit | source_dataset | category
"""

import pandas as pd
from pathlib import Path


def merge_datasets():
    # Define paths
    pusf_long = Path(__file__).parent / 'pusf_long_format.csv'
    publicfinances_long = Path(__file__).parent / 'publicfinances_long_format.csv'
    output_file = Path(__file__).parent / 'economic_data_combined_1800_2024.csv'

    print("Loading datasets...")
    pusf_df = pd.read_csv(pusf_long)
    pf_df = pd.read_csv(publicfinances_long)

    # Add source_dataset column if not present
    if 'source_dataset' not in pusf_df.columns:
        pusf_df['source_dataset'] = 'PUSF'
    if 'source_dataset' not in pf_df.columns:
        pf_df['source_dataset'] = 'PublicFinances1800-2023'

    print("\nPUSF data:")
    print(f"  Shape: {pusf_df.shape}")
    print(f"  Date range: {pusf_df['date_period'].min()} - {pusf_df['date_period'].max()}")
    print(f"  Measures: {pusf_df['measure'].nunique()}")

    print("\nPublicFinances data:")
    print(f"  Shape: {pf_df.shape}")
    print(f"  Date range: {pf_df['date_period'].min()} - {pf_df['date_period'].max()}")
    print(f"  Measures: {pf_df['measure'].nunique()}")

    # Clean up date_period to ensure they're integers
    # Remove rows with NaN date_period first
    pusf_df = pusf_df[pusf_df['date_period'].notna()].copy()
    pf_df = pf_df[pf_df['date_period'].notna()].copy()

    pusf_df['date_period'] = pusf_df['date_period'].astype(int)
    pf_df['date_period'] = pf_df['date_period'].astype(int)

    # Split data by period
    # PublicFinances before 1938
    pf_before_1938 = pf_df[pf_df['date_period'] < 1938].copy()

    # PUSF data (1938+)
    pusf_all = pusf_df.copy()

    # PublicFinances overlapping period (for comparison)
    pf_overlap = pf_df[(pf_df['date_period'] >= 1938) & (pf_df['date_period'] <= 2023)].copy()

    print("\nData split:")
    print(f"  PublicFinances before 1938: {len(pf_before_1938)} rows")
    print(f"  PUSF (1938-2024): {len(pusf_all)} rows")
    print(f"  PublicFinances overlapping (1938-2023): {len(pf_overlap)} rows")

    # Check for overlapping measures in overlap period
    pusf_measures_overlap = set(pusf_df[pusf_df['date_period'] >= 1938]['measure'].unique())
    pf_measures_overlap = set(pf_overlap['measure'].unique())

    common_measures = pusf_measures_overlap.intersection(pf_measures_overlap)
    print(f"\nCommon measures in overlap period (1938-2023): {len(common_measures)}")
    if len(common_measures) > 0:
        print(f"  Sample common measures: {list(common_measures)[:3]}")

    # Combine: PublicFinances pre-1938 + PUSF (which covers 1938-2024)
    # For the overlap period, PUSF is the primary source (more detailed and current)
    combined_df = pd.concat([
        pf_before_1938,  # PublicFinances 1801-1937
        pusf_all         # PUSF 1938-2024 (includes overlap)
    ], ignore_index=True)

    # Sort and clean
    combined_df = combined_df.sort_values(['date_period', 'measure']).reset_index(drop=True)

    # Add category column if not present
    if 'category' not in combined_df.columns:
        combined_df['category'] = ''  # Will be populated based on measure type

    # Categorize measures
    def categorize_measure(measure, cdid, source):
        """Categorize measures based on known patterns"""
        measure_lower = str(measure).lower()

        # Tax receipts
        tax_terms = [
            'tax', 'income tax', 'national insurance', 'capital gains', 'death duties',
            'business rates', 'corporation tax', 'petroleum', 'vat', 'stamp duties',
            'excise', 'council tax'
        ]
        if any(term in measure_lower for term in tax_terms):
            return 'Tax Receipts'

        # Spending
        spending_terms = [
            'spending', 'expenditure', 'defence', 'health', 'education',
            'social security', 'pension'
        ]
        if any(term in measure_lower for term in spending_terms):
            return 'Government Spending'

        # Borrowing and debt
        elif any(term in measure_lower for term in ['borrowing', 'net debt', 'psnb', 'psnd', 'deficit', 'surplus']):
            return 'Fiscal Position'

        # Price indices and GDP
        elif any(term in measure_lower for term in ['retail price', 'rpi', 'gdp', 'price index', 'inflation']):
            return 'Economic Indicators'

        # Assets and liabilities (PUSF specific)
        elif any(term in measure_lower for term in ['asset', 'liability', 'equity', 'balance sheet']):
            return 'Balance Sheet'

        # Flows (PUSF specific)
        elif any(term in measure_lower for term in ['flow', 'transaction']):
            return 'Transactions'

        else:
            if source == 'PublicFinances1800-2023':
                return 'PublicFinances - Other'
            else:
                return 'PUSF - Other'

    combined_df['category'] = combined_df.apply(
        lambda row: categorize_measure(row['measure'], row['cdid'], row['source_dataset']),
        axis=1
    )

    # Save to CSV
    combined_df.to_csv(output_file, index=False)

    print("\n✓ Successfully merged datasets")
    print(f"Output: {output_file}")
    print(f"Shape: {combined_df.shape}")

    print("\nCombined data summary:")
    print(f"  Date range: {combined_df['date_period'].min()} - {combined_df['date_period'].max()}")
    print(f"  Total years: {combined_df['date_period'].nunique()}")
    print(f"  Unique measures: {combined_df['measure'].nunique()}")
    print(f"  Total rows: {len(combined_df)}")
    print(f"  Non-null values: {combined_df['value'].notna().sum()}")
    print(f"  Null values: {combined_df['value'].isna().sum()}")
    print(f"  Data completeness: {combined_df['value'].notna().sum() / len(combined_df) * 100:.1f}%")

    print("\nSource dataset breakdown:")
    print(combined_df['source_dataset'].value_counts())

    print("\nCategory breakdown:")
    print(combined_df['category'].value_counts())

    print("\nMeasures per source:")
    for source in combined_df['source_dataset'].unique():
        source_measures = combined_df[combined_df['source_dataset'] == source]['measure'].nunique()
        print(f"  {source}: {source_measures} measures")

    return combined_df


if __name__ == "__main__":
    combined_df = merge_datasets()
