"""Generate final BluePrint model enhancements from the repository dataset.
Run: python scripts/07_final_model_enhancements.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
repo = Path(__file__).resolve().parents[1]

# Ensure folders
for p in ['config', 'data/cleaned', 'reports', 'visuals', 'recommendations', 'scripts', 'docs']:
    (repo / p).mkdir(parents=True, exist_ok=True)

# ---------- Load data ----------
df = pd.read_csv(repo / 'data/cleaned/us_county_market_intelligence_acs_2024_analysis_ready.csv')

# ---------- Customization profiles ----------
profiles = pd.DataFrame([
    {
        'profile_name': 'Youth and Education Default',
        'mission_focus': 'Youth workshops, school outreach, youth education, enrichment programs',
        'target_population_indicator': 0.30,
        'economic_barrier_indicator': 0.20,
        'employment_barrier_indicator': 0.10,
        'income_barrier_indicator': 0.20,
        'digital_access_barrier_indicator': 0.20,
        'notes': 'Prioritizes youth population while still accounting for economic and digital access barriers.'
    },
    {
        'profile_name': 'Community Services',
        'mission_focus': 'Food access, family services, housing support, emergency assistance, resource navigation',
        'target_population_indicator': 0.10,
        'economic_barrier_indicator': 0.30,
        'employment_barrier_indicator': 0.25,
        'income_barrier_indicator': 0.25,
        'digital_access_barrier_indicator': 0.10,
        'notes': 'Prioritizes economic need and employment barriers.'
    },
    {
        'profile_name': 'Mental Health and Wellness',
        'mission_focus': 'Youth wellbeing, body image, confidence, self-esteem, mental health education',
        'target_population_indicator': 0.30,
        'economic_barrier_indicator': 0.20,
        'employment_barrier_indicator': 0.10,
        'income_barrier_indicator': 0.15,
        'digital_access_barrier_indicator': 0.25,
        'notes': 'Prioritizes youth population and access barriers that may affect wellbeing outreach.'
    },
    {
        'profile_name': 'Digital Outreach Heavy',
        'mission_focus': 'Programs relying on online campaigns, social media, virtual workshops, and remote engagement',
        'target_population_indicator': 0.20,
        'economic_barrier_indicator': 0.15,
        'employment_barrier_indicator': 0.10,
        'income_barrier_indicator': 0.15,
        'digital_access_barrier_indicator': 0.40,
        'notes': 'Prioritizes broadband barriers because digital access shapes outreach strategy.'
    },
    {
        'profile_name': 'Be Kind 5 Prototype',
        'mission_focus': 'Kindness and confidence workshops for motivated youth groups',
        'target_population_indicator': 0.35,
        'economic_barrier_indicator': 0.15,
        'employment_barrier_indicator': 0.10,
        'income_barrier_indicator': 0.15,
        'digital_access_barrier_indicator': 0.25,
        'notes': 'Prototype customization based on youth workshop outreach and engagement needs.'
    },
    {
        'profile_name': 'Mirror Echoes Prototype',
        'mission_focus': 'Body image, self-esteem, and confidence workshops for youth audiences',
        'target_population_indicator': 0.30,
        'economic_barrier_indicator': 0.20,
        'employment_barrier_indicator': 0.10,
        'income_barrier_indicator': 0.15,
        'digital_access_barrier_indicator': 0.25,
        'notes': 'Prototype customization based on youth wellbeing outreach and access barriers.'
    },
])
indicator_cols = [
    'target_population_indicator',
    'economic_barrier_indicator',
    'employment_barrier_indicator',
    'income_barrier_indicator',
    'digital_access_barrier_indicator'
]
profiles.to_csv(repo / 'config/nonprofit_customization_profiles.csv', index=False)

# Generate customized scores for each profile
custom_outputs = []
for _, prof in profiles.iterrows():
    weights = prof[indicator_cols].astype(float)
    score = (df[indicator_cols] * weights.values).sum(axis=1) * 100
    tmp = df[['county_name','state_name','total_population','percent_under_18','poverty_rate','unemployment_rate','median_household_income','broadband_internet_rate']].copy()
    tmp['profile_name'] = prof['profile_name']
    tmp['customized_opportunity_score'] = score.round(2)
    tmp['rank_within_profile'] = tmp['customized_opportunity_score'].rank(ascending=False, method='first').astype(int)
    custom_outputs.append(tmp)
custom_scores = pd.concat(custom_outputs, ignore_index=True)
custom_scores.to_csv(repo / 'data/cleaned/customized_opportunity_scores_by_profile.csv', index=False)

# Top recommendations per profile
recs = []
for name, group in custom_scores.groupby('profile_name'):
    top = group.sort_values('customized_opportunity_score', ascending=False).head(10)
    for _, r in top.iterrows():
        recs.append({
            'profile_name': name,
            'county_name': r['county_name'],
            'score': r['customized_opportunity_score'],
            'why_flagged': 'High customized opportunity score based on profile-specific weights.',
            'suggested_next_step': 'Review local partners, validate need with interviews, and customize outreach materials before campaign launch.'
        })
recommendations = pd.DataFrame(recs)
recommendations.to_csv(repo / 'recommendations/customized_nonprofit_recommendations.csv', index=False)

# ---------- Multiple linear regression ----------
def standardize(s):
    s = pd.Series(s).astype(float)
    return (s - s.mean()) / s.std(ddof=0)

def multi_regression(data, y_col, x_cols, model_name):
    clean = data[[y_col] + x_cols].dropna().copy()
    y = clean[y_col].astype(float).values
    X_raw = clean[x_cols].astype(float)
    X = np.column_stack([np.ones(len(X_raw))] + [standardize(X_raw[c]).values for c in x_cols])
    beta, residuals, rank, svals = np.linalg.lstsq(X, y, rcond=None)
    y_hat = X @ beta
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot
    n = len(y)
    p = len(x_cols)
    adj_r2 = 1 - (1-r2) * (n-1) / (n-p-1)
    out = []
    out.append({'model_name': model_name, 'target_variable': y_col, 'predictor': 'Intercept', 'coefficient': beta[0], 'r_squared': r2, 'adjusted_r_squared': adj_r2, 'n_counties': n})
    for col, coef in zip(x_cols, beta[1:]):
        out.append({'model_name': model_name, 'target_variable': y_col, 'predictor': col, 'coefficient': coef, 'r_squared': r2, 'adjusted_r_squared': adj_r2, 'n_counties': n})
    return pd.DataFrame(out), y, y_hat

x_cols = ['percent_under_18','poverty_rate','unemployment_rate','median_household_income','broadband_internet_rate']
models = []
model_specs = [
    ('market_outreach_opportunity_score', 'Multiple Regression: Opportunity Score', x_cols),
    ('poverty_rate', 'Multiple Regression: Poverty Rate', [c for c in x_cols if c != 'poverty_rate']),
    ('broadband_internet_rate', 'Multiple Regression: Broadband Access', [c for c in x_cols if c != 'broadband_internet_rate']),
]
for y_col, name, predictors in model_specs:
    res, y, y_hat = multi_regression(df, y_col, predictors, name)
    models.append(res)
multireg = pd.concat(models, ignore_index=True)
multireg.to_csv(repo / 'reports/final_multiple_regression_results.csv', index=False)

# ---------- Nonlinear polynomial comparisons ----------
def poly_compare(data, x_col, y_col, pair_name):
    clean = data[[x_col,y_col]].dropna().copy()
    x = clean[x_col].astype(float).values
    y = clean[y_col].astype(float).values
    # Linear
    b1 = np.polyfit(x, y, 1)
    ylin = np.polyval(b1, x)
    r2_lin = 1 - np.sum((y-ylin)**2)/np.sum((y-y.mean())**2)
    # Quadratic
    b2 = np.polyfit(x, y, 2)
    yquad = np.polyval(b2, x)
    r2_quad = 1 - np.sum((y-yquad)**2)/np.sum((y-y.mean())**2)
    return {
        'pair_name': pair_name,
        'x_variable': x_col,
        'y_variable': y_col,
        'linear_r_squared': r2_lin,
        'quadratic_r_squared': r2_quad,
        'r_squared_change': r2_quad - r2_lin,
        'n_counties': len(clean),
        'linear_coefficients': list(b1),
        'quadratic_coefficients': list(b2),
    }
nonlinear_rows = [
    poly_compare(df, 'median_household_income','poverty_rate','Income vs Poverty'),
    poly_compare(df, 'median_household_income','broadband_internet_rate','Income vs Broadband'),
    poly_compare(df, 'poverty_rate','broadband_internet_rate','Poverty vs Broadband'),
    poly_compare(df, 'unemployment_rate','poverty_rate','Unemployment vs Poverty'),
]
nonlinear = pd.DataFrame(nonlinear_rows)
nonlinear.to_csv(repo / 'reports/final_nonlinear_regression_comparison.csv', index=False)

# ---------- Visuals ----------
plt.rcParams.update({'font.size': 10})
colors = {
    'Target Population': '#2F80ED',
    'Economic Need': '#F2994A',
    'Employment Barrier': '#EB5757',
    'Income Barrier': '#9B51E0',
    'Digital Access Barrier': '#27AE60',
}
var_category = {
    'percent_under_18':'Target Population',
    'poverty_rate':'Economic Need',
    'unemployment_rate':'Employment Barrier',
    'median_household_income':'Income Barrier',
    'broadband_internet_rate':'Digital Access Barrier',
    'target_population_indicator':'Target Population',
    'economic_barrier_indicator':'Economic Need',
    'employment_barrier_indicator':'Employment Barrier',
    'income_barrier_indicator':'Income Barrier',
    'digital_access_barrier_indicator':'Digital Access Barrier'
}

# Variable framework
fig, ax = plt.subplots(figsize=(12, 6))
ax.axis('off')
ax.set_title('Color-Coded Variable Framework for BluePrint', fontsize=18, weight='bold', pad=20)
items = [
    ('Youth %', 'Target Population', 'Larger youth audience'),
    ('Poverty Rate', 'Economic Need', 'Economic barrier'),
    ('Unemployment', 'Employment Barrier', 'Job/economic pressure'),
    ('Lower Income', 'Income Barrier', 'Resource constraint'),
    ('Lower Broadband', 'Digital Access Barrier', 'Digital outreach barrier'),
]
x_positions = np.linspace(0.08, 0.92, len(items))
for x, (label, cat, desc) in zip(x_positions, items):
    ax.add_patch(plt.Rectangle((x-0.08, 0.48), 0.16, 0.22, color=colors[cat], alpha=0.9, transform=ax.transAxes))
    ax.text(x, 0.60, label, ha='center', va='center', transform=ax.transAxes, fontsize=12, weight='bold', color='white')
    ax.text(x, 0.40, cat, ha='center', va='center', transform=ax.transAxes, fontsize=10, weight='bold')
    ax.text(x, 0.31, desc, ha='center', va='center', transform=ax.transAxes, fontsize=9)
ax.text(0.5, 0.13, 'Each indicator is converted to a comparable scale and combined into the Market Outreach Opportunity Score.', ha='center', va='center', fontsize=12, weight='bold', transform=ax.transAxes)
fig.tight_layout()
fig.savefig(repo / 'visuals/final_color_coded_variable_framework.png', dpi=300, bbox_inches='tight')
plt.close(fig)

# Customized top 10 score comparison for three profiles
prof_names = ['Youth and Education Default','Community Services','Digital Outreach Heavy']
plot_data = []
for name in prof_names:
    top = custom_scores[custom_scores['profile_name']==name].sort_values('customized_opportunity_score', ascending=False).head(5)
    for _, r in top.iterrows():
        plot_data.append({'profile': name, 'county': r['county_name'].split(',')[0].replace(' County',''), 'score': r['customized_opportunity_score']})
plot_df = pd.DataFrame(plot_data)
fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharex=False)
for ax, name in zip(axes, prof_names):
    sub = plot_df[plot_df['profile']==name].sort_values('score')
    ax.barh(sub['county'], sub['score'], color='#2F80ED')
    ax.set_title(name, fontsize=11, weight='bold')
    ax.set_xlabel('Customized Score')
    ax.set_xlim(90, 100)
fig.suptitle('Customization Changes the Top Counties by Nonprofit Profile', fontsize=16, weight='bold')
fig.tight_layout()
fig.savefig(repo / 'visuals/final_customized_score_comparison_top5.png', dpi=300, bbox_inches='tight')
plt.close(fig)

# Multiple regression coefficients for opportunity score
coef_df = multireg[(multireg['model_name']=='Multiple Regression: Opportunity Score') & (multireg['predictor']!='Intercept')].copy()
coef_df['category'] = coef_df['predictor'].map(var_category)
coef_df['color'] = coef_df['category'].map(colors)
coef_df['label'] = coef_df['predictor'].replace({
    'percent_under_18':'Youth %',
    'poverty_rate':'Poverty',
    'unemployment_rate':'Unemployment',
    'median_household_income':'Income',
    'broadband_internet_rate':'Broadband'
})
fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(coef_df['label'], coef_df['coefficient'], color=coef_df['color'])
ax.axhline(0, color='black', linewidth=1)
r2 = coef_df['r_squared'].iloc[0]
ax.set_title(f'Opportunity Score Sensitivity: Five-Predictor Regression (R² = {r2:.3f})', fontsize=14, weight='bold')
ax.set_ylabel('Score-point change per 1 SD increase in predictor')
ax.set_xlabel('Predictor variable')
for tick in ax.get_xticklabels():
    tick.set_rotation(20)
fig.tight_layout()
fig.savefig(repo / 'visuals/final_multiple_regression_coefficients.png', dpi=300, bbox_inches='tight')
plt.close(fig)

# Linear vs nonlinear plots
def plot_linear_quad(x_col, y_col, fname, title, xlabel, ylabel):
    clean = df[[x_col,y_col]].dropna().copy()
    x = clean[x_col].values.astype(float)
    y = clean[y_col].values.astype(float)
    x_grid = np.linspace(x.min(), x.max(), 300)
    lin = np.polyfit(x, y, 1)
    quad = np.polyfit(x, y, 2)
    y_lin = np.polyval(lin, x)
    y_quad = np.polyval(quad, x)
    r2_lin = 1 - np.sum((y-y_lin)**2)/np.sum((y-y.mean())**2)
    r2_quad = 1 - np.sum((y-y_quad)**2)/np.sum((y-y.mean())**2)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(x, y, s=10, alpha=0.25, color='#2F80ED', label='County')
    ax.plot(x_grid, np.polyval(lin, x_grid), color='#EB5757', linewidth=2.5, label=f'Linear fit (R²={r2_lin:.3f})')
    ax.plot(x_grid, np.polyval(quad, x_grid), color='#27AE60', linewidth=2.5, label=f'Quadratic fit (R²={r2_quad:.3f})')
    ax.set_title(title, fontsize=14, weight='bold')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    fig.tight_layout()
    fig.savefig(repo / 'visuals' / fname, dpi=300, bbox_inches='tight')
    plt.close(fig)

plot_linear_quad('median_household_income','poverty_rate','final_linear_vs_nonlinear_income_poverty.png','Linear vs Nonlinear Fit: Income and Poverty','Median household income','Poverty rate')
plot_linear_quad('median_household_income','broadband_internet_rate','final_linear_vs_nonlinear_income_broadband.png','Linear vs Nonlinear Fit: Income and Broadband','Median household income','Broadband internet rate')
plot_linear_quad('poverty_rate','broadband_internet_rate','final_linear_vs_nonlinear_poverty_broadband.png','Linear vs Nonlinear Fit: Poverty and Broadband','Poverty rate','Broadband internet rate')

plot_linear_quad('unemployment_rate','poverty_rate','final_linear_vs_nonlinear_unemployment_poverty.png','Linear vs Nonlinear Fit: Unemployment and Poverty','Unemployment rate (%)','Poverty rate (%)')

# Color-coded scatter by opportunity category
fig, ax = plt.subplots(figsize=(9, 6))
cat_colors = {'High':'#EB5757','Medium':'#F2994A','Low':'#2F80ED'}
# handle actual category names
for cat, group in df.groupby('opportunity_category'):
    color = next((value for key, value in cat_colors.items() if str(cat).lower().startswith(key.split()[0].lower())), '#777777')
    ax.scatter(group['poverty_rate'], group['broadband_internet_rate'], s=12, alpha=0.5, label=cat, color=color)
ax.set_title('Color-Coded Counties by Opportunity Category', fontsize=14, weight='bold')
ax.set_xlabel('Poverty rate')
ax.set_ylabel('Broadband internet rate')
ax.legend()
fig.tight_layout()
fig.savefig(repo / 'visuals/final_color_coded_opportunity_scatter.png', dpi=300, bbox_inches='tight')
plt.close(fig)

# ---------- Report ----------
summary = f"""# Final Model Enhancement Summary

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

Opportunity score model R-squared: {r2:.3f}

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

{multireg[['model_name', 'r_squared', 'adjusted_r_squared', 'n_counties']].drop_duplicates().to_markdown(index=False)}

Linear versus quadratic comparison (in-sample):

{nonlinear[['pair_name', 'linear_r_squared', 'quadratic_r_squared', 'r_squared_change', 'n_counties']].to_markdown(index=False)}

## 8. Interpretation
These updates make BluePrint stronger because the final product is no longer only a fixed general score. It now supports mission-specific customization, clearer visual communication, more advanced regression modeling, and nonlinear exploratory analysis.
"""
(repo / 'reports/final_model_enhancement_summary.md').write_text(summary)


print('SUCCESS: Generated 8 visuals, 3 reports, customization profiles, county scores, and recommendations.')

# Verify and inventory every deliverable from this run.
import hashlib, json, platform
from PIL import Image
paths = [Path('scripts/07_final_model_enhancements.py'),
         Path('config/nonprofit_customization_profiles.csv'),
         Path('data/cleaned/customized_opportunity_scores_by_profile.csv'),
         Path('recommendations/customized_nonprofit_recommendations.csv')]
paths += sorted(Path('visuals').glob('__never__'))
paths += [p.relative_to(repo) for p in sorted((repo / 'visuals').glob('final_*.png'))]
paths += [Path('reports/final_multiple_regression_results.csv'), Path('reports/final_nonlinear_regression_comparison.csv'), Path('reports/final_model_enhancement_summary.md')]
assert len(df) == df[['county_name', 'state_name']].drop_duplicates().shape[0]
assert np.isfinite(df[x_cols + ['market_outreach_opportunity_score']].to_numpy(dtype=float)).all()
assert np.allclose(profiles[indicator_cols].sum(axis=1), 1)
assert len(custom_scores) == len(df) * len(profiles)
assert len(multireg) == 16 and len(nonlinear) == 4
for rel in paths:
    f = repo / rel
    assert f.is_file() and f.stat().st_size > 0, str(rel)
    if f.suffix == '.png':
        with Image.open(f) as im:
            im.verify()
manifest = pd.DataFrame([{'path': str(p), 'bytes': (repo/p).stat().st_size, 'sha256': hashlib.sha256((repo/p).read_bytes()).hexdigest()} for p in paths])
manifest.to_csv(repo / 'reports/final_output_manifest.csv', index=False)
print(manifest[['path', 'bytes']].to_string(index=False))
print(f'VERIFIED: {len(paths)} deliverables plus manifest; {len(df)} counties; {len(custom_scores)} customized rows.')
