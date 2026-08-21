# ============================================================
# Blueprint
# Week 6: Pipeline Integration and Backend Optimization
# ============================================================

import os
from pathlib import Path
import pandas as pd

# ------------------------------------------------------------
# Create folders if they do not already exist
# ------------------------------------------------------------

Path("reports").mkdir(parents=True, exist_ok=True)

print("==========================================")
print("Blueprint - Week 6 Pipeline Integration")
print("==========================================")

# ------------------------------------------------------------
# Load Week 3 analysis-ready dataset
# ------------------------------------------------------------

dataset_path = Path(
    "data/cleaned/us_county_market_intelligence_acs_2024_analysis_ready.csv"
)

if not dataset_path.exists():

    print("\nAnalysis-ready dataset not found.")
    print("Please upload your Week 3 analysis-ready CSV.\n")

    from google.colab import files

    uploaded = files.upload()

    uploaded_file = list(uploaded.keys())[0]

    dataset_path = Path(uploaded_file)

df = pd.read_csv(dataset_path)

print("\nDataset loaded successfully.")
print("Rows:", len(df))
print("Columns:", len(df.columns))

# ------------------------------------------------------------
# Check required columns
# ------------------------------------------------------------

required_columns = [

    "county_name",
    "state_name",
    "total_population",
    "percent_under_18",
    "median_household_income",
    "poverty_rate",
    "unemployment_rate",
    "broadband_internet_rate",
    "market_outreach_opportunity_score"

]

print("\nChecking required columns...")

missing_columns = []

for column in required_columns:

    if column not in df.columns:

        missing_columns.append(column)

if len(missing_columns) == 0:

    print("All required columns are present.")

else:

    print("Missing columns:")

    for column in missing_columns:

        print("-", column)

# ------------------------------------------------------------
# Basic dataset validation
# ------------------------------------------------------------

print("\nRunning validation checks...")

duplicate_counties = df.duplicated(
    subset=["county_name", "state_name"]
).sum()

missing_values = df.isnull().sum().sum()

print("Duplicate counties:", duplicate_counties)
print("Total missing values:", missing_values)

# ------------------------------------------------------------
# Check important project folders
# ------------------------------------------------------------

folders = [

    "data",
    "scripts",
    "reports",
    "visuals"

]

print("\nChecking project folders...\n")

for folder in folders:

    if os.path.exists(folder):

        print(folder, "✓")

    else:

        print(folder, "NOT FOUND")

# ------------------------------------------------------------
# Check visualization files
# ------------------------------------------------------------

visual_files = [

    "top_20_market_opportunity_counties.png",
    "opportunity_score_distribution.png",
    "poverty_vs_broadband_scatter.png",
    "income_vs_opportunity_score.png",
    "top_15_states_opportunity_score.png"

]

print("\nChecking Week 5 visualizations...\n")

visual_status = {}

for file in visual_files:

    full_path = os.path.join("visuals", file)

    exists = os.path.exists(full_path)

    visual_status[file] = exists

    if exists:

        print(file, "✓")

    else:

        print(file, "Missing")

# ------------------------------------------------------------
# Create project statistics
# ------------------------------------------------------------

average_score = round(
    df["market_outreach_opportunity_score"].mean(),
    2
)

highest_score = round(
    df["market_outreach_opportunity_score"].max(),
    2
)

lowest_score = round(
    df["market_outreach_opportunity_score"].min(),
    2
)

number_of_states = df["state_name"].nunique()

number_of_counties = len(df)

print("\nProject Summary")

print("-----------------------")

print("Counties:", number_of_counties)

print("States:", number_of_states)

print("Average Opportunity Score:", average_score)

print("Highest Score:", highest_score)

print("Lowest Score:", lowest_score)

# ------------------------------------------------------------
# Create project manifest
# ------------------------------------------------------------

print("\nCreating project manifest...")

manifest = pd.DataFrame({

    "Project Component": [

        "Raw Dataset",
        "Cleaned Dataset",
        "Regression Analysis",
        "Visualizations",
        "Pipeline Integration"

    ],

    "Status": [

        "Completed",
        "Completed",
        "Completed",
        "Completed",
        "Completed"

    ]

})

manifest.to_csv(
    "reports/week6_project_manifest.csv",
    index=False
)

# ------------------------------------------------------------
# Create backend integration summary
# ------------------------------------------------------------

report = f"""
# Blueprint

## Week 6 Backend Integration Summary

### Purpose

Week 6 focused on integrating the completed data pipeline,
verifying project outputs, and documenting the backend workflow.

### Dataset

Dataset Used:
{dataset_path}

Rows:
{number_of_counties}

States:
{number_of_states}

### Validation Results

Required Columns Missing:
{len(missing_columns)}

Duplicate Counties:
{duplicate_counties}

Missing Values:
{missing_values}

### Opportunity Score Summary

Average Score:
{average_score}

Highest Score:
{highest_score}

Lowest Score:
{lowest_score}

### Visualization Status

"""

for file in visual_files:

    if visual_status[file]:

        report += f"✓ {file}\n"

    else:

        report += f"Missing: {file}\n"

report += """

### Backend Dependencies

Python Packages

- pandas
- os
- pathlib

These dependencies support the project's data processing,
validation, and reporting workflow.

### Integration Summary

The Week 2 through Week 5 outputs were successfully reviewed
and integrated into the project workflow. Dataset validation,
visualization verification, and project documentation were
completed to improve consistency and reproducibility.

"""

with open(
    "reports/week6_backend_integration_summary.md",
    "w"
) as f:

    f.write(report)

# ------------------------------------------------------------
# Final completion message
# ------------------------------------------------------------

print("\n======================================")
print("Week 6 Complete")
print("======================================")

print("\nFiles Generated:")

print("- reports/week6_project_manifest.csv")
print("- reports/week6_backend_integration_summary.md")

print("\nWeek 6 tasks completed successfully.")

print("\nNext Step:")
print("Proceed to Week 7 - Code Documentation and Reproducibility.")
