# Week 4 Regression Modeling Summary

## Purpose

The purpose of Week 4 was to move from cleaned data into statistical analysis. I used the Week 3 analysis-ready ACS county-level dataset to run simple linear regression models and create charts showing relationships between socioeconomic variables.

## Dataset Used

Input file: us_county_market_intelligence_acs_2024_analysis_ready.csv

Rows used after removing missing values: 3143

## Regression Models Created

The following regression models were created:

- `poverty_rate ~ median_household_income` showed a negative relationship with an R² value of 0.526, which suggests a strong relationship in this dataset.
- `poverty_rate ~ unemployment_rate` showed a positive relationship with an R² value of 0.271, which suggests a moderate relationship in this dataset.
- `broadband_internet_rate ~ median_household_income` showed a positive relationship with an R² value of 0.436, which suggests a moderate relationship in this dataset.
- `broadband_internet_rate ~ poverty_rate` showed a negative relationship with an R² value of 0.307, which suggests a moderate relationship in this dataset.

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
