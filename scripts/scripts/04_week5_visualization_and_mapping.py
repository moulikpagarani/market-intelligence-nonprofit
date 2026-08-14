import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Create folders
Path("visuals").mkdir(parents=True, exist_ok=True)
Path("reports").mkdir(parents=True, exist_ok=True)

# Load Week 3 analysis-ready dataset
input_path = Path("data/cleaned/us_county_market_intelligence_acs_2024_analysis_ready.csv")

if not input_path.exists():
    print("Upload your Week 3 analysis-ready CSV file now.")
    from google.colab import files
    uploaded = files.upload()
    uploaded_filename = list(uploaded.keys())[0]
    input_path = Path(uploaded_filename)

df = pd.read_csv(input_path)

print("Dataset loaded successfully.")
print("Rows:", len(df))
print("Columns:", df.columns.tolist())

# Make sure important columns are numeric
numeric_cols = [
    "total_population",
    "percent_under_18",
    "median_household_income",
    "poverty_rate",
    "unemployment_rate",
    "broadband_internet_rate",
    "market_outreach_opportunity_score"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=numeric_cols).copy()

# Sort counties by opportunity score
df_sorted = df.sort_values("market_outreach_opportunity_score", ascending=False)

# -----------------------------
# Chart 1: Top 20 counties
# -----------------------------

top20 = df_sorted.head(20).copy()
top20 = top20.sort_values("market_outreach_opportunity_score")

plt.figure(figsize=(10, 8))
plt.barh(top20["county_name"], top20["market_outreach_opportunity_score"])
plt.xlabel("Market Outreach Opportunity Score")
plt.ylabel("County")
plt.title("Top 20 Counties by Market Outreach Opportunity Score")
plt.tight_layout()
plt.savefig("visuals/top_20_market_opportunity_counties.png", dpi=300, bbox_inches="tight")
plt.show()

# -----------------------------
# Chart 2: Score distribution
# -----------------------------

plt.figure(figsize=(8, 6))
plt.hist(df["market_outreach_opportunity_score"], bins=30, edgecolor="black")
plt.xlabel("Market Outreach Opportunity Score")
plt.ylabel("Number of Counties")
plt.title("Distribution of Market Outreach Opportunity Scores")
plt.tight_layout()
plt.savefig("visuals/opportunity_score_distribution.png", dpi=300, bbox_inches="tight")
plt.show()

# -----------------------------
# Chart 3: Poverty vs Broadband
# -----------------------------

plt.figure(figsize=(8, 6))
plt.scatter(df["poverty_rate"], df["broadband_internet_rate"], alpha=0.35)
plt.xlabel("Poverty Rate (%)")
plt.ylabel("Broadband Internet Access Rate (%)")
plt.title("Poverty Rate vs Broadband Access")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("visuals/poverty_vs_broadband_scatter.png", dpi=300, bbox_inches="tight")
plt.show()

# -----------------------------
# Chart 4: Income vs Opportunity Score
# -----------------------------

plt.figure(figsize=(8, 6))
plt.scatter(df["median_household_income"], df["market_outreach_opportunity_score"], alpha=0.35)
plt.xlabel("Median Household Income")
plt.ylabel("Market Outreach Opportunity Score")
plt.title("Income vs Market Outreach Opportunity Score")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("visuals/income_vs_opportunity_score.png", dpi=300, bbox_inches="tight")
plt.show()

# -----------------------------
# Create regional/state summary
# -----------------------------

if "state_name" in df.columns:
    state_col = "state_name"
else:
    state_col = "state"

state_summary = df.groupby(state_col).agg(
    average_opportunity_score=("market_outreach_opportunity_score", "mean"),
    average_poverty_rate=("poverty_rate", "mean"),
    average_unemployment_rate=("unemployment_rate", "mean"),
    average_broadband_access=("broadband_internet_rate", "mean"),
    county_count=("county_name", "count")
).reset_index()

state_summary = state_summary.sort_values("average_opportunity_score", ascending=False)

state_summary.to_csv("reports/week5_state_level_visual_summary.csv", index=False)

# -----------------------------
# Chart 5: Top 15 states/regions
# -----------------------------

top_states = state_summary.head(15).copy()
top_states = top_states.sort_values("average_opportunity_score")

plt.figure(figsize=(10, 7))
plt.barh(top_states[state_col], top_states["average_opportunity_score"])
plt.xlabel("Average Market Outreach Opportunity Score")
plt.ylabel("State")
plt.title("Top 15 States by Average Market Outreach Opportunity Score")
plt.tight_layout()
plt.savefig("visuals/top_15_states_opportunity_score.png", dpi=300, bbox_inches="tight")
plt.show()

# -----------------------------
# Optional interactive county map
# -----------------------------

try:
    import plotly.express as px

    # Make sure GEOID is a 5 digit string
    df["GEOID"] = df["GEOID"].astype(str).str.zfill(5)

    county_geojson_url = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"

    fig = px.choropleth(
        df,
        geojson=county_geojson_url,
        locations="GEOID",
        color="market_outreach_opportunity_score",
        scope="usa",
        hover_name="county_name",
        hover_data={
            "market_outreach_opportunity_score": True,
            "poverty_rate": True,
            "median_household_income": True,
            "broadband_internet_rate": True,
            "GEOID": False
        },
        title="U.S. County Market Outreach Opportunity Score"
    )

    fig.update_layout(margin={"r":0, "t":50, "l":0, "b":0})
    fig.write_html("visuals/us_county_opportunity_score_map.html")

    print("Interactive map saved: visuals/us_county_opportunity_score_map.html")

except Exception as e:
    print("Map could not be created, but the charts were created successfully.")
    print("Map error:", e)

# -----------------------------
# Create Week 5 summary report
# -----------------------------

report = f"""# Week 5 Visualization and Mapping Summary

## Purpose

The purpose of Week 5 was to turn the cleaned dataset and regression analysis into polished visuals that can support the final nonprofit strategy report.

## Dataset Used

Input file: {input_path}

Rows used: {len(df)}

## Visuals Created

The following visuals were created:

1. `top_20_market_opportunity_counties.png`
2. `opportunity_score_distribution.png`
3. `poverty_vs_broadband_scatter.png`
4. `income_vs_opportunity_score.png`
5. `top_15_states_opportunity_score.png`
6. `us_county_opportunity_score_map.html`

## Main Findings to Discuss

The visuals help show which counties and states may deserve deeper nonprofit strategy review. The charts also show how poverty, broadband access, income, and opportunity scores relate to each other.

## How This Supports the Project

These visuals make the data easier for the team to explain. Instead of only showing raw numbers, the project can now show charts and maps that connect public data to outreach barriers, community disparities, and nonprofit strategy decisions.

## Important Limitation

These visuals are meant to guide deeper review. They do not prove that one county automatically needs more support than another. Local context, nonprofit mission fit, and community research still matter.
"""

with open("reports/week5_visualization_mapping_summary.md", "w") as f:
    f.write(report)

print("Week 5 visualization work complete.")
print("Saved charts in visuals folder.")
print("Saved report: reports/week5_visualization_mapping_summary.md")
print("Saved state summary: reports/week5_state_level_visual_summary.csv")
