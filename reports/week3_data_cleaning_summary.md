# Week 3 Data Cleaning Summary

## Purpose

The goal of Week 3 was to clean and prepare the ACS 2024 county-level market intelligence dataset for analysis, visualization, mapping, and nonprofit strategy work.

## Input Dataset

Input file: us_county_market_intelligence_acs_2024_cleaned.csv

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

Rows before cleaning: 3144
Rows after cleaning: 3143

## Missing Values Before Dropping Rows

total_population           0
percent_under_18           0
median_household_income    1
poverty_rate               0
unemployment_rate          0
broadband_internet_rate    0

## Score Explanation

The market outreach opportunity score is a first-pass screening tool. A higher score means a county may deserve deeper nonprofit strategy review based on a combination of youth population, poverty, unemployment, income, and broadband access indicators.

The score is not a final decision. It helps narrow down where the team may want to focus future analysis, mapping, outreach planning, and nonprofit strategy work.

## Top 10 Counties for Deeper Review

                       county_name  total_population  percent_under_18  median_household_income  poverty_rate  unemployment_rate  broadband_internet_rate  market_outreach_opportunity_score               opportunity_category
Oglala Lakota County, South Dakota           13491.0              35.4                  41417.0          57.6               16.4                     70.2                          98.927776 High opportunity for deeper review
         Todd County, South Dakota            9244.0              38.8                  42075.0          48.4               18.7                     75.2                          98.237353 High opportunity for deeper review
       Leflore County, Mississippi           27141.0              27.3                  35277.0          31.5               11.6                     69.3                          97.887369 High opportunity for deeper review
      Buffalo County, South Dakota            1808.0              39.2                  47045.0          33.9               10.8                     68.7                          97.610563 High opportunity for deeper review
      Jackson County, South Dakota            2802.0              32.9                  35417.0          42.4                7.2                     62.7                          97.410118 High opportunity for deeper review
               Starr County, Texas           66067.0              32.5                  37639.0          33.5               10.4                     78.6                          96.996500 High opportunity for deeper review
            Apache County, Arizona           65341.0              26.0                  41438.0          30.5               10.7                     60.0                          96.888323 High opportunity for deeper review
     Humphreys County, Mississippi            7395.0              25.2                  33731.0          27.0               12.5                     65.3                          96.306077 High opportunity for deeper review
        Sioux County, North Dakota            3740.0              34.0                  42083.0          43.3               17.0                     80.6                          96.264715 High opportunity for deeper review
        Tunica County, Mississippi            9475.0              27.7                  39364.0          31.1               13.3                     78.7                          96.236080 High opportunity for deeper review

## Output Files

- data/cleaned/us_county_market_intelligence_acs_2024_analysis_ready.csv
- data/cleaned/top_50_market_opportunity_counties.csv
