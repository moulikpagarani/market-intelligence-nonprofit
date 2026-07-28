# Data Dictionary

## Dataset: us_county_market_intelligence_acs_2024_cleaned.csv

This dataset uses U.S. Census ACS 2024 5-Year county-level data to support nonprofit market intelligence and outreach planning.

| Column | Meaning |
|---|---|
| county_name | County and state name |
| total_population | Total population estimate |
| percent_under_18 | Percent of the population under age 18 |
| median_household_income | Median household income |
| poverty_rate | Percent of people below the poverty level |
| unemployment_rate | Civilian labor force unemployment rate |
| broadband_internet_rate | Percent of households with broadband internet subscription |
| state | State FIPS code |
| county | County FIPS code |
| GEOID | Census geographic ID used for mapping |
| target_population_indicator | Ranking based on youth population percentage |
| economic_barrier_indicator | Ranking based on poverty rate |
| employment_barrier_indicator | Ranking based on unemployment rate |
| income_barrier_indicator | Ranking based on lower median household income |
| digital_access_barrier_indicator | Ranking based on lower broadband internet access |
| market_outreach_opportunity_score | Combined score used to identify counties for deeper nonprofit market intelligence review |

## Important Note

The market outreach opportunity score is not a final judgment about a county. It is a starting point for nonprofit market intelligence. It helps the team decide which places deserve deeper research, mapping, outreach planning, and strategy development.

## Additional Week 3 Columns

| Column | Meaning |
|---|---|
| county_clean | Cleaned county name without the state text |
| state_name | State name separated from the county name |
| opportunity_category | High, medium, or low review category based on market outreach opportunity score |
| population_size_category | County size category based on total population |

## Week 3 Output Files

- `us_county_market_intelligence_acs_2024_analysis_ready.csv`: Final analysis-ready dataset.
- `top_50_market_opportunity_counties.csv`: Top 50 counties for deeper nonprofit strategy review.
- `week3_data_cleaning_summary.md`: Written summary of the cleaning process.
