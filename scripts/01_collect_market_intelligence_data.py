import pandas as pd
from pathlib import Path

# Create folders
Path("data/raw").mkdir(parents=True, exist_ok=True)
Path("data/cleaned").mkdir(parents=True, exist_ok=True)

# U.S. Census ACS 2024 5-Year Data Profile API
# Geography: all U.S. counties
# Purpose: market intelligence foundation for nonprofit outreach strategy

url = (
    "https://api.census.gov/data/2024/acs/acs5/profile"
    "?get=NAME,"
    "DP05_0001E,"   # total population
    "DP05_0019PE,"  # percent under 18
    "DP03_0062E,"   # median household income
    "DP03_0128PE,"  # poverty rate
    "DP03_0009PE,"  # unemployment rate
    "DP02_0154PE"   # broadband internet subscription rate
    "&for=county:*&in=state:*"
)

df = pd.read_json(url)

# First row is column names
df.columns = df.iloc[0]
df = df.iloc[1:].copy()

# Rename columns
df = df.rename(columns={
    "NAME": "county_name",
    "DP05_0001E": "total_population",
    "DP05_0019PE": "percent_under_18",
    "DP03_0062E": "median_household_income",
    "DP03_0128PE": "poverty_rate",
    "DP03_0009PE": "unemployment_rate",
    "DP02_0154PE": "broadband_internet_rate"
})

# Create mapping ID
df["GEOID"] = df["state"] + df["county"]

# Save raw data
df.to_csv("data/raw/us_county_market_intelligence_acs_2024_raw.csv", index=False)

# Convert columns to numbers
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

# Create market opportunity indicators
df["target_population_indicator"] = df["percent_under_18"].rank(pct=True)
df["economic_barrier_indicator"] = df["poverty_rate"].rank(pct=True)
df["employment_barrier_indicator"] = df["unemployment_rate"].rank(pct=True)
df["income_barrier_indicator"] = 1 - df["median_household_income"].rank(pct=True)
df["digital_access_barrier_indicator"] = 1 - df["broadband_internet_rate"].rank(pct=True)

# Combined score for further review, not a final judgment
df["market_outreach_opportunity_score"] = (
    df["target_population_indicator"] +
    df["economic_barrier_indicator"] +
    df["employment_barrier_indicator"] +
    df["income_barrier_indicator"] +
    df["digital_access_barrier_indicator"]
) / 5 * 100

df = df.sort_values("market_outreach_opportunity_score", ascending=False)

# Save cleaned data
df.to_csv("data/cleaned/us_county_market_intelligence_acs_2024_cleaned.csv", index=False)

print("Finished.")
print("Saved raw file: data/raw/us_county_market_intelligence_acs_2024_raw.csv")
print("Saved cleaned file: data/cleaned/us_county_market_intelligence_acs_2024_cleaned.csv")
print()
print("Top 10 counties for further market intelligence review:")
print(df[[
    "county_name",
    "total_population",
    "percent_under_18",
    "median_household_income",
    "poverty_rate",
    "unemployment_rate",
    "broadband_internet_rate",
    "market_outreach_opportunity_score"
]].head(10))
