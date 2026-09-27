# Final Model Enhancement Summary

## Purpose
This final enhancement implements feedback received after the initial presentation. The updates improve customization, strengthen the opportunity score explanation, add multiple-variable regression, add color-coded variable groups, and test nonlinear relationships.

## 1. Customization Layer
BluePrint should be understood as a general toolkit with customized outputs. The backend pipeline can be reused, but the final results can change based on nonprofit mission, location, target population, and outreach goals.

New file created:

- `config/nonprofit_customization_profiles.csv`
- `data/cleaned/customized_opportunity_scores_by_profile.csv`
- `recommendations/customized_nonprofit_recommendations.csv`

Customization profiles include Youth and Education, Community Services, Mental Health and Wellness, Digital Outreach Heavy, Be Kind 5 Prototype, and Mirror Echoes Prototype.

## 2. Opportunity Score Update
The original Market Outreach Opportunity Score remains useful as the default screening metric. The enhanced version adds adjustable profile weights. The score still uses:

- youth population
- poverty rate
- unemployment rate
- income barrier
- broadband access barrier

The difference is that nonprofits can now weight these variables differently based on mission fit.

## 3. Multiple Linear Regression
The original analysis used mostly simple one-variable regressions. The enhancement adds multiple linear regression models that test several predictors at the same time.

New output:

- `reports/final_multiple_regression_results.csv`

Opportunity score model R-squared: 0.903

## 4. Nonlinear Relationship Testing
The enhancement compares linear and quadratic models for selected relationships. This responds to feedback that some relationships may not be perfectly linear.

New output:

- `reports/final_nonlinear_regression_comparison.csv`

## 5. Color-Coded Variable Framework
Variables are now grouped into clearer categories:

- Target Population
- Economic Need
- Employment Barrier
- Income Barrier
- Digital Access Barrier

New visuals include:

- `visuals/final_color_coded_variable_framework.png`
- `visuals/final_multiple_regression_coefficients.png`
- `visuals/final_linear_vs_nonlinear_income_poverty.png`
- `visuals/final_linear_vs_nonlinear_income_broadband.png`
- `visuals/final_linear_vs_nonlinear_poverty_broadband.png`
- `visuals/final_linear_vs_nonlinear_unemployment_poverty.png`
- `visuals/final_customized_score_comparison_top5.png`
- `visuals/final_color_coded_opportunity_scatter.png`

## 6. Model limitations
R-squared values are in-sample descriptive fit, not held-out predictive performance. Quadratic models can improve training fit simply by adding a parameter. These associations do not establish causality. The opportunity score is constructed from these same socioeconomic inputs, so its regression is descriptive and is not independent validation of outreach outcomes. Predictors are standardized; coefficients retain the target variable units. Profile weights are illustrative prototypes, not empirically validated nonprofit preferences. Customization currently changes weights only; location and other constraints require separate filtering.

## 7. Numerical Results

Multiple regression model fit (all predictors fitted together; in-sample):

| model_name                             |   r_squared |   adjusted_r_squared |   n_counties |
|:---------------------------------------|------------:|---------------------:|-------------:|
| Multiple Regression: Opportunity Score |    0.902939 |             0.902784 |         3143 |
| Multiple Regression: Poverty Rate      |    0.653407 |             0.652965 |         3143 |
| Multiple Regression: Broadband Access  |    0.450093 |             0.449392 |         3143 |

Linear versus quadratic comparison (in-sample):

| pair_name               |   linear_r_squared |   quadratic_r_squared |   r_squared_change |   n_counties |
|:------------------------|-------------------:|----------------------:|-------------------:|-------------:|
| Income vs Poverty       |           0.525946 |              0.652138 |        0.126191    |         3143 |
| Income vs Broadband     |           0.436191 |              0.483219 |        0.0470286   |         3143 |
| Poverty vs Broadband    |           0.30735  |              0.309141 |        0.00179046  |         3143 |
| Unemployment vs Poverty |           0.270904 |              0.271191 |        0.000287079 |         3143 |

## 8. Interpretation
These updates make BluePrint stronger because the final product is no longer only a fixed general score. It now supports mission-specific customization, clearer visual communication, more advanced regression modeling, and nonlinear exploratory analysis.
