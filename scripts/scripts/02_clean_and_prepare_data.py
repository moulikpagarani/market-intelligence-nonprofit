import pandas as pd
import numpy as np
from pathlib import Path

# Create folders
Path("data/cleaned").mkdir(parents=True, exist_ok=True)
Path("reports").mkdir(parents=True, exist_ok=True)

# Try to find the cleaned Week 2 file
input_path = Path("data/cleaned/us_county_market_intelligence_acs_2024_cleaned.csv")

# If the file is not already in Colab, upload it manually
if not input_path.exists():
    print("Upload your Week 2 cleaned CSV file now.")
    from google.colab import files
    uploaded = files.upload()
    uploaded_filename = list(uploaded.keys())[0]
    input_path = Path(uploaded_filename)

# Load dataset
df = pd.read_csv(input_path)

print("Original dataset shape:", df.shape)
print("Original columns:")
print(df.columns.tolist())

# Clean column names
df.columns = df.columns.str.strip()

# Required columns for the project
required_cols = [
    "county_name",
    "total_population",
    "percent_under_18",
    "median_household_income",
    "poverty_rate",
    "unemployment_rate",
    "broadband_internet_rate",
    "GEOID"
]

# Check for missing columns
missing_cols = [col for col in required_cols if col not in df.columns]

if missing_cols:
    raise ValueError(f"Missing required columns: {missing_cols}")

# Keep only useful columns for Week 3 analysis
df = df[required_cols].copy()

# Clean county names
df["county_name"] = df["county_name"].astype(str).str.strip()

# Split county and state into separate columns
name_parts = df["county_name"].str.rsplit(",", n=1, expand=True)
df["county_clean"] = name_parts[0].str.strip()

if name_parts.shape[1] > 1:
    df["state_name"] = name_parts[1].str.strip()
else:
    df["state_name"] = pd.NA

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
    df.loc[df[col] < 0, col] = np.nan

# Count missing values before dropping
missing_summary = df[numeric_cols].isna().sum()

# Remove rows missing key numeric values
df_clean = df.dropna(subset=numeric_cols).copy()

print("Rows before cleaning:", len(df))
print("Rows after removing missing key values:", len(df_clean))

# Recreate market intelligence indicators
df_clean["target_population_indicator"] = df_clean["percent_under_18"].rank(pct=True)
df_clean["economic_barrier_indicator"] = df_clean["poverty_rate"].rank(pct=True)
df_clean["employment_barrier_indicator"] = df_clean["unemployment_rate"].rank(pct=True)
df_clean["income_barrier_indicator"] = 1 - df_clean["median_household_income"].rank(pct=True)
df_clean["digital_access_barrier_indicator"] = 1 - df_clean["broadband_internet_rate"].rank(pct=True)

# Recreate market outreach opportunity score
df_clean["market_outreach_opportunity_score"] = (
    df_clean["target_population_indicator"] +
    df_clean["economic_barrier_indicator"] +
    df_clean["employment_barrier_indicator"] +
    df_clean["income_barrier_indicator"] +
    df_clean["digital_access_barrier_indicator"]
) / 5 * 100

# Create opportunity categories
low_cutoff = df_clean["market_outreach_opportunity_score"].quantile(0.25)
high_cutoff = df_clean["market_outreach_opportunity_score"].quantile(0.75)

def assign_opportunity_category(score):
    if score >= high_cutoff:
        return "High opportunity for deeper review"
    elif score <= low_cutoff:
        return "Low opportunity based on selected indicators"
    else:
        return "Medium opportunity for deeper review"

df_clean["opportunity_category"] = df_clean["market_outreach_opportunity_score"].apply(assign_opportunity_category)

# Create population size category
df_clean["population_size_category"] = pd.cut(
    df_clean["total_population"],
    bins=[0, 50000, 250000, 1000000, np.inf],
    labels=["Small county", "Medium county", "Large county", "Very large county"]
)

# Sort by opportunity score
df_clean = df_clean.sort_values("market_outreach_opportunity_score", ascending=False)

# Save analysis-ready dataset
final_path = "data/cleaned/us_county_market_intelligence_acs_2024_analysis_ready.csv"
df_clean.to_csv(final_path, index=False)

# Save top 50 counties for easier review
top_50_path = "data/cleaned/top_50_market_opportunity_counties.csv"
df_clean.head(50).to_csv(top_50_path, index=False)

# Create Week 3 cleaning summary report
top_10_text = df_clean[[
    "county_name",
    "total_population",
    "percent_under_18",
    "median_household_income",
    "poverty_rate",
    "unemployment_rate",
    "broadband_internet_rate",
    "market_outreach_opportunity_score",
    "opportunity_category"
]].head(10).to_string(index=False)

summary = f"""# Week 3 Data Cleaning Summary

## Purpose

The goal of Week 3 was to clean and prepare the ACS 2024 county-level market intelligence dataset for analysis, visualization, mapping, and nonprofit strategy work.

## Input Dataset

Input file: {input_path}

## Cleaning Steps Completed

1. Loaded the Week 2 ACS county-level dataset.
2. Checked that all required columns were present.
3. Kept only the columns needed for nonprofit market intelligence.
4. Cleaned county names and separated county/state text.
5. Converted numeric fields into proper number formats.
6. Checked for missing values.
7. Removed rows missing key numeric values.
8. Recreated the market intelligence indicators.
9. Recalculated the market outreach opportunity score.
10. Added opportunity categories: high, medium, and low.
11. Added population size categories.
12. Saved an analysis-ready dataset and a top 50 review file.

## Rows Before and After Cleaning

Rows before cleaning: {len(df)}
Rows after cleaning: {len(df_clean)}

## Missing Values Before Dropping Rows

{missing_summary.to_string()}

## Score Explanation

The market outreach opportunity score is a first-pass screening tool. A higher score means a county may deserve deeper nonprofit strategy review based on a combination of youth population, poverty, unemployment, income, and broadband access indicators.

The score is not a final decision. It helps narrow down where the team may want to focus future analysis, mapping, outreach planning, and nonprofit strategy work.

## Top 10 Counties for Deeper Review

{top_10_text}

## Output Files

- data/cleaned/us_county_market_intelligence_acs_2024_analysis_ready.csv
- data/cleaned/top_50_market_opportunity_counties.csv
"""

report_path = "reports/week3_data_cleaning_summary.md"

with open(report_path, "w") as f:
    f.write(summary)

print("Week 3 cleaning complete.")
print("Saved:", final_path)
print("Saved:", top_50_path)
print("Saved:", report_path)

df_clean.head(10)
