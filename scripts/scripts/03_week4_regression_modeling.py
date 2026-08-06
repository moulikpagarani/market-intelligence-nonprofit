import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.stats import linregress

# Create folders
Path("visuals").mkdir(parents=True, exist_ok=True)
Path("reports").mkdir(parents=True, exist_ok=True)

# Load Week 3 analysis-ready dataset
input_path = Path("data/cleaned/us_county_market_intelligence_acs_2024_analysis_ready.csv")

# If Colab cannot find it, upload the file manually
if not input_path.exists():
    print("Upload your Week 3 analysis-ready CSV file now.")
    from google.colab import files
    uploaded = files.upload()
    uploaded_filename = list(uploaded.keys())[0]
    input_path = Path(uploaded_filename)

df = pd.read_csv(input_path)

print("Dataset loaded successfully.")
print("Rows:", len(df))
print("Columns:")
print(df.columns.tolist())

# Required columns for Week 4 regression modeling
required_cols = [
    "county_name",
    "total_population",
    "percent_under_18",
    "median_household_income",
    "poverty_rate",
    "unemployment_rate",
    "broadband_internet_rate",
    "market_outreach_opportunity_score"
]

missing_cols = [col for col in required_cols if col not in df.columns]

if missing_cols:
    raise ValueError(f"Missing required columns: {missing_cols}")

# Make sure numeric columns are actually numeric
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

# Drop rows with missing values in important columns
df_model = df.dropna(subset=numeric_cols).copy()

print("Rows after removing missing values:", len(df_model))

# Function to run simple linear regression and create chart
def run_regression_and_chart(df, x_col, y_col, x_label, y_label, title, output_file):
    model_data = df[[x_col, y_col]].dropna()

    x = model_data[x_col]
    y = model_data[y_col]

    result = linregress(x, y)

    slope = result.slope
    intercept = result.intercept
    r_value = result.rvalue
    r_squared = r_value ** 2
    p_value = result.pvalue

    # Create prediction line
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = intercept + slope * x_line

    # Plot
    plt.figure(figsize=(8, 6))
    plt.scatter(x, y, alpha=0.35)
    plt.plot(x_line, y_line)
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid(True, alpha=0.3)

    annotation = f"R² = {r_squared:.3f}\np-value = {p_value:.4g}"
    plt.text(
        0.05,
        0.95,
        annotation,
        transform=plt.gca().transAxes,
        verticalalignment="top",
        bbox=dict(boxstyle="round", alpha=0.2)
    )

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.show()

    return {
        "model": f"{y_col} ~ {x_col}",
        "x_variable": x_col,
        "y_variable": y_col,
        "slope": slope,
        "intercept": intercept,
        "r_squared": r_squared,
        "p_value": p_value,
        "output_chart": output_file
    }

# Run regression models
results = []

results.append(run_regression_and_chart(
    df_model,
    x_col="median_household_income",
    y_col="poverty_rate",
    x_label="Median Household Income",
    y_label="Poverty Rate (%)",
    title="Median Household Income vs Poverty Rate",
    output_file="visuals/income_vs_poverty_regression.png"
))

results.append(run_regression_and_chart(
    df_model,
    x_col="unemployment_rate",
    y_col="poverty_rate",
    x_label="Unemployment Rate (%)",
    y_label="Poverty Rate (%)",
    title="Unemployment Rate vs Poverty Rate",
    output_file="visuals/unemployment_vs_poverty_regression.png"
))

results.append(run_regression_and_chart(
    df_model,
    x_col="median_household_income",
    y_col="broadband_internet_rate",
    x_label="Median Household Income",
    y_label="Broadband Internet Access Rate (%)",
    title="Median Household Income vs Broadband Access",
    output_file="visuals/income_vs_broadband_regression.png"
))

results.append(run_regression_and_chart(
    df_model,
    x_col="poverty_rate",
    y_col="broadband_internet_rate",
    x_label="Poverty Rate (%)",
    y_label="Broadband Internet Access Rate (%)",
    title="Poverty Rate vs Broadband Access",
    output_file="visuals/poverty_vs_broadband_regression.png"
))

# Save regression results
results_df = pd.DataFrame(results)
results_path = "reports/week4_regression_results.csv"
results_df.to_csv(results_path, index=False)

print("Regression results saved:", results_path)
display(results_df)

# Create written interpretation
def interpret_direction(slope):
    if slope > 0:
        return "positive"
    elif slope < 0:
        return "negative"
    else:
        return "no clear"

def interpret_strength(r_squared):
    if r_squared >= 0.5:
        return "strong"
    elif r_squared >= 0.25:
        return "moderate"
    elif r_squared >= 0.1:
        return "weak to moderate"
    else:
        return "weak"

summary_lines = []

for row in results:
    direction = interpret_direction(row["slope"])
    strength = interpret_strength(row["r_squared"])

    summary_lines.append(
        f"- `{row['model']}` showed a {direction} relationship with an R² value of {row['r_squared']:.3f}, which suggests a {strength} relationship in this dataset."
    )

summary_text = "\n".join(summary_lines)

report = f"""# Week 4 Regression Modeling Summary

## Purpose

The purpose of Week 4 was to move from cleaned data into statistical analysis. I used the Week 3 analysis-ready ACS county-level dataset to run simple linear regression models and create charts showing relationships between socioeconomic variables.

## Dataset Used

Input file: {input_path}

Rows used after removing missing values: {len(df_model)}

## Regression Models Created

The following regression models were created:

{summary_text}

## Charts Created

- `visuals/income_vs_poverty_regression.png`
- `visuals/unemployment_vs_poverty_regression.png`
- `visuals/income_vs_broadband_regression.png`
- `visuals/poverty_vs_broadband_regression.png`

## Main Takeaway

These models help identify broad socioeconomic patterns across counties. For example, the analysis can show whether counties with lower income tend to have higher poverty rates, whether unemployment and poverty move together, and whether broadband access is connected to income or poverty levels.

## Important Limitation

These regression models show relationships, not causation. The results should be used as a starting point for nonprofit strategy discussion, not as final proof that one variable directly causes another.

## Connection to Project Goal

This analysis supports the project by turning raw public data into interpretable trends. These trends can help nonprofits better understand outreach barriers, community disparities, and areas that may need deeper strategic review.
"""

report_path = "reports/week4_regression_modeling_summary.md"

with open(report_path, "w") as f:
    f.write(report)

print("Week 4 regression modeling complete.")
print("Saved:", results_path)
print("Saved:", report_path)
print("Saved charts in visuals folder.")
