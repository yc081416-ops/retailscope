"""Statistical boundary tests, independent CI calculations and live P3 evidence checks."""
from decimal import Decimal
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import optimize,stats
from streamlit.testing.v1 import AppTest

from retailscope.diagnostics import (
    ROOT,association_analysis,cluster_bootstrap,concentration_analysis,difference_intervals,
    load_sources,markdown_report,proportion_difference,trend_analysis,wilson_interval,
)
from retailscope.warehouse import query_rows
from retailscope.bi.components import evidence_path,analysis_report_path


@pytest.fixture(scope='module')
def sources():
    return load_sources()


@pytest.fixture(scope='module')
def result():
    return json.loads(evidence_path('reports/p3/analysis.json').read_text(encoding='utf-8'))


def test_live_p3_kpis_equal_p1(sources):
    baseline=json.loads((ROOT/'reports/p1/kpi_overview.json').read_text())[0]
    actual=sources['kpis'].iloc[0]
    assert all(actual[k]==(Decimal(v) if isinstance(v,str) else v) for k,v in baseline.items())
    assert sources['association_orders'].order_id.is_unique


def test_live_sample_counts_and_sql_mean_variance(result,sources):
    independent=query_rows("""SELECT is_late,count(*) AS n,avg(review_mean) AS mean,
        count(*) FILTER(WHERE latest_review_score<=2) AS low
        FROM mart.order_wide WHERE is_eligible AND is_late IS NOT NULL
          AND review_mean IS NOT NULL AND latest_review_score IS NOT NULL AND customer_unique_id IS NOT NULL
        GROUP BY is_late ORDER BY is_late""")
    for actual,expected in zip(result['association']['groups'],independent,strict=True):
        assert actual['n']==expected['n'] and actual['low_scores']==expected['low']
        assert actual['mean_score']==pytest.approx(float(expected['mean']),abs=1e-12)
    a=result['association']
    assert a['valid_orders']+a['excluded_orders']==len(sources['association_orders'])
    assert sum(g['n'] for g in a['groups'])==a['valid_orders']


def test_welch_ci_matches_scipy_direct_order_arrays(result,sources):
    frame=sources['association_orders'].dropna(subset=['is_late','review_mean','latest_review_score','customer_unique_id'])
    a=frame[frame.is_late.eq(True)].review_mean.astype(float).to_numpy()
    b=frame[frame.is_late.eq(False)].review_mean.astype(float).to_numpy()
    expected=stats.ttest_ind(a,b,equal_var=False).confidence_interval(confidence_level=.95)
    actual=difference_intervals(a,b)
    np.testing.assert_allclose(actual['welch_ci'],[expected.low,expected.high],rtol=1e-12)
    np.testing.assert_allclose(result['association']['differences_late_minus_on_time']['welch_ci'],actual['welch_ci'],rtol=1e-12)


@pytest.mark.parametrize('x,n',[(0,40),(10,40),(40,40),(3983,6381)])
def test_wilson_closed_form_matches_score_test_inversion(x,n):
    z=stats.norm.ppf(.975)
    # Independent numerical inversion of binomial score statistic, not the Wilson formula.
    p=x/n
    def score_equation(q):
        return n*(p-q)**2-z*z*q*(1-q)
    lower=0 if x==0 else optimize.brentq(score_equation,0,p-1e-12 if x==n else p)
    upper=1 if x==n else optimize.brentq(score_equation,p+1e-12 if x==0 else p,1)
    np.testing.assert_allclose(wilson_interval(x,n),[lower,upper],atol=1e-11)


def test_newcombe_difference_matches_geometric_construction():
    a,b=wilson_interval(40,100),wilson_interval(10,100)
    expected=[.3-np.sqrt((.4-a[0])**2+(b[1]-.1)**2),.3+np.sqrt((a[1]-.4)**2+(.1-b[0])**2)]
    np.testing.assert_allclose(proportion_difference(40,100,10,100)['newcombe_ci'],expected,atol=1e-14)


def cluster_fixture():
    rows=[]
    for user in range(60):
        for order in range(3):
            score=1+(user+order)%5
            rows.append(dict(order_id=f'{user}_{order}',customer_unique_id=f'u{user:03}',
                is_late=(user+order)%3==0,review_mean=float(score),latest_review_score=score))
    return pd.DataFrame(rows)


def test_cluster_bootstrap_matches_independent_resampled_order_rows():
    frame=cluster_fixture()
    actual=cluster_bootstrap(frame,reps=200,seed=991)
    ids=sorted(frame.customer_unique_id.unique())
    rng=np.random.default_rng(991)
    indexed=frame.set_index('customer_unique_id')
    estimates=[]
    for _ in range(200):
        picked=[ids[i] for i in rng.integers(0,len(ids),size=len(ids))]
        sample=indexed.loc[picked]  # Materialize all orders in every resampled user cluster.
        a,b=sample[sample.is_late],sample[~sample.is_late]
        estimates.append([a.review_mean.mean()-b.review_mean.mean(),a.latest_review_score.le(2).mean()-b.latest_review_score.le(2).mean()])
    expected=np.quantile(estimates,[.025,.975],axis=0)
    np.testing.assert_allclose(actual['mean_ci'],expected[:,0],atol=1e-12)
    np.testing.assert_allclose(actual['low_rate_ci'],expected[:,1],atol=1e-12)
    assert cluster_bootstrap(frame,reps=200,seed=991)==actual


def test_small_missing_and_empty_samples_do_not_claim_inference():
    frame=cluster_fixture().iloc[:3].copy()
    assert cluster_bootstrap(frame,reps=100)['mean_ci'] is None
    assert difference_intervals([1,2],[3])['welch_ci'] is None
    assert proportion_difference(1,2,0,1)['newcombe_ci'] is None
    assert wilson_interval(0,0)==(None,None)
    frame['review_mean']=None
    assert association_analysis(frame,reps=100)['valid_orders']==0
    assert association_analysis(frame.iloc[:0],reps=100)['cluster_bootstrap']['mean_ci'] is None
    assert not concentration_analysis(pd.DataFrame(columns=['category','orders','merchandise']))['available']


def test_partial_sparse_months_and_mad_zero_are_not_anomalies():
    frame=pd.DataFrame(dict(month_start=pd.date_range('2017-01-01',periods=16,freq='MS'),
        orders=[200]*16,merchandise=[Decimal('100')]*16,is_complete=[True]*15+[False]))
    analysis=trend_analysis(frame)
    assert analysis['months'][-1]['mom_merchandise'] is None
    assert analysis['months'][-1]['yoy_merchandise'] is None
    assert all(row['merchandise_flag'] is None for row in analysis['months'])  # MAD=0.
    frame.loc[3,'orders']=10
    changed=trend_analysis(frame)
    assert changed['months'][3]['mom_orders'] is None and changed['months'][4]['mom_orders'] is None
    assert not trend_analysis(frame.iloc[:0])['mad_reference']['merchandise']['available']


def test_live_growth_and_concentration_independent_decimal_checks(result,sources):
    lookup={str(r['month_start']):r for r in sources['monthly'].to_dict('records')}
    for row in result['trend']['months']:
        if not row['complete']:
            assert row['mom_merchandise'] is None and row['yoy_orders'] is None
        for lag,label in ((1,'mom'),(12,'yoy')):
            if row[f'{label}_merchandise'] is not None:
                previous=(pd.Timestamp(row['month'])-pd.DateOffset(months=lag)).date().isoformat()
                baseline=lookup[previous]
                expected=float(Decimal(row['merchandise'])/baseline['merchandise']-1)
                assert row[f'{label}_merchandise']==pytest.approx(expected,abs=1e-14)
                assert baseline['is_complete'] and baseline['orders']>=100
    cat=sources['categories']
    total=sum(cat.merchandise,Decimal(0))
    hhi=sum((value/total)**2 for value in cat.merchandise)
    assert result['concentration']['hhi']==pytest.approx(float(hhi),abs=1e-14)
    assert total==sources['kpis'].iloc[0].merchandise
    assert sum(result['users']['segments'][i]['users'] for i in range(len(result['users']['segments'])))==93358


def test_report_cards_are_computed_traceable_and_equal_export(result):
    assert len(result['findings'])>=5
    assert len({f['id'] for f in result['findings']})==len(result['findings'])
    for finding in result['findings']:
        for key in ('title','result','source_sql','scope','sample','method','limitations','suggestion','statistics'):
            assert finding[key]
        assert set(finding['source_sql'])<=set(result['source_queries'].values())
    assert markdown_report(result)==analysis_report_path().read_text(encoding='utf-8')
    assert str(result['association']['groups'][1]['n']) in markdown_report(result).replace(',','')
    cohort=query_rows("""SELECT sum(active_users) AS active,sum(new_users) AS baseline FROM mart.cohort_retention
        WHERE month_age=1 AND is_observed AND NOT cohort_left_truncated""")[0]
    assert result['users']['m1_active_users_total']==cohort['active']
    assert result['users']['m1_baseline_users_total']==cohort['baseline']


def test_optimized_axes_and_p3_page_export():
    at=AppTest.from_file(str(ROOT/'app/Home.py'),default_timeout=45).run()
    assert not at.exception
    figure=json.loads(at.get('plotly_chart')[0].proto.spec)
    assert figure['layout']['yaxis2']['range'][0]==figure['layout']['yaxis']['range'][0]==0
    at.switch_page('pages/findings.py').run(timeout=45)
    assert not at.exception and not at.error
    assert any(e.label.startswith('F05') for e in at.expander)
    assert at.get('download_button')
