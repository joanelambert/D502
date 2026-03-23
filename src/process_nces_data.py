"""
process_nces_data.py
--------------------
Processes NCES Excel files to extract graduation rates and per-pupil expenditure
data for all 50 states, 2010-2019.

Input files:
  - tabn219.46.xls - Table 219.46: ACGR by state
  - tabn236.65.xlsx - Table 236.65: Current expenditure per pupil

Output files:
  - nces_graduation.csv - Clean graduation rate data
  - nces_spending.csv - Clean per-pupil spending data
"""

import pandas as pd

# CONFIGURATION

# Input files
GRADUATION_FILE = "../data/raw/tabn219.46.xls"
SPENDING_FILE = "../data/raw/tabn236.65.xlsx"

# Output files
GRAD_OUTPUT = "../data/raw/nces_graduation.csv"
SPEND_OUTPUT = "../data/raw/nces_spending.csv"

# Years to extract (2010-2019)
YEARS = list(range(2010, 2020))

# HELPER FUNCTIONS

def process_graduation_data(filepath: str) -> pd.DataFrame:
    """
    Process NCES Table 219.46 - ACGR by state.
    
    The table has:
    - Header information in rows 2-3 (rows 1-2 in 0-indexed)
    - Data starts at row 4 (row 3 in 0-indexed)
    - State names in the first column with possible footnote markers
    - Graduation rates with formatting (footnotes, special characters)
    - May contain non-state rows that need to be filtered out
    - Year columns may have different formats (e.g., "2010-11", "2010- 11", "2010-2011")
    """
    
    # Get the year headers from worksheet rows 3 and 5 (0-indexed)
    df_header = pd.read_excel(filepath, header=None, nrows=5)
    year_row_3 = df_header.iloc[2]
    year_row_5 = df_header.iloc[4]
    
    print("\nYear row 3:")
    print(year_row_3)
    print("\nYear row 5:")
    print(year_row_5)
    
    # Fill missing values from row 5 with values from row 3
    year_row_combined = year_row_5.fillna(year_row_3)
    
    print("\nCombined year row:")
    print(year_row_combined)
    
    # Forward-fill to handle merged cells
    year_row_filled = year_row_combined.ffill()
    
    print("\nYear row after forward-fill:")
    print(year_row_filled)
    
    # Read the data starting from row 6
    df = pd.read_excel(filepath, header=None, skiprows=5)
    
    print("\nFirst five rows of data:")
    print(df.head())
    
    # Name the year columns, add a suffix to duplicates
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
    
    # Put state names in the first column
    state_col = df.columns[0]
    
    grad_data = []
    
    for idx, row in df.iterrows():
        state_name = row[state_col]
        
        # Skip non-state rows
        if pd.isna(state_name) or not isinstance(state_name, str):
            continue
        
        # Remove footnote markers from state names
        state_name_clean = state_name.strip()
        if '\\' in state_name_clean:
            state_name_clean = state_name_clean.split('\\')[0].strip()
        
        if state_name_clean in ["", "United States", "State", "1"]:
            continue
            
        # Extract data for each year 2010-2019
        for year in YEARS:
            # Account for different year label formats
            possible_year_labels = [
                f"{year}-{str(year+1)[-2:]}",      # "2010-11"
                f"{year}- {str(year+1)[-2:]}",     # "2010- 11"
                f"{year} - {str(year+1)[-2:]}",    # "2010 - 11"
                f"{year}-{year+1}",                # "2010-2011"
            ]
            
            # Locate other year columns
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
                            # Clean the year value
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
        - Years in row 3 (0-indexed row 2) in merged cells
        - Data starts around row 6
        - State names in the first column with possible footnote markers
        - Per-pupil spending values with formatting (commas, dollar signs, footnotes)
        - May contain non-state rows that need to be filtered out
        - Year columns may have different formats (e.g., "2010-11", "2010- 11", "2010-2011")
    """
    print(f"\nProcessing spending data from: {filepath}")
    
    # Use row 3 as column names
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
        
        # CRemove footnote markers from state names
        state_name_clean = state_name.strip()
        if '\\' in state_name_clean:
            state_name_clean = state_name_clean.split('\\')[0].strip()
        
        if state_name_clean in ["", "United States", "State"]:
            continue
            
        for year in YEARS:
            # Locate the year column
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
    """
    # List of the 50 US states
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
    
    # Remove extra whitespace from state names
    df['state_name'] = df['state_name'].str.strip()
    
    # Remove footnote markers from state names
    df['state_name'] = df['state_name'].str.split('\\').str[0].str.strip()
    
    # Filter to only the 50 states
    df = df[df['state_name'].isin(fifty_states)].copy()
    
    return df


# MAIN PROCESSING FUNCTION

def main():
    
    # Process graduation data
    grad_df = process_graduation_data(GRADUATION_FILE)
    grad_df = standardize_state_names(grad_df)
    
    # Process spending data
    spend_df = process_spending_data(SPENDING_FILE)
    spend_df = standardize_state_names(spend_df)
    
    # Summarize the datasets
    print("\n" + "="*70)
    print("Graduation Data Summary")
    print("="*70)
    print(f"Shape: {grad_df.shape}")
    print(f"Years: {sorted(grad_df['year'].unique())}")
    print(f"States: {grad_df['state_name'].nunique()}")
    print(f"\nMissing values:\n{grad_df.isnull().sum()}")
    print(f"\nSample:\n{grad_df.head(10)}")
    
    print("\n" + "="*70)
    print("Spending Data Summary")
    print("="*70)
    print(f"Shape: {spend_df.shape}")
    print(f"Years: {sorted(spend_df['year'].unique())}")
    print(f"States: {spend_df['state_name'].nunique()}")
    print(f"\nMissing values:\n{spend_df.isnull().sum()}")
    print(f"\nSample:\n{spend_df.head(10)}")
    
    # Save the output files
    grad_df.to_csv(GRAD_OUTPUT, index=False)
    print(f"\nSaved graduation data to: {GRAD_OUTPUT}")

    spend_df.to_csv(SPEND_OUTPUT, index=False)
    print(f"Saved spending data to: {SPEND_OUTPUT}")


if __name__ == "__main__":
    main()