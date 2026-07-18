import pandas as pd
import requests
from pathlib import Path
import time

# Put your Census API key inside the quotes below.
# Example: CENSUS_API_KEY = "abc123yourkey"
CENSUS_API_KEY = "PUT_YOUR_KEY_HERE"

# Create folders
Path("data/raw").mkdir(parents=True, exist_ok=True)
Path("data/cleaned").mkdir(parents=True, exist_ok=True)

# Census ACS 2024 5-Year Data Profile API
base_url = "https://api.census.gov/data/2024/acs/acs5/profile"

# State FIPS codes for 50 states + DC
state_fips_codes = [
    "01", "02", "04", "05", "06", "08", "09", "10", "11", "12",
    "13", "15", "16", "17", "18", "19", "20", "21", "22", "23",
    "24", "25", "26", "27", "28", "29", "30", "31", "32", "33",
    "34", "35", "36", "37", "38", "39", "40", "41", "42", "44",
    "45", "46", "47", "48", "49", "50", "51", "53", "54", "55", "56"
]

all_rows = []

for state in state_fips_codes:
    params = {
        "get": "NAME,DP05_0001E,DP05_0019PE,DP03_0062E,DP03_0128PE,DP03_0009PE,DP02_0154PE",
        "for": "county:*",
        "in": f"state:{state}",
        "key": CENSUS_API_KEY
    }

    response = requests.get(base_url, params=params)

    print(f"State {state}: status {response.status_code}")

    if response.status_code != 200:
        print("Problem with this state:")
        print(response.text[:500])
        continue

    try:
        data = response.json()
    except Exception:
        print("Could not read JSON for state:", state)
        print(response.text[:500])
        continue

    if len(data) > 1:
        rows = data[1:]
        all_rows.extend(rows)

    time.sleep(0.2)

# Stop if no data was collected
if len(all_rows) == 0:
    raise ValueError("No data was collected. Check your Census API key.")

# Column names
columns = [
    "county_name",
    "total_population",
    "percent_under_18",
    "median_household_income",
    "poverty_rate",
    "unemployment_rate",
    "broadband_internet_rate",
    "state",
    "county"
]

df = pd.DataFrame(all_rows, columns=columns)

# Create Census GEOID for mapping later
df["GEOID"] = df["state"] + df["county"]

# Save raw file
df.to_csv("data/raw/us_county_market_intelligence_acs_2024_raw.csv", index=False)

# Convert numeric columns
numeric_cols = [
    "total_population",
    "percent_under_18",
    "median_household_income",
    "poverty_rate",
    "unemployment_rate",
    "broadband_internet_rate"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")
    df.loc[df[col] < 0, col] = pd.NA

# Market intelligence indicators
df["target_population_indicator"] = df["percent_under_18"].rank(pct=True)
df["economic_barrier_indicator"] = df["poverty_rate"].rank(pct=True)
df["employment_barrier_indicator"] = df["unemployment_rate"].rank(pct=True)
df["income_barrier_indicator"] = 1 - df["median_household_income"].rank(pct=True)
df["digital_access_barrier_indicator"] = 1 - df["broadband_internet_rate"].rank(pct=True)

# Market outreach opportunity score
df["market_outreach_opportunity_score"] = (
    df["target_population_indicator"] +
    df["economic_barrier_indicator"] +
    df["employment_barrier_indicator"] +
    df["income_barrier_indicator"] +
    df["digital_access_barrier_indicator"]
) / 5 * 100

# Sort highest opportunity areas first
df = df.sort_values("market_outreach_opportunity_score", ascending=False)

# Save cleaned file
df.to_csv("data/cleaned/us_county_market_intelligence_acs_2024_cleaned.csv", index=False)

print("Finished successfully.")
print("Number of counties collected:", len(df))
print("Raw file saved: data/raw/us_county_market_intelligence_acs_2024_raw.csv")
print("Cleaned file saved: data/cleaned/us_county_market_intelligence_acs_2024_cleaned.csv")

df.head(10)
