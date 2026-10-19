# Current data dictionary

- `total_population`: ACS variable DP05_0001E; people
- `percent_under_18`: ACS variable DP05_0019PE; percent
- `median_household_income`: ACS variable DP03_0062E; 2024 inflation-adjusted dollars
- `poverty_rate`: ACS variable DP03_0128PE; percent
- `unemployment_rate`: ACS variable DP03_0009PE; percent
- `broadband_internet_rate`: ACS variable DP02_0154PE; percent

GEOID/state/county are strings of widths 5/2/3. *_moe: published 90% margin of error; *_cv: MOE/1.645/positive estimate. *_precision_flag separates unavailable MOE, undefined CV, and CV review categories. score_status explicitly identifies withheld scores. Sentinel audit preserves raw values. See reports/week7_technical_documentation.md.
