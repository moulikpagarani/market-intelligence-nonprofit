# BluePrint: county outreach screening

Audited ACS 2024 five-year indicators, relative screening ranks, uncertainty flags, geographic match audits, and state-held-out descriptive models. No model predicts the constructed score.

```sh
python -m pip install -r requirements.txt
python scripts/blueprint_pipeline.py
python scripts/06_week7_reproducibility_check.py
```

Paths work from any directory when the script path is absolute. Inputs are cached; use `--refresh` to recollect, with CENSUS_API_KEY in the environment. No API key is stored in source. Current results and limitations: [technical report](reports/week7_technical_documentation.md). All 3,144 original counties remain represented, including unscored De Baca. Absolute units are in data/cleaned/absolute_indicators_and_uncertainty.csv. The interactive map uses ACS2024 boundaries. Historical outputs are preserved in archive/pre_audit_2026_10_18 and must not be cited as current validation. Tests use only the standard library plus declared dependencies.
