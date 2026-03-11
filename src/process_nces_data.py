"""
process_nces_data.py
--------------------
Processes NCES Excel files to extract graduation rates and per-pupil expenditure
data for all 50 states, 2010-2019.

Input files (must be in data/raw/):
  - tabn219.46.xls - Table 219.46: ACGR by state
  - tabn236.65.xlsx - Table 236.65: Current expenditure per pupil

Output files (saved to data/raw/):
  - nces_graduation.csv - Clean graduation rate data
  - nces_spending.csv - Clean per-pupil spending data

Note: NCES Excel files often have multiple header rows and footnotes.
This script is designed to handle the standard NCES table format.
"""

import pandas as pd
import os
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent  # Assumes script is in src/ folder

# File paths - adjust these if your filenames are slightly different
GRADUATION_FILE = PROJECT_ROOT / "data" / "raw" / "tabn219.46.xls"
SPENDING_FILE = PROJECT_ROOT / "data" / "raw" / "tabn236.65.xlsx"

# Years to extract
YEARS = list(range(2010, 2020))  # 2010-2019

# ── Helper Functions ──────────────────────────────────────────────────────────

def process_graduation_data(filepath: str) -> pd.DataFrame:
    """
    Process NCES Table 219.46 - ACGR by state.
    
    The table has:
    - Years in row 3 (0-indexed row 2) in merged cells
    - Each year label (like "2010-11") spans 2 columns
    - Data starts around row 6
    """
    print(f"Processing graduation data from: {filepath}")
    
    # First, read rows 2 and 4 (0-indexed) to get the year headers from multiple rows
    df_header = pd.read_excel(filepath, header=None, nrows=5)
    year_row_3 = df_header.iloc[2]  # Row 3 (0-indexed row 2)
    year_row_5 = df_header.iloc[4]  # Row 5 (0-indexed row 4)
    
    print("\nYear row 3:")
    print(year_row_3)
    print("\nYear row 5:")
    print(year_row_5)
    
    # Combine the two rows - use row 5 where it has values, otherwise use row 3
    year_row_combined = year_row_5.fillna(year_row_3)
    
    print("\nCombined year row:")
    print(year_row_combined)
    
    # Forward-fill to handle merged cells
    year_row_filled = year_row_combined.ffill()
    
    print("\nYear row after forward-fill:")
    print(year_row_filled)
    
    # Now read the actual data starting from row 6 (0-indexed row 5)
    df = pd.read_excel(filepath, header=None, skiprows=5)
    
    print("\nFirst few rows of data:")
    print(df.head())
    
    # Set the forward-filled year row as column names
    # Make column names unique by adding a suffix to duplicates
    cols = year_row_filled.tolist()
    seen = {}
    unique_cols = []
    for col in cols:
        if col in seen:
            seen[col] += 1
            unique_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            unique_cols.append(col)
    
    df.columns = unique_cols
    
    print(f"\nColumns after setting year headers: {df.columns.tolist()[:15]}")
    
    # First column should be state names
    state_col = df.columns[0]
    
    grad_data = []
    
    for idx, row in df.iterrows():
        state_name = row[state_col]
        
        # Skip non-state rows
        if pd.isna(state_name) or not isinstance(state_name, str):
            continue
        
        # Clean state name - remove footnote markers like \10\
        state_name_clean = state_name.strip()
        if '\\' in state_name_clean:
            state_name_clean = state_name_clean.split('\\')[0].strip()
        
        if state_name_clean in ["", "United States", "State", "1"]:
            continue
            
        # Extract data for each year 2010-2019
        for year in YEARS:
            # Try different possible formats for year labels
            possible_year_labels = [
                f"{year}-{str(year+1)[-2:]}",      # "2010-11"
                f"{year}- {str(year+1)[-2:]}",     # "2010- 11" (with space)
                f"{year} - {str(year+1)[-2:]}",    # "2010 - 11" (with spaces)
                f"{year}-{year+1}",                 # "2010-2011"
            ]
            
            # Also search for any column containing the year
            for col in df.columns:
                if pd.notna(col) and str(year) in str(col) and '-' in str(col):
                    if col not in possible_year_labels:
                        possible_year_labels.append(col)
            
            for year_label in possible_year_labels:
                if year_label in df.columns:
                    # Get the value for this year
                    grad_rate = row[year_label]
                    
                    if pd.notna(grad_rate):
                        try:
                            # Clean the value
                            grad_rate_str = str(grad_rate).replace('†', '').replace('‡', '').replace('\\', '').replace('---', '').strip()
                            if grad_rate_str and grad_rate_str != '':
                                grad_rate_clean = float(grad_rate_str)
                                grad_data.append({
                                    'year': year,
                                    'state_name': state_name_clean,
                                    'graduation_rate': grad_rate_clean
                                })
                                break
                        except ValueError:
                            pass
    
    result_df = pd.DataFrame(grad_data)
    print(f"\nExtracted {len(result_df)} state-year observations for graduation rates")
    return result_df


def process_spending_data(filepath: str) -> pd.DataFrame:
    """
    Process NCES Table 236.65 - Current expenditure per pupil by state.
    
    The table has:
    - Header information in rows 2-3 (rows 1-2 in 0-indexed)
    - Data starts at row 4 (row 3 in 0-indexed)
    """
    print(f"\nProcessing spending data from: {filepath}")
    
    # Read Excel file - skip first 2 rows of headers, use row 3 (index 2) as column names
    df = pd.read_excel(filepath, header=2)
    
    print("\nFirst few rows of spending data:")
    print(df.head())
    print(f"\nColumns: {df.columns.tolist()}")
    
    state_col = df.columns[0]
    
    spend_data = []
    
    for idx, row in df.iterrows():
        state_name = row[state_col]
        
        # Skip non-state rows
        if pd.isna(state_name) or not isinstance(state_name, str):
            continue
        
        # Clean state name - remove footnote markers
        state_name_clean = state_name.strip()
        if '\\' in state_name_clean:
            state_name_clean = state_name_clean.split('\\')[0].strip()
        
        if state_name_clean in ["", "United States", "State"]:
            continue
            
        for year in YEARS:
            # NCES uses school year format - spending for 2010 might be labeled "2009-10" or "2010-11"
            # We'll look for columns containing the year
            matching_cols = [col for col in df.columns if str(year) in str(col)]
            
            if matching_cols:
                per_pupil_spend = row[matching_cols[0]]
                
                # Clean the value
                if pd.notna(per_pupil_spend):
                    try:
                        # Remove commas, dollar signs, and other formatting
                        per_pupil_spend = float(str(per_pupil_spend).replace('$', '').replace(',', '').replace('†', '').replace('‡', '').replace('\\', '').strip())
                        spend_data.append({
                            'year': year,
                            'state_name': state_name_clean,
                            'per_pupil_spending': per_pupil_spend
                        })
                    except:
                        pass
    
    result_df = pd.DataFrame(spend_data)
    print(f"\nExtracted {len(result_df)} state-year observations for per-pupil spending")
    return result_df


def standardize_state_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize state names to match Census data format.
    Filter to only the 50 states (exclude DC, territories, and aggregates).
    """
    # List of the 50 US states (no DC, no territories)
    fifty_states = {
        'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
        'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
        'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
        'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
        'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
        'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
        'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
        'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
        'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
        'West Virginia', 'Wisconsin', 'Wyoming'
    }
    
    df = df[df['state_name'].notna()].copy()
    
    # Clean state names - remove footnote markers and extra whitespace
    df['state_name'] = df['state_name'].str.strip()
    
    # Remove anything after backslash (footnote markers like \10\)
    df['state_name'] = df['state_name'].str.split('\\').str[0].str.strip()
    
    # Filter to only the 50 states
    df = df[df['state_name'].isin(fifty_states)].copy()
    
    return df


# ── Main Processing ───────────────────────────────────────────────────────────

def main():
    # Check if files exist
    if not os.path.exists(GRADUATION_FILE):
        print(f"ERROR: Graduation file not found: {GRADUATION_FILE}")
        print("Please ensure the NCES Table 219.46 Excel file is in data/raw/")
        return
    
    if not os.path.exists(SPENDING_FILE):
        print(f"ERROR: Spending file not found: {SPENDING_FILE}")
        print("Please ensure the NCES Table 236.65 Excel file is in data/raw/")
        return
    
    # Process graduation data
    grad_df = process_graduation_data(GRADUATION_FILE)
    grad_df = standardize_state_names(grad_df)
    
    # Process spending data
    spend_df = process_spending_data(SPENDING_FILE)
    spend_df = standardize_state_names(spend_df)
    
    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("GRADUATION DATA SUMMARY")
    print("="*70)
    print(f"Shape: {grad_df.shape}")
    print(f"Years: {sorted(grad_df['year'].unique())}")
    print(f"States: {grad_df['state_name'].nunique()}")
    print(f"\nMissing values:\n{grad_df.isnull().sum()}")
    print(f"\nSample:\n{grad_df.head(10)}")
    
    print("\n" + "="*70)
    print("SPENDING DATA SUMMARY")
    print("="*70)
    print(f"Shape: {spend_df.shape}")
    print(f"Years: {sorted(spend_df['year'].unique())}")
    print(f"States: {spend_df['state_name'].nunique()}")
    print(f"\nMissing values:\n{spend_df.isnull().sum()}")
    print(f"\nSample:\n{spend_df.head(10)}")
    
    # ── Save ──────────────────────────────────────────────────────────────────
    grad_output = PROJECT_ROOT / "data" / "raw" / "nces_graduation.csv"
    spend_output = PROJECT_ROOT / "data" / "raw" / "nces_spending.csv"
    
    grad_df.to_csv(grad_output, index=False)
    spend_df.to_csv(spend_output, index=False)
    
    print(f"\n✓ Saved graduation data to: {grad_output}")
    print(f"✓ Saved spending data to: {spend_output}")
    
    print("""
NOTE: If the output looks incorrect or incomplete, you may need to adjust:
1. The header row number (currently set to 4, try 3 or 5)
2. The year column matching logic
3. State name filtering

Check the printed column names and first few rows above to diagnose issues.
""")


if __name__ == "__main__":
    main()