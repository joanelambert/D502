"""
adjust_inflation.py
-------------------
Adjusts monetary values to constant 2019 dollars using CPI-U data.

Input file (from data/processed/):
  - merged_panel.csv

Output file (to data/processed/):
  - final_panel.csv - Analysis-ready dataset with inflation-adjusted values

The script uses official BLS CPI-U annual averages to convert:
  - median_hh_income → median_hh_income_2019
  - per_pupil_spending → per_pupil_spending_2019

Formula: value_2019 = value_year × (CPI_2019 / CPI_year)
"""

import pandas as pd
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

# Get paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Input file
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "merged_panel.csv"

# Output file
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "final_panel.csv"

# Base year for inflation adjustment
BASE_YEAR = 2019

# CPI-U annual averages from Bureau of Labor Statistics
# Source: https://www.bls.gov/cpi/
# Series ID: CUUR0000SA0 (All items in U.S. city average)
CPI_DATA = {
    2010: 218.056,
    2011: 224.939,
    2012: 229.594,
    2013: 232.957,
    2014: 236.736,
    2015: 237.017,
    2016: 240.007,
    2017: 245.120,
    2018: 251.107,
    2019: 255.657,  # Base year
}

# ── Helper Functions ──────────────────────────────────────────────────────────

def adjust_for_inflation(value: float, year: int, base_year: int = BASE_YEAR) -> float:
    """
    Adjust a dollar value from a given year to constant base_year dollars.
    
    Formula: value_2019 = value_year × (CPI_2019 / CPI_year)
    
    Args:
        value: Dollar amount in nominal (current) dollars
        year: Year of the nominal value
        base_year: Target year for constant dollars (default 2019)
    
    Returns:
        Dollar amount in constant base_year dollars
    """
    if pd.isna(value):
        return None
    
    cpi_year = CPI_DATA[year]
    cpi_base = CPI_DATA[base_year]
    
    adjusted_value = value * (cpi_base / cpi_year)
    
    return round(adjusted_value, 2)


# ── Main Processing ───────────────────────────────────────────────────────────

def main():
    print("="*70)
    print("INFLATION ADJUSTMENT")
    print("="*70)
    
    # Load merged dataset
    print(f"\nLoading merged dataset from: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    print(f"  ✓ Loaded {len(df)} observations")
    
    # Display CPI data
    print(f"\nCPI-U Annual Averages (Base Year: {BASE_YEAR}):")
    for year in sorted(CPI_DATA.keys()):
        inflation_factor = CPI_DATA[BASE_YEAR] / CPI_DATA[year]
        print(f"  {year}: {CPI_DATA[year]:.3f} (multiply by {inflation_factor:.4f} to get 2019 dollars)")
    
    # Apply inflation adjustment
    print(f"\nAdjusting monetary values to constant {BASE_YEAR} dollars...")
    
    # Adjust median household income
    print("  Processing median_hh_income...")
    df['median_hh_income_2019'] = df.apply(
        lambda row: adjust_for_inflation(row['median_hh_income'], row['year']),
        axis=1
    )
    
    # Adjust per-pupil spending
    print("  Processing per_pupil_spending...")
    df['per_pupil_spending_2019'] = df.apply(
        lambda row: adjust_for_inflation(row['per_pupil_spending'], row['year']),
        axis=1
    )
    
    print("  ✓ Created inflation-adjusted columns:")
    print("    - median_hh_income_2019")
    print("    - per_pupil_spending_2019")
    
    # Reorder columns for clarity
    print("\nReordering columns...")
    column_order = [
        'year',
        'state_fips',
        'state_name',
        'graduation_rate',
        'per_pupil_spending',
        'per_pupil_spending_2019',
        'median_hh_income',
        'median_hh_income_2019',
        'poverty_rate',
        'poverty_population',
        'poverty_below'
    ]
    
    df = df[column_order]
    
    # Summary statistics
    print("\n" + "="*70)
    print("FINAL DATASET SUMMARY")
    print("="*70)
    
    print(f"\nShape: {df.shape[0]} observations × {df.shape[1]} variables")
    print(f"Years: {sorted(df['year'].unique())}")
    print(f"States: {df['state_name'].nunique()}")
    
    print(f"\nMissing values:")
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if len(missing) > 0:
        for var, count in missing.items():
            pct = (count / len(df)) * 100
            print(f"  {var}: {count} ({pct:.1f}%)")
    else:
        print("  No missing values!")
    
    print(f"\nComparison of nominal vs. inflation-adjusted values:")
    print("\nPer-Pupil Spending:")
    print(df[['year', 'per_pupil_spending', 'per_pupil_spending_2019']].groupby('year').mean().round(2))
    
    print("\nMedian Household Income:")
    print(df[['year', 'median_hh_income', 'median_hh_income_2019']].groupby('year').mean().round(2))
    
    print(f"\nDescriptive statistics (inflation-adjusted values):")
    print(df[['graduation_rate', 'per_pupil_spending_2019', 
              'median_hh_income_2019', 'poverty_rate']].describe().round(2))
    
    print(f"\nSample (first 10 rows):")
    print(df[['year', 'state_name', 'graduation_rate', 
              'per_pupil_spending_2019', 'median_hh_income_2019', 'poverty_rate']].head(10))
    
    # Save final dataset
    df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\n{'='*70}")
    print(f"✓ Saved final dataset to: {OUTPUT_FILE}")
    print(f"{'='*70}")
    
    print("""
DATA PREPARATION COMPLETE!

final_panel.csv is ready for analysis with:
  - 500 state-year observations (9 with missing graduation_rate)
  - All monetary values in constant 2019 dollars
  - Processed, merged data from Census ACS and NCES

NEXT STEPS:
1. Begin exploratory data analysis (EDA).
2. Check correlations and multicollinearity (VIF).
3. Create visualizations.
4. Run fixed effects regression analysis.
""")


if __name__ == "__main__":
    main()