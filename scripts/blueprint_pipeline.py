"""Audited ACS 2024 screening and descriptive prediction pipeline.
Run from any directory: python /path/to/scripts/blueprint_pipeline.py
Network acquisition is explicit (--refresh); cached inputs are checksum inventoried.
"""
from pathlib import Path
import argparse, hashlib, json, os, platform, sys
import numpy as np
import pandas as pd
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.express as px
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.model_selection import GroupShuffleSplit, GroupKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'
CLEAN=ROOT/'data/cleaned'
REPORT=ROOT/'reports'
VIS=ROOT/'visuals'
for p in [RAW,CLEAN,REPORT,VIS]: p.mkdir(exist_ok=True,parents=True)
BASE='https://api.census.gov/data/2024/acs/acs5/profile'
CODES={'total_population':'DP05_0001E','percent_under_18':'DP05_0019PE','median_household_income':'DP03_0062E','poverty_rate':'DP03_0128PE','unemployment_rate':'DP03_0009PE','broadband_internet_rate':'DP02_0154PE'}
IND=['target_population_indicator','economic_barrier_indicator','employment_barrier_indicator','income_barrier_indicator','digital_access_barrier_indicator']
FEATURES=list(CODES)[1:]
SCORE='market_outreach_opportunity_score'
STATES='01 02 04 05 06 08 09 10 11 12 13 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 53 54 55 56'.split()
BOUNDARY='https://tigerweb.geo.census.gov/arcgis/rest/services/Generalized_ACS2024/State_County/MapServer/13/query'
LEGACY='https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json'

def acquire(refresh=False):
    """Fail closed on partial API collection; do not log request URLs containing keys."""
    key=os.getenv('CENSUS_API_KEY')
    if refresh and not key: raise RuntimeError('--refresh requires CENSUS_API_KEY; cached data were not changed')
    path=RAW/'acs_2024_profile_with_moe.json'
    if refresh or not path.exists():
        if key:
            variables=['NAME']
            for c in CODES.values(): variables.extend([c,c[:-1]+'M',c+'A',c[:-1]+'MA'])
            response=requests.get(BASE,params={'get':','.join(variables),'for':'county:*','key':key},timeout=120)
            if response.status_code!=200: raise RuntimeError('Census acquisition failed; HTTP '+str(response.status_code))
            try: payload=response.json()
            except ValueError: raise RuntimeError('Census returned non-JSON; check CENSUS_API_KEY') from None
            if not isinstance(payload,list) or len(payload)<3000: raise RuntimeError('Incomplete Census response')
            path.write_text(json.dumps(payload))
        else:
            print('Census key unavailable: using original actual estimates; MOE availability is explicitly flagged.')
    geo=RAW/'counties_acs2024_20m.geojson'
    if refresh or not geo.exists():
        features=[]
        offset=0
        while True:
            result=requests.get(BOUNDARY,params={'where':'1=1','outFields':'GEOID,NAME,STATE,COUNTY','returnGeometry':'true','outSR':4326,'f':'geojson','resultOffset':offset,'resultRecordCount':500,'orderByFields':'GEOID'},timeout=120)
            result.raise_for_status(); data=result.json()
            if 'features' not in data: raise RuntimeError('Boundary service did not return features: '+str(data)[:300])
            features.extend(data['features'])
            if not data['features'] or len(data['features'])<500: break
            offset+=len(data['features'])
        if len(features)<3100: raise RuntimeError('Incomplete boundary acquisition')
        for f in features: f['id']=f['properties']['GEOID']
        geo.write_text(json.dumps({'type':'FeatureCollection','features':features}))
    legacy=RAW/'legacy_plotly_counties.geojson'
    if refresh or not legacy.exists():
        response=requests.get(LEGACY,timeout=120);response.raise_for_status();legacy.write_text(response.text)


def clean():
    original=pd.read_csv(RAW/'us_county_market_intelligence_acs_2024_raw.csv',dtype={'GEOID':str,'state':str,'county':str})
    payload=RAW/'acs_2024_profile_with_moe.json'
    if payload.exists():
        rows=json.loads(payload.read_text()); source=pd.DataFrame(rows[1:],columns=rows[0])
        source=source[source.state.isin(STATES)].copy()
        df=source.rename(columns={'NAME':'county_name',**{v:k for k,v in CODES.items()}})
        df['GEOID']=df.state+df.county
        for name,code in CODES.items():
            df[name+'_moe_raw']=df[code[:-1]+'M']
        df=df[['county_name','GEOID','state','county']+list(CODES)+[x+'_moe_raw' for x in CODES]].copy()
    else: df=original.copy()
    assert df.GEOID.str.fullmatch(r'\d{5}').all() and df.GEOID.is_unique
    assert set(df.state)==set(STATES)
    reasons=[]
    for c in CODES:
        values=pd.to_numeric(df[c],errors='coerce')
        for i in df.index[values.isna() | (values<0)]:
            reasons.append({'GEOID':df.loc[i,'GEOID'],'county_name':df.loc[i,'county_name'],'field':c,'raw_value':df.loc[i,c],'reason':'Census sentinel/unavailable' if pd.notna(values.loc[i]) else 'missing or nonnumeric'})
        df[c]=values.mask(values<0)
        if c!='median_household_income' and c!='total_population': assert df[c].dropna().between(0,100).all()
        raw=c+'_moe_raw'
        moe=pd.to_numeric(df[raw],errors='coerce') if raw in df else pd.Series(np.nan,index=df.index)
        for i in df.index[moe<0]: reasons.append({'GEOID':df.loc[i,'GEOID'],'county_name':df.loc[i,'county_name'],'field':c+'_moe','raw_value':moe.loc[i],'reason':'MOE sentinel; unavailable'})
        df[c+'_moe']=moe.mask(moe<0)
        df[c+'_cv']=df[c+'_moe']/1.645/df[c].where(df[c]>0)
        df[c+'_precision_flag']=np.select([df[c+'_moe'].isna(),df[c].isna() | (df[c]<=0),df[c+'_cv']>0.30],['MOE unavailable','CV undefined','CV above 30%'],default='CV at most 30%')
    pd.DataFrame(reasons,columns=['GEOID','county_name','field','raw_value','reason']).to_csv(REPORT/'missing_value_audit.csv',index=False)
    df['county_clean']=df.county_name.str.rsplit(',',n=1).str[0]
    df['state_name']=df.county_name.str.rsplit(',',n=1).str[1].str.strip()
    df['small_population_flag']=df.total_population<20000
    df['any_moe_unavailable']=df[[c+'_moe' for c in CODES]].isna().any(axis=1)
    df['any_high_cv']=df[[c+'_cv' for c in CODES]].gt(.30).any(axis=1)
    complete=df[FEATURES].notna().all(axis=1)
    df['score_status']=np.where(complete,'complete relative score','incomplete indicators: score withheld')
    for ind,c,direction in zip(IND,['percent_under_18','poverty_rate','unemployment_rate','median_household_income','broadband_internet_rate'],[1,1,1,-1,-1]):
        ranks=df.loc[complete,c].rank(pct=True,method='average')
        df.loc[complete,ind]=ranks if direction==1 else 1-ranks
    df[SCORE]=df[IND].mean(axis=1,skipna=False)*100
    lo,hi=df[SCORE].quantile([.25,.75])
    df['opportunity_category']=np.select([~complete,df[SCORE]>=hi,df[SCORE]<=lo],['Not scored','Upper quartile (relative)','Lower quartile (relative)'],default='Middle half (relative)')
    df['population_size_category']=pd.cut(df.total_population,[0,50000,250000,1000000,np.inf],labels=['Small county','Medium county','Large county','Very large county'])
    df.to_csv(CLEAN/'us_county_market_intelligence_acs_2024_cleaned.csv',index=False)
    # Analysis-ready retains unscored counties; each analysis explicitly selects required fields.
    df.sort_values(SCORE,ascending=False).to_csv(CLEAN/'us_county_market_intelligence_acs_2024_analysis_ready.csv',index=False)
    df[complete].nlargest(50,SCORE).to_csv(CLEAN/'top_50_market_opportunity_counties.csv',index=False)
    df[['GEOID','county_name']+list(CODES)+[c+'_moe' for c in CODES]+[c+'_precision_flag' for c in CODES]+['small_population_flag','any_moe_unavailable','any_high_cv','score_status']].to_csv(CLEAN/'absolute_indicators_and_uncertainty.csv',index=False)
    return df


def sensitivities(df):
    d=df.dropna(subset=IND).copy()
    variants={'equal_five':[.2]*5,'economic_domain_balanced':[.25,.125,.25,.125,.25],'without_income':[.25,.25,.25,0,.25],'without_poverty':[.25,0,.25,.25,.25]}
    profiles=pd.read_csv(ROOT/'config/nonprofit_customization_profiles.csv')
    for _,row in profiles.iterrows(): variants[row.profile_name]=row[IND].astype(float).tolist()
    for i in range(5):
        w=np.ones(5);w[i]=0;variants['omit_'+IND[i]]=(w/w.sum()).tolist()
    base=d[SCORE].round(10).rank(ascending=False,method='average')
    top=set(d.nlargest(50,SCORE).GEOID)
    summary=[];outputs=[]
    for name,weights in variants.items():
        assert np.isclose(sum(weights),1) and min(weights)>=0
        scores=np.round((d[IND]*np.array(weights)).sum(axis=1).to_numpy()*100,10)
        ranks=pd.Series(scores,index=d.index).rank(ascending=False,method='average')
        sub=d[['GEOID','county_name','state_name']+list(CODES)].copy()
        sub['profile_name']=name;sub['customized_opportunity_score']=scores;sub['rank_within_profile']=ranks
        sub['rank_change_from_equal']=ranks-base
        outputs.append(sub)
        summary.append({'profile':name,'spearman_rank_correlation':ranks.corr(base),'top50_overlap':len(set(sub.nlargest(50,'customized_opportunity_score').GEOID)&top),'median_absolute_rank_shift':(ranks-base).abs().median(),'max_absolute_rank_shift':(ranks-base).abs().max(),**dict(zip(IND,weights))})
    out=pd.concat(outputs);out.to_csv(CLEAN/'customized_opportunity_scores_by_profile.csv',index=False)
    pd.DataFrame(summary).to_csv(REPORT/'weight_sensitivity.csv',index=False)
    rec=out.sort_values('customized_opportunity_score',ascending=False).groupby('profile_name',sort=False).head(10).copy()
    rec['suggested_next_step']='Illustrative review list only: verify local service availability, community preferences, population and estimate precision.'
    rec.to_csv(ROOT/'recommendations/customized_nonprofit_recommendations.csv',index=False)
    d[FEATURES].corr(method='pearson').to_csv(REPORT/'indicator_pearson_correlation.csv')
    d[FEATURES].corr(method='spearman').to_csv(REPORT/'indicator_spearman_correlation.csv')
    vif=[]
    X=StandardScaler().fit_transform(d[FEATURES])
    for i,c in enumerate(FEATURES):
        r2=LinearRegression().fit(np.delete(X,i,axis=1),X[:,i]).score(np.delete(X,i,axis=1),X[:,i])
        vif.append({'predictor':c,'VIF':1/(1-r2)})
    pd.DataFrame(vif).to_csv(REPORT/'predictor_vif.csv',index=False)
    fig,ax=plt.subplots(figsize=(9,5));s=pd.DataFrame(summary).iloc[:4];ax.bar(s.profile,s.median_absolute_rank_shift,color=['#0072B2','#E69F00','#009E73','#CC79A7']);ax.set(ylabel='Median absolute county rank shift',title='Weight choices change relative screening ranks');ax.tick_params(axis='x',rotation=15);fig.tight_layout();fig.savefig(VIS/'weight_sensitivity.png',dpi=160);plt.close(fig)
    return pd.DataFrame(summary)


def models(df):
    # A single fixed state-held-out split; outcomes never constructed from their predictors.
    train_states,test_states=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=42).split(df,groups=df.state))
    train_ids=set(df.iloc[train_states].GEOID);test_ids=set(df.iloc[test_states].GEOID)
    pd.DataFrame({'GEOID':df.GEOID,'state':df.state,'split':np.where(df.GEOID.isin(test_ids),'test','train')}).to_csv(REPORT/'model_split.csv',index=False)
    metrics=[];coeff=[];predictions=[];selection=[]
    for target in ['poverty_rate','broadband_internet_rate']:
        cols=[c for c in FEATURES if c!=target]+['log_population']
        d=df.copy();d['log_population']=np.log1p(d.total_population);d=d.dropna(subset=[target]+cols)
        train=d[d.GEOID.isin(train_ids)];test=d[d.GEOID.isin(test_ids)]
        X=train[cols];y=train[target];Xt=test[cols];yt=test[target]
        for name in ['train_mean','multiple_linear','quadratic_ridge']:
            if name=='train_mean': model=DummyRegressor()
            elif name=='multiple_linear': model=make_pipeline(StandardScaler(),LinearRegression())
            else:
                candidates=[]
                for alpha in [.1,1,10,100]:
                    candidate=make_pipeline(StandardScaler(),PolynomialFeatures(2,include_bias=False),Ridge(alpha=alpha))
                    rmse=-cross_val_score(candidate,X,y,groups=train.state,cv=GroupKFold(5),scoring='neg_root_mean_squared_error').mean()
                    candidates.append((rmse,alpha));selection.append({'target':target,'alpha':alpha,'train_state_cv_rmse':rmse})
                alpha=min(candidates)[1]
                model=make_pipeline(StandardScaler(),PolynomialFeatures(2,include_bias=False),Ridge(alpha=alpha))
            model.fit(X,y);p=model.predict(Xt)
            metrics.append({'target':target,'model':name,'train_n':len(train),'test_n':len(test),'test_r2':r2_score(yt,p),'test_rmse':np.sqrt(mean_squared_error(yt,p)),'test_mae':mean_absolute_error(yt,p),'predictors':';'.join(cols)})
            predictions.extend({'GEOID':g,'target':target,'model':name,'observed':a,'predicted':b} for g,a,b in zip(test.GEOID,yt,p))
            if name=='multiple_linear':
                reg=model[-1]
                coeff.extend({'target':target,'predictor':c,'coefficient_per_train_SD':b} for c,b in zip(cols,reg.coef_))
                fig,ax=plt.subplots(figsize=(9,5));ax.scatter(yt,p,c=test.poverty_rate if target!='poverty_rate' else test.broadband_internet_rate,cmap='viridis',s=16,alpha=.6);mn=min(yt.min(),p.min());mx=max(yt.max(),p.max());ax.plot([mn,mx],[mn,mx],'k--');ax.set(xlabel='Observed '+target+' (%)',ylabel='Held-out prediction (%)',title='Multiple linear model: unseen states');fig.colorbar(ax.collections[0],ax=ax,label=('Poverty' if target!='poverty_rate' else 'Broadband subscription')+' (%)');fig.tight_layout();fig.savefig(VIS/('heldout_'+target+'.png'),dpi=160);plt.close(fig)
    pd.DataFrame(metrics).to_csv(REPORT/'final_multiple_regression_results.csv',index=False)
    pd.DataFrame(coeff).to_csv(REPORT/'multivariable_coefficients.csv',index=False)
    pd.DataFrame(predictions).to_csv(REPORT/'heldout_predictions.csv',index=False)
    pd.DataFrame(selection).to_csv(REPORT/'training_cv_selection.csv',index=False)
    # Univariate nonlinear comparisons share exactly the same state holdout.
    pairs=[('median_household_income','poverty_rate','income_poverty'),('median_household_income','broadband_internet_rate','income_broadband'),('poverty_rate','broadband_internet_rate','poverty_broadband'),('unemployment_rate','poverty_rate','unemployment_poverty')]
    rows=[]
    for x,y,label in pairs:
        d=df.dropna(subset=[x,y]);tr=d[d.GEOID.isin(train_ids)];te=d[d.GEOID.isin(test_ids)]
        fig,ax=plt.subplots(figsize=(9,5));ax.scatter(te[x],te[y],s=10,alpha=.25,color='#777777',label='Held-out counties')
        grid=np.linspace(tr[x].min(),tr[x].max(),300).reshape(-1,1)
        for deg,color in [(1,'#0072B2'),(2,'#D55E00')]:
            m=make_pipeline(StandardScaler(),PolynomialFeatures(deg,include_bias=False),LinearRegression()).fit(tr[[x]],tr[y]);p=m.predict(te[[x]])
            metric={'x':x,'y':y,'degree':deg,'test_r2':r2_score(te[y],p),'test_rmse':np.sqrt(mean_squared_error(te[y],p)),'train_n':len(tr),'test_n':len(te)};rows.append(metric)
            ax.plot(grid[:,0],m.predict(pd.DataFrame(grid,columns=[x])),color=color,label=f'Degree {deg}; test RMSE {metric["test_rmse"]:.2f}')
        ax.set(xlabel=x.replace('_',' ')+(' ($)' if 'income' in x else ' (%)'),ylabel=y.replace('_',' ')+' (%)',title='Training fits; state-held-out evaluation');ax.legend();fig.tight_layout();fig.savefig(VIS/f'final_linear_vs_nonlinear_{label}.png',dpi=160);plt.close(fig)
    pd.DataFrame(rows).to_csv(REPORT/'final_nonlinear_regression_comparison.csv',index=False)
    return pd.DataFrame(metrics)


def mapping(df):
    new=json.loads((RAW/'counties_acs2024_20m.geojson').read_text());old=json.loads((RAW/'legacy_plotly_counties.geojson').read_text())
    rows=[]
    for name,geo in [('legacy_plotly',old),('acs2024',new)]:
        features=geo['features'];ids=[str(f.get('id',f['properties'].get('GEOID'))) for f in features];assert len(ids)==len(set(ids))
        universe=set(ids);observed=set(df.GEOID)
        for _,r in df.iterrows(): rows.append({'boundary':name,'GEOID':r.GEOID,'name':r.county_name,'status':'matched' if r.GEOID in universe else 'data_without_geometry'})
        for f in features:
            g=str(f.get('id',f['properties'].get('GEOID')))
            if g not in observed: rows.append({'boundary':name,'GEOID':g,'name':f['properties'].get('NAME',f['properties'].get('name','')),'status':'geometry_without_data' if g[:2] in STATES else 'outside_50_states_DC'})
    audit=pd.DataFrame(rows);audit.to_csv(REPORT/'map_geoid_audit.csv',index=False)
    missing=audit[(audit.boundary=='acs2024')&(audit.status=='data_without_geometry')]
    if len(missing): raise AssertionError('ACS2024 data lack geometry; see map_geoid_audit.csv')
    # Gray unscored polygons are a separate layer; no missing county silently disappears.
    import plotly.graph_objects as go
    valid=df.dropna(subset=[SCORE]);unscored=df[df[SCORE].isna()]
    fig=px.choropleth(valid,geojson=new,locations='GEOID',color=SCORE,scope='usa',hover_name='county_name',hover_data=['GEOID','total_population','poverty_rate','median_household_income','broadband_internet_rate','small_population_flag','any_moe_unavailable'],range_color=(0,100),title='Relative screening score — not measured service need (ACS 2024)')
    fig.add_trace(go.Choropleth(geojson=new,locations=unscored.GEOID,z=np.zeros(len(unscored)),colorscale=[[0,'#aaaaaa'],[1,'#aaaaaa']],showscale=False,text=unscored.county_name,hovertemplate='%{text}<br>Score withheld: incomplete indicators<extra></extra>',name='Not scored'))
    fig.update_layout(margin=dict(l=0,r=0,b=0,t=60));fig.write_html(VIS/'us_county_opportunity_score_map.html',include_plotlyjs=True)
    return audit


def visuals(df):
    fig,axes=plt.subplots(2,3,figsize=(14,8))
    for ax,c in zip(axes.flat,CODES):
        ax.hist(df[c].dropna(),bins=35,color='#0072B2',edgecolor='white');ax.set_title(c);ax.set_xlabel('People' if c=='total_population' else '$ (2024 inflation-adjusted)' if 'income' in c else '%');ax.set_ylabel('Counties')
    fig.suptitle('Absolute ACS indicator distributions — observed units');fig.tight_layout();fig.savefig(VIS/'absolute_indicator_distributions.png',dpi=160);plt.close(fig)
    d=df.dropna(subset=FEATURES)
    fig,ax=plt.subplots(figsize=(10,6));sc=ax.scatter(d.median_household_income,d.broadband_internet_rate,c=d.poverty_rate,s=10+np.clip(np.sqrt(d.total_population)/15,0,100),cmap='viridis',alpha=.55);fig.colorbar(sc,ax=ax,label='Poverty (%)');ax.set(xlabel='Median household income ($, 2024 adjusted)',ylabel='Households with broadband subscription (%)',title='Four observed variables: color = poverty; size = population');fig.tight_layout();fig.savefig(VIS/'final_color_coded_opportunity_scatter.png',dpi=160);plt.close(fig)
    c=pd.read_csv(REPORT/'multivariable_coefficients.csv');fig,axes=plt.subplots(1,2,figsize=(14,6))
    for ax,(target,group) in zip(axes,c.groupby('target')):
        colors={'percent_under_18':'#0072B2','median_household_income':'#E69F00','poverty_rate':'#009E73','unemployment_rate':'#CC79A7','broadband_internet_rate':'#56B4E9','log_population':'#D55E00'}; ax.barh(group.predictor.str.replace('_',' '),group.coefficient_per_train_SD,color=[colors[c] for c in group.predictor]);ax.axvline(0,color='k');ax.set(title=target.replace('_',' '),xlabel='Percentage-point change per training SD')
    fig.tight_layout();fig.savefig(VIS/'final_multiple_regression_coefficients.png',dpi=160);plt.close(fig)


def document(df,metrics,sensitivity,audit):
    n=df[SCORE].notna().sum();mean=df[SCORE].mean();corr=df.median_household_income.corr(df.poverty_rate)
    missing=pd.read_csv(REPORT/'missing_value_audit.csv',dtype={'GEOID':str})
    mapcounts=audit.groupby(['boundary','status']).size().to_string()
    text=f'''# BluePrint audited technical report

## Evidence and scope
Run date: 2026-10-18 (America/New_York). ACS 2024 five-year estimates describe 2020–2024, not a point-in-time survey. {len(df)} counties/equivalents across 50 states and DC; {n} complete scores. Original raw data and pre-audit code/outputs are preserved under archive/pre_audit_2026_10_18. Historical outputs are not current evidence. No synthetic ACS values or imputed county incomes were introduced.

## Correct interpretation of scores
The score is 100 times the mean of five average percentile ranks; income and broadband are reversed using 1-rank. Ranking uses only counties with all five indicators. Mean is {mean:.8f}; with this exact convention its algebraic expectation is 50 + 10/n = {50+10/n:.8f}, not exactly 50 (the old report rounded it). An upper-quartile label selects approximately one quarter of complete counties, with ties possibly changing counts. It does not indicate an absolute severity cutoff, service gaps, reachable audience, or intervention benefit. A common monotone improvement preserving ranks leaves scores unchanged. Across-year or changed-universe score comparisons require a fixed reference distribution. Absolute indicator CSV and distributions retain actual units. Percent under 18 is a share, not a count; total population is supplied separately. Youth counts inferred from shares would be approximate and are not presented as direct ACS counts.

## Missing values and precision
{missing.to_string(index=False)}

De Baca (35011) remains in both cleaned and analysis-ready tables and the gray map layer; incomplete scores are withheld. Raw sentinels are recorded before conversion; no partial-indicator average is used. Small-population flag (<20,000) is an analyst screening rule, not evidence of low precision. MOE unavailable for {int(df.any_moe_unavailable.sum())} counties; high CV for at least one available field: {int(df.any_high_cv.sum())}. CV = MOE / 1.645 / estimate, only for positive estimates. CV >30% is a review flag chosen for this project, not a universal Census publication rule. Zero estimates have undefined CV. Missing MOEs are never labeled reliable. Marginal MOEs do not supply joint covariance: no score confidence intervals or probability-of-top-rank claims are made. MOE sentinels and annotations must be inspected when available. ACS population estimates are survey estimates, not sample sizes.

## Income–poverty overlap and weights
Pearson correlation between income and poverty: {corr:.4f}. Full Pearson/Spearman matrices and predictor VIFs are saved. The baseline gives income and poverty 40% combined weight, so correlated economic deprivation may receive extra emphasis. Economic-domain-balanced weights allocate 25% total across those two variables. Omission and six illustrative mission profiles are compared using rank correlation, rank shifts, and top-50 overlap; these are sensitivity exercises, not validated mission preferences. No universal optimal weights or new absolute composite need threshold is asserted.

{sensitivity.iloc[:4].to_string(index=False)}

## Prediction without circularity
Removed score-on-components regression from active scripts and current results. Outcomes are actual poverty and broadband subscription percentages, each predicted from the other four indicators and log(1+population). They are descriptive cross-sectional models, not outreach-impact or causal models. Split is fixed (seed 42), holding out whole states (20% of 51 state groups); all preprocessing fits training data only. Quadratic multivariable Ridge includes squares and pairwise interactions; alpha is selected only by five-fold state-group CV inside training. A training-mean baseline is evaluated on the same test rows. No statistical significance claim is made. State holdout reduces geographic leakage but one split does not establish transfer to other years or every state. Counts differ by target when a needed indicator is missing. Test metrics are unweighted across counties, not population-weighted; predictions may exceed 0–100 because these are unconstrained regressions. Outcomes share socioeconomic context and ACS measurement error.

{metrics.to_string(index=False)}

Linear vs quadratic bivariate comparisons use the same held-out states and training-fitted transforms. Training fit improvement is not evidence of better generalization. Comparisons are exploratory and test-set reuse across displayed models limits strong model-selection claims. Four-variable scatter encodes income, broadband, poverty color and population size; fitted-vs-observed plots are held-out multivariable predictions, not bivariate fits mislabeled as multiple regression.

## Boundary audit
{mapcounts}

Legacy data without geometry:
{audit[(audit.boundary=='legacy_plotly') & (audit.status=='data_without_geometry')].to_string(index=False)}

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
- Boundary service: {BOUNDARY}
- Historical map boundary source: {LEGACY}
'''
    (REPORT/'week7_technical_documentation.md').write_text(text)
    (REPORT/'final_model_enhancement_summary.md').write_text(text)
    (REPORT/'week8_final_project_summary.md').write_text('# Final review\n\n'+text)
    for f in ['week3_data_cleaning_summary.md','week4_regression_modeling_summary.md','week5_visualization_mapping_summary.md','week6_backend_integration_summary.md']:
        (REPORT/f).write_text('# Audited replacement\n\nSee week7_technical_documentation.md for current methods, actual results, validation and limitations. Original report retained under archive/pre_audit_2026_10_18/reports.\n\n'+text)
    (ROOT/'docs/data_dictionary.md').write_text('# Current data dictionary\n\n'+ '\n'.join(f'- `{name}`: ACS variable {code}; '+('people' if name=='total_population' else '2024 inflation-adjusted dollars' if 'income' in name else 'percent') for name,code in CODES.items())+'\n\nGEOID/state/county are strings of widths 5/2/3. *_moe: published 90% margin of error; *_cv: MOE/1.645/positive estimate. *_precision_flag separates unavailable MOE, undefined CV, and CV review categories. score_status explicitly identifies withheld scores. Sentinel audit preserves raw values. See reports/week7_technical_documentation.md.\n')
    (ROOT/'docs/decision_framework.md').write_text('# Decision limits\n\nUse absolute indicators, population, precision flags, and weight sensitivity together. Rankings screen for further inquiry; they do not measure unmet demand or program benefit. Validate existing services, local priorities and capacity before allocating resources. Scores are relative to the complete-county reference set.\n')
    (ROOT/'README.md').write_text('# BluePrint: county outreach screening\n\nAudited ACS 2024 five-year indicators, relative screening ranks, uncertainty flags, geographic match audits, and state-held-out descriptive models. No model predicts the constructed score.\n\n```sh\npython -m pip install -r requirements.txt\npython scripts/blueprint_pipeline.py\npython scripts/06_week7_reproducibility_check.py\n```\n\nPaths work from any directory when the script path is absolute. Inputs are cached; use `--refresh` to recollect, with CENSUS_API_KEY in the environment. No API key is stored in source. Current results and limitations: [technical report](reports/week7_technical_documentation.md). All 3,144 original counties remain represented, including unscored De Baca. Absolute units are in data/cleaned/absolute_indicators_and_uncertainty.csv. The interactive map uses ACS2024 boundaries. Historical outputs are preserved in archive/pre_audit_2026_10_18 and must not be cited as current validation. Tests use only the standard library plus declared dependencies.\n')
    (ROOT/'docs/project_plan.md').write_text('# Completion evidence\n\nCurrent pipeline and populated Week 7/8 reports supersede historical milestone claims. See verification_results.json and run_environment.json for actual verification. GitHub publication and original Colab execution require separate confirmed evidence; local script success does not imply either.\n')
    (ROOT/'docs/data_sources.md').write_text('# Sources\n\n'+text[text.index('## Sources'):])


def verify():
    d=pd.read_csv(CLEAN/'us_county_market_intelligence_acs_2024_analysis_ready.csv',dtype={'GEOID':str,'state':str,'county':str})
    assert d.GEOID.str.fullmatch(r'\d{5}').all() and d.GEOID.is_unique
    original=pd.read_csv(RAW/'us_county_market_intelligence_acs_2024_raw.csv',dtype={'GEOID':str})
    assert set(d.GEOID)==set(original.GEOID),'County universe changed'
    assert set(d.state)==set(STATES)
    de=d[d.GEOID=='35011'];assert len(de)==1
    if de.median_household_income.isna().iloc[0]: assert de[SCORE].isna().all()
    good=d.dropna(subset=IND);assert np.allclose(good[SCORE],good[IND].mean(axis=1)*100)
    assert d.loc[d[FEATURES].isna().any(axis=1),SCORE].isna().all()
    assert np.isclose(good[SCORE].mean(),50+10/len(good))
    assert d.loc[d.any_moe_unavailable,[c+'_precision_flag' for c in CODES]].eq('MOE unavailable').any(axis=1).all()
    audit=pd.read_csv(REPORT/'map_geoid_audit.csv',dtype={'GEOID':str});assert not ((audit.boundary=='acs2024')&(audit.status=='data_without_geometry')).any()
    split=pd.read_csv(REPORT/'model_split.csv',dtype={'GEOID':str,'state':str});assert split.groupby('state').split.nunique().max()==1
    metrics=pd.read_csv(REPORT/'final_multiple_regression_results.csv');assert SCORE not in set(metrics.target)
    preds=pd.read_csv(REPORT/'heldout_predictions.csv',dtype={'GEOID':str});assert set(preds.GEOID)<=set(split.loc[split.split=='test','GEOID'])
    for _,m in metrics.iterrows():
        p=preds[(preds.target==m.target)&(preds.model==m.model)];assert np.isclose(m.test_rmse,np.sqrt(mean_squared_error(p.observed,p.predicted)))
    for p in [REPORT/'week7_technical_documentation.md',REPORT/'week8_final_project_summary.md']: assert p.stat().st_size>1000
    from PIL import Image
    for p in VIS.glob('*.png'):
        with Image.open(p) as im: im.verify()
    status={'status':'PASS','checks':['county universe retained','five-character GEOIDs','unscored incomplete rows','score arithmetic and relative mean','MOE missingness explicit','all ACS2024 data GEOIDs matched','state split disjoint','no constructed-score regression','heldout metrics recomputed','nonempty documentation','PNG integrity'],'counties':len(d),'scored':len(good),'moe_unavailable_counties':int(d.any_moe_unavailable.sum())}
    (REPORT/'verification_results.json').write_text(json.dumps(status,indent=2));print(json.dumps(status,indent=2));return status


def inventory():
    import importlib.metadata
    env={'python':platform.python_version(),'platform':platform.platform(),'packages':{p:importlib.metadata.version(p) for p in ['pandas','numpy','matplotlib','requests','plotly','scikit-learn','Pillow']}}
    (REPORT/'run_environment.json').write_text(json.dumps(env,indent=2))
    paths=[]
    for folder in ['scripts','data','reports','visuals','config','recommendations','docs','notebooks']:
        paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.name not in ['final_output_manifest.csv'])
    paths.extend([ROOT/'README.md',ROOT/'requirements.txt',ROOT/'requirements-lock.txt',ROOT/'ARCHIVE.md',ROOT/'pre_audit_2026_10_18.zip'])
    paths.extend(p for p in (ROOT/'tests').glob('*.py'))
    pd.DataFrame([{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)]).to_csv(REPORT/'final_output_manifest.csv',index=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--refresh',action='store_true');parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    if args.verify_only: verify();return
    acquire(args.refresh);df=clean();s=sensitivities(df);m=models(df);a=mapping(df);visuals(df);document(df,m,s,a);verify();inventory();print('AUDITED PIPELINE COMPLETED; see reports/verification_results.json')

if __name__=='__main__': main()
