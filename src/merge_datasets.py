"""
merge_datasets.py
-----------------
Merges ACS, NCES graduation, and NCES spending data into a single panel dataset.

Input files (from data/raw/):
  - acs_state_panel.csv
  - nces_graduation.csv
  - nces_spending.csv

Output file (to data/clean/):
  - merged_panel.csv - Combined dataset (not yet inflation-adjusted)

The script performs a series of left joins to combine all data sources,
preserving all state-year combinations from the base ACS dataset.
"""

import pandas as pd
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

# Get paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Input files
ACS_FILE = PROJECT_ROOT / "data" / "raw" / "acs_state_panel.csv"
GRADUATION_FILE = PROJECT_ROOT / "data" / "raw" / "nces_graduation.csv"
SPENDING_FILE = PROJECT_ROOT / "data" / "raw" / "nces_spending.csv"

# Output file
OUTPUT_DIR = PROJECT_ROOT / "data" / "clean"
OUTPUT_FILE = OUTPUT_DIR / "merged_panel.csv"

# ── Main Processing ───────────────────────────────────────────────────────────

def main():
    print("="*70)
    print("MERGING DATASETS")
    print("="*70)
    
    # Load datasets
    print("\nLoading datasets...")
    acs_df = pd.read_csv(ACS_FILE)
    print(f"  ✓ ACS data: {len(acs_df)} observations")
    print(f"    Columns: {list(acs_df.columns)}")
    
    grad_df = pd.read_csv(GRADUATION_FILE)
    print(f"  ✓ Graduation data: {len(grad_df)} observations")
    print(f"    Columns: {list(grad_df.columns)}")
    
    spend_df = pd.read_csv(SPENDING_FILE)
    print(f"  ✓ Spending data: {len(spend_df)} observations")
    print(f"    Columns: {list(spend_df.columns)}")
    
    # Verify merge keys
    print("\nVerifying merge keys (state_name and year)...")
    print(f"  ACS states: {acs_df['state_name'].nunique()}")
    print(f"  Graduation states: {grad_df['state_name'].nunique()}")
    print(f"  Spending states: {spend_df['state_name'].nunique()}")
    
    # Start with ACS data as base
    merged = acs_df.copy()
    print(f"\nStarting with ACS data: {len(merged)} observations")
    
    # Merge graduation data
    print("\nMerging graduation data...")
    merged = merged.merge(
        grad_df[['state_name', 'year', 'graduation_rate']],
        on=['state_name', 'year'],
        how='left',
        indicator='_merge_grad'
    )
    
    # Check merge results
    merge_counts = merged['_merge_grad'].value_counts()
    print(f"  Both (matched): {merge_counts.get('both', 0)}")
    print(f"  Left only (no graduation data): {merge_counts.get('left_only', 0)}")
    merged = merged.drop(columns=['_merge_grad'])
    
    # Merge spending data
    print("\nMerging spending data...")
    merged = merged.merge(
        spend_df[['state_name', 'year', 'per_pupil_spending']],
        on=['state_name', 'year'],
        how='left',
        indicator='_merge_spend'
    )
    
    # Check merge results
    merge_counts = merged['_merge_spend'].value_counts()
    print(f"  Both (matched): {merge_counts.get('both', 0)}")
    print(f"  Left only (no spending data): {merge_counts.get('left_only', 0)}")
    merged = merged.drop(columns=['_merge_spend'])
    
    # Sort by state and year
    merged = merged.sort_values(['state_name', 'year']).reset_index(drop=True)
    
    # Summary statistics
    print("\n" + "="*70)
    print("MERGED DATASET SUMMARY")
    print("="*70)
    
    print(f"\nShape: {merged.shape[0]} observations × {merged.shape[1]} variables")
    print(f"Years: {sorted(merged['year'].unique())}")
    print(f"States: {merged['state_name'].nunique()}")
    
    print(f"\nColumns in merged dataset:")
    for col in merged.columns:
        print(f"  - {col}")
    
    print(f"\nMissing values by variable:")
    missing = merged.isnull().sum()
    missing = missing[missing > 0]
    if len(missing) > 0:
        for var, count in missing.items():
            pct = (count / len(merged)) * 100
            print(f"  {var}: {count} ({pct:.1f}%)")
    else:
        print("  No missing values!")
    
    print(f"\nSample (first 10 rows):")
    print(merged[['year', 'state_name', 'graduation_rate', 
                  'per_pupil_spending', 'poverty_rate']].head(10))
    
    # Create output directory if needed
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save merged dataset
    merged.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\n{'='*70}")
    print(f"✓ Saved merged dataset to: {OUTPUT_FILE}")
    print(f"{'='*70}")
    
    print("""
NEXT STEP:
Run the inflation adjustment script (adjust_inflation.py) to convert
monetary values to constant 2019 dollars.
""")


if __name__ == "__main__":
    main()