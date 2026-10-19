"""Regression checks against lost IDs, silent exclusions and misleading score semantics."""
from pathlib import Path
import unittest
import sys
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
import blueprint_pipeline as bp
class ReproducibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=pd.read_csv(R/'data/cleaned/us_county_market_intelligence_acs_2024_analysis_ready.csv',dtype={'GEOID':str,'state':str,'county':str})
    def test_geoid_roundtrip_and_original_universe(self):
        raw=pd.read_csv(R/'data/raw/us_county_market_intelligence_acs_2024_raw.csv',dtype=str)
        self.assertEqual(set(raw.GEOID),set(self.d.GEOID))
        self.assertTrue(self.d.GEOID.str.fullmatch(r'\d{5}').all())
        self.assertTrue(self.d.GEOID.str.startswith('0').any())
    def test_indicator_direction_and_score(self):
        d=self.d.dropna(subset=bp.IND)
        mapping={'target_population_indicator':'percent_under_18','economic_barrier_indicator':'poverty_rate','employment_barrier_indicator':'unemployment_rate','income_barrier_indicator':'median_household_income','digital_access_barrier_indicator':'broadband_internet_rate'}
        for indicator,raw in mapping.items():
            expected=d[raw].rank(pct=True)
            if indicator in ['income_barrier_indicator','digital_access_barrier_indicator']:expected=1-expected
            np.testing.assert_allclose(d[indicator],expected)
        np.testing.assert_allclose(d[bp.SCORE],d[bp.IND].mean(axis=1)*100)
    def test_uniform_improvement_preserves_ranks(self):
        d=self.d.dropna(subset=bp.IND)
        np.testing.assert_allclose(d.poverty_rate.rank(pct=True),(d.poverty_rate*.8).rank(pct=True))
    def test_de_baca_retained_and_missing_explicit(self):
        row=self.d.set_index('GEOID').loc['35011']
        self.assertEqual(row.total_population,1576)
        if pd.isna(row.median_household_income):self.assertTrue(pd.isna(row[bp.SCORE]))
        audit=pd.read_csv(R/'reports/missing_value_audit.csv',dtype={'GEOID':str})
        self.assertIn('35011',set(audit.GEOID))
    def test_state_holdout_and_metric_evidence(self):
        bp.verify()
    def test_sensitivity_profiles_valid(self):
        d=pd.read_csv(R/'reports/weight_sensitivity.csv')
        np.testing.assert_allclose(d[bp.IND].sum(axis=1),1)
        self.assertTrue(d.top50_overlap.between(0,50).all())
        self.assertEqual(d.set_index('profile').loc['equal_five','max_absolute_rank_shift'],0)
if __name__=='__main__':unittest.main()
