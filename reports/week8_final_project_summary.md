# Final review

# BluePrint audited technical report

## Evidence and scope
Run date: 2026-10-18 (America/New_York). ACS 2024 five-year estimates describe 2020–2024, not a point-in-time survey. 3144 counties/equivalents across 50 states and DC; 3143 complete scores. Original raw data and pre-audit code/outputs are preserved under archive/pre_audit_2026_10_18. Historical outputs are not current evidence. No synthetic ACS values or imputed county incomes were introduced.

## Correct interpretation of scores
The score is 100 times the mean of five average percentile ranks; income and broadband are reversed using 1-rank. Ranking uses only counties with all five indicators. Mean is 50.00318167; with this exact convention its algebraic expectation is 50 + 10/n = 50.00318167, not exactly 50 (the old report rounded it). An upper-quartile label selects approximately one quarter of complete counties, with ties possibly changing counts. It does not indicate an absolute severity cutoff, service gaps, reachable audience, or intervention benefit. A common monotone improvement preserving ranks leaves scores unchanged. Across-year or changed-universe score comparisons require a fixed reference distribution. Absolute indicator CSV and distributions retain actual units. Percent under 18 is a share, not a count; total population is supplied separately. Youth counts inferred from shares would be approximate and are not presented as direct ACS counts.

## Missing values and precision
GEOID                county_name                   field  raw_value                      reason
35011 De Baca County, New Mexico median_household_income -666666666 Census sentinel/unavailable

De Baca (35011) remains in both cleaned and analysis-ready tables and the gray map layer; incomplete scores are withheld. Raw sentinels are recorded before conversion; no partial-indicator average is used. Small-population flag (<20,000) is an analyst screening rule, not evidence of low precision. MOE unavailable for 3144 counties; high CV for at least one available field: 0. CV = MOE / 1.645 / estimate, only for positive estimates. CV >30% is a review flag chosen for this project, not a universal Census publication rule. Zero estimates have undefined CV. Missing MOEs are never labeled reliable. Marginal MOEs do not supply joint covariance: no score confidence intervals or probability-of-top-rank claims are made. MOE sentinels and annotations must be inspected when available. ACS population estimates are survey estimates, not sample sizes.

## Income–poverty overlap and weights
Pearson correlation between income and poverty: -0.7252. Full Pearson/Spearman matrices and predictor VIFs are saved. The baseline gives income and poverty 40% combined weight, so correlated economic deprivation may receive extra emphasis. Economic-domain-balanced weights allocate 25% total across those two variables. Omission and six illustrative mission profiles are compared using rank correlation, rank shifts, and top-50 overlap; these are sensitivity exercises, not validated mission preferences. No universal optimal weights or new absolute composite need threshold is asserted.

                 profile  spearman_rank_correlation  top50_overlap  median_absolute_rank_shift  max_absolute_rank_shift  target_population_indicator  economic_barrier_indicator  employment_barrier_indicator  income_barrier_indicator  digital_access_barrier_indicator
              equal_five                   1.000000             50                         0.0                      0.0                         0.20                       0.200                          0.20                     0.200                              0.20
economic_domain_balanced                   0.985519             47                        85.0                    774.0                         0.25                       0.125                          0.25                     0.125                              0.25
          without_income                   0.975891             43                       112.5                    778.5                         0.25                       0.250                          0.25                     0.000                              0.25
         without_poverty                   0.978116             49                        98.5                    769.0                         0.25                       0.000                          0.25                     0.250                              0.25

## Prediction without circularity
Removed score-on-components regression from active scripts and current results. Outcomes are actual poverty and broadband subscription percentages, each predicted from the other four indicators and log(1+population). They are descriptive cross-sectional models, not outreach-impact or causal models. Split is fixed (seed 42), holding out whole states (20% of 51 state groups); all preprocessing fits training data only. Quadratic multivariable Ridge includes squares and pairwise interactions; alpha is selected only by five-fold state-group CV inside training. A training-mean baseline is evaluated on the same test rows. No statistical significance claim is made. State holdout reduces geographic leakage but one split does not establish transfer to other years or every state. Counts differ by target when a needed indicator is missing. Test metrics are unweighted across counties, not population-weighted; predictions may exceed 0–100 because these are unconstrained regressions. Outcomes share socioeconomic context and ACS measurement error.

                 target           model  train_n  test_n   test_r2  test_rmse  test_mae                                                                                        predictors
           poverty_rate      train_mean     2172     971 -0.113839   6.753562  5.101877 percent_under_18;median_household_income;unemployment_rate;broadband_internet_rate;log_population
           poverty_rate multiple_linear     2172     971  0.636345   3.858926  2.723774 percent_under_18;median_household_income;unemployment_rate;broadband_internet_rate;log_population
           poverty_rate quadratic_ridge     2172     971  0.734322   3.298373  2.354106 percent_under_18;median_household_income;unemployment_rate;broadband_internet_rate;log_population
broadband_internet_rate      train_mean     2172     971 -0.041961   6.580578  4.851604            percent_under_18;median_household_income;poverty_rate;unemployment_rate;log_population
broadband_internet_rate multiple_linear     2172     971  0.461784   4.729516  3.269369            percent_under_18;median_household_income;poverty_rate;unemployment_rate;log_population
broadband_internet_rate quadratic_ridge     2172     971  0.471226   4.687849  3.215525            percent_under_18;median_household_income;poverty_rate;unemployment_rate;log_population

Linear vs quadratic bivariate comparisons use the same held-out states and training-fitted transforms. Training fit improvement is not evidence of better generalization. Comparisons are exploratory and test-set reuse across displayed models limits strong model-selection claims. Four-variable scatter encodes income, broadband, poverty color and population size; fitted-vs-observed plots are held-out multivariable predictions, not bivariate fits mislabeled as multiple regression.

## Boundary audit
boundary       status               
acs2024        matched                  3144
               outside_50_states_DC       78
legacy_plotly  data_without_geometry      13
               geometry_without_data      12
               matched                  3131
               outside_50_states_DC       78

Legacy data without geometry:
     boundary GEOID                                                        name                status
legacy_plotly 02063                                 Chugach Census Area, Alaska data_without_geometry
legacy_plotly 02066                            Copper River Census Area, Alaska data_without_geometry
legacy_plotly 02158                                Kusilvak Census Area, Alaska data_without_geometry
legacy_plotly 09110                        Capitol Planning Region, Connecticut data_without_geometry
legacy_plotly 09120             Greater Bridgeport Planning Region, Connecticut data_without_geometry
legacy_plotly 09130 Lower Connecticut River Valley Planning Region, Connecticut data_without_geometry
legacy_plotly 09140               Naugatuck Valley Planning Region, Connecticut data_without_geometry
legacy_plotly 09150       Northeastern Connecticut Planning Region, Connecticut data_without_geometry
legacy_plotly 09160                Northwest Hills Planning Region, Connecticut data_without_geometry
legacy_plotly 09170      South Central Connecticut Planning Region, Connecticut data_without_geometry
legacy_plotly 09180       Southeastern Connecticut Planning Region, Connecticut data_without_geometry
legacy_plotly 09190            Western Connecticut Planning Region, Connecticut data_without_geometry
legacy_plotly 46102                          Oglala Lakota County, South Dakota data_without_geometry

Every data GEOID is checked, including unscored counties. Census Generalized ACS2024 20M boundaries replace the stale Plotly boundaries. The audit includes both data-without-geometry and geometry-without-data rows plus territories outside scope. Connecticut planning regions and Alaska county-equivalent changes are handled by contemporaneous GEOIDs, never by simply renaming old polygons. Boundary simplification affects display geometry; it is unsuitable for precise local spatial analysis. All current data GEOIDs must match or the pipeline fails. The map displays unscored counties in gray. Puerto Rico and other territories are outside this project's 50-state-plus-DC universe.

## Reproduction and limitations
Install requirements, then run `python scripts/blueprint_pipeline.py`; working directory is irrelevant. `--refresh` explicitly refreshes network caches and requires CENSUS_API_KEY for ACS. `python scripts/06_week7_reproducibility_check.py` validates schemas, identifiers, missingness, split separation, metrics and files, rather than declaring success based on existence alone. `python scripts/07_week8_final_project_review.py` invokes the same checks. requirements-lock.txt records the tested environment. SHA-256 manifest inventories current inputs, scripts and outputs. Archive scripts are historical and are not entry points.

No service inventory, nonprofit outcomes, local partner capacity, cost, resident preferences, or program demand was observed. These gaps prevent treating ranks or model associations as allocation recommendations. Fresh MOEs require a working Census API key if absent in cache. Cached inputs make offline reruns possible; refresh can change results and should be reviewed.

## Sources
- ACS variables and annotations: https://api.census.gov/data/2024/acs/acs5/profile/variables.json
- Under 18: https://api.census.gov/data/2024/acs/acs5/profile/variables/DP05_0019PE.json
- Broadband subscription (not infrastructure availability): https://api.census.gov/data/2024/acs/acs5/profile/variables/DP02_0154PE.json
- Census MOE/SE: https://www.census.gov/programs-surveys/acs/methodology/sample-size-and-data-quality/quality-standards-metrics-definitions.html
- ACS 2024 boundaries: https://www.census.gov/programs-surveys/acs/geography-acs/geography-boundaries-by-year/2024.html
- Boundary service: https://tigerweb.geo.census.gov/arcgis/rest/services/Generalized_ACS2024/State_County/MapServer/13/query
- Historical map boundary source: https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json
