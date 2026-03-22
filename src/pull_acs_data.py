"""
pull_acs_data.py
----------------
Pulls American Community Survey 1-year estimates for all 50 US states, 2010-2019,
for the following variables:
  - Median household income
  - Poverty rate: % of people below poverty level

Output: acs_state_panel.csv — a clean state-year panel dataset
"""

import requests
import pandas as pd
import time

# Configuration

API_KEY = "4f995e6a9a94315d0aa92eca682e2dfaf1838145"

# Years to pull
YEARS = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019]

# Variables to request from the ACS API
# B19013_001E = Median household income in the past 12 months (inflation-adjusted dollars)
# B17001_001E = Total population for whom poverty status is determined
# B17001_002E = Number of people below poverty level
# NAME        = State name
VARIABLES = "NAME,B19013_001E,B17001_001E,B17001_002E"

BASE_URL = "https://api.census.gov/data/{year}/acs/acs1"

# Helper Functions

def fetch_acs_year(year: int, api_key: str) -> pd.DataFrame:
    """
    Fetch ACS 1-year estimates for all states for a given year.
    Returns a DataFrame with columns: year, state_fips, state_name,
    median_hh_income, poverty_population, poverty_below, poverty_rate.
    """
    url = BASE_URL.format(year=year)
    params = {
        "get": VARIABLES,
        "for": "state:*",   # All states
        "key": API_KEY
    }

    response = requests.get(url, params=params, timeout=30)

    if response.status_code != 200:
        print(f"  WARNING: HTTP {response.status_code} for year {year}. Skipping.")
        return pd.DataFrame()

    data = response.json()

    # First row is the header
    headers = data[0]
    rows = data[1:]

    df = pd.DataFrame(rows, columns=headers)

    # Rename columns for clarity
    df = df.rename(columns={
        "NAME":         "state_name",
        "B19013_001E":  "median_hh_income",
        "B17001_001E":  "poverty_population",
        "B17001_002E":  "poverty_below",
        "state":        "state_fips"
    })

    # Add year column
    df["year"] = year

    # Convert numeric columns from strings
    numeric_cols = ["median_hh_income", "poverty_population", "poverty_below"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Calculate poverty rate as a percentage
    df["poverty_rate"] = (df["poverty_below"] / df["poverty_population"] * 100).round(2)

    # Flag missing or suppressed income values
    df.loc[df["median_hh_income"] < 0, "median_hh_income"] = None

    return df[["year", "state_fips", "state_name", "median_hh_income",
               "poverty_population", "poverty_below", "poverty_rate"]]


def filter_50_states(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retain only the 50 US states based on their FIPS codes. 
    This excludes DC (11), Puerto Rico (72), and other territories.
    """
    fifty_state_fips = {
        "01","02","04","05","06","08","09","10",
        "12","13","15","16","17","18","19","20",
        "21","22","23","24","25","26","27","28",
        "29","30","31","32","33","34","35","36",
        "37","38","39","40","41","42","44","45",
        "46","47","48","49","50","51","53","54",
        "55","56"
    }
    return df[df["state_fips"].isin(fifty_state_fips)].copy()


# Main Pull

def main():

    all_years = []

    for year in YEARS:
        print(f"Fetching {year}...", end=" ")
        df_year = fetch_acs_year(year, API_KEY)

        if df_year.empty:
            continue

        df_year = filter_50_states(df_year)
        all_years.append(df_year)
        print(f"✓  {len(df_year)} states retrieved")

        # Short pause between requests
        time.sleep(0.5)

    if not all_years:
        print("No data retrieved. Check your API key and internet connection.")
        return

    # Combine all years into a single panel dataset
    panel = pd.concat(all_years, ignore_index=True)

    # Sort by state and year
    panel = panel.sort_values(["state_name", "year"]).reset_index(drop=True)

    # Summary
    print(f"\nDataset shape: {panel.shape[0]} rows × {panel.shape[1]} columns")
    print(f"Years covered: {sorted(panel['year'].unique())}")
    print(f"States covered: {panel['state_name'].nunique()}")
    print(f"\nMissing values:\n{panel.isnull().sum()}")
    print(f"\nSample (first 5 rows):\n{panel.head()}")

    # Save the file
    output_file = "acs_state_panel.csv"
    panel.to_csv(output_file, index=False)
    print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    main()