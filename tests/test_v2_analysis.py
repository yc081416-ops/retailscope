"""V2-02 interfaces reconcile real accepted rows and independent order/item SQL."""
import csv
from decimal import Decimal
from io import StringIO
import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text
from api import main,analysis

@pytest.fixture(scope='module')
def client():
    with TestClient(main.app,raise_server_exceptions=False) as conn:yield conn


def test_users_equal_every_accepted_p1_row(client):
    response=client.get('/api/analysis/users');assert response.status_code==200
    data=response.json()
    files={'segments':'rfm_segments','frequency':'repurchase_distribution','summary':'repurchase_summary','cohort':'cohort_retention','new_users':'cohort_sizes'}
    for key,name in files.items():
        expected=json.loads(Path('reports/p1',name+'.json').read_text(encoding='utf-8'))
        assert sorted(data[key],key=lambda r:json.dumps(r,sort_keys=True))==sorted(expected,key=lambda r:json.dumps(r,sort_keys=True))
    assert len(data['segments'])==6
    assert sum(row['retention'] is None for row in data['cohort'])==298
    assert sum(r['users'] for r in data['segments'])==93358
    assert data['metadata']['context']['rfm_reference_date']=='2018-08-30'
    assert data['scope']['mode']=='fixed'


@pytest.mark.parametrize('scope',[{'start':'2017-01-01'},{'state':'SP'},{'category':'beleza_saude'}])
def test_fixed_users_reject_local_filters(client,scope):
    assert client.get('/api/analysis/users',params=scope).status_code==422


def test_products_defaults_and_cross_category_order_dedup(client):
    result=client.get('/api/analysis/products').json()
    kpi=result['kpis'][0]
    assert kpi['orders']==96478 and kpi['items']==110197
    assert Decimal(kpi['merchandise'])==Decimal('13221498.11')
    assert sum(r['orders'] for r in result['categories'])>kpi['orders']
    assert sum(Decimal(r['merchandise']) for r in result['categories'])==Decimal(kpi['merchandise'])


@pytest.mark.parametrize('page',['products','delivery'])
@pytest.mark.parametrize('scope',[{'start':'2017-05-10','end':'2017-06-20','state':'SP','category':'beleza_saude'},
    {'start':'2018-01-01','end':'2018-01-01','state':'RJ'},{'category':'__unknown__'}])
def test_scopes_reconcile_independent_sql(client,page,scope):
    response=client.get('/api/analysis/'+page,params=scope);assert response.status_code==200
    result=response.json();params=result['scope']
    with main.database().connect() as conn:
        base="""WITH chosen AS (SELECT o.order_id,i.price,i.freight FROM mart.order_wide o
            JOIN mart.order_item_fact i USING(order_id) JOIN mart.dim_product p USING(product_id)
            WHERE o.is_eligible AND o.purchased_at>=CAST(:start AS date)
              AND o.purchased_at<CAST(:end AS date)+interval '1 day'
              AND (CAST(:state AS text) IS NULL OR o.customer_state=:state)
              AND (CAST(:category AS text) IS NULL OR p.category=:category)) """
        expected=conn.execute(text(base+"SELECT count(DISTINCT order_id) AS orders,count(*) AS items,coalesce(sum(price),0) AS amount FROM chosen"),params).mappings().one()
    kpi=result['kpis'][0]
    assert kpi['orders']==expected['orders']
    if page=='products':
        assert kpi['items']==expected['items']
        assert Decimal(kpi['merchandise'])==expected['amount']
        assert sum(Decimal(r['merchandise']) for r in result['monthly'])==expected['amount']
    else:
        assert sum(r['orders'] for r in result['histogram'])==kpi['delivery_n']
        for row in result['association']:
            assert row['low_score_n']<=row['orders']
            assert abs(Decimal(row['low_score_rate'])-Decimal(row['low_score_orders'])/row['low_score_n'])<Decimal('1e-18')


def test_delivery_defaults_and_p3_sample_agreement(client):
    result=client.get('/api/analysis/delivery').json();kpi=result['kpis'][0]
    assert round(Decimal(kpi['delivery_days']),2)==Decimal('12.56')
    assert round(100*Decimal(kpi['late_rate']),4)==Decimal('6.7731')
    assert round(Decimal(kpi['review_mean']),2)==Decimal('4.16')
    assert kpi['delivery_n']==kpi['late_n']==96470 and kpi['reviewed_orders']==95832
    groups=result['association'];assert sum(g['orders'] for g in groups)==95824
    assert sum(g['low_score_orders'] for g in groups)==12272
    assert {g['delivery_group']:g['orders'] for g in groups}=={'逾期':6381,'未逾期':89443}


@pytest.mark.parametrize('page,table',[('users','segments'),('users','cohort'),('users','summary'),('products','kpis'),('products','categories'),('products','monthly'),('delivery','association'),('delivery','regions'),('delivery','histogram'),('delivery','reviews'),('delivery','kpis')])
def test_each_analysis_export_reconciles(client,page,table):
    scope={} if page=='users' else {'start':'2017-05-10','end':'2017-06-20','state':'SP','category':'beleza_saude'}
    data=client.get('/api/analysis/'+page,params=scope).json()
    response=client.get('/api/analysis/'+page+'/export',params={**scope,'table':table})
    assert response.status_code==200 and response.content.startswith(b'\xef\xbb\xbf')
    exported=list(csv.DictReader(StringIO(response.content.decode('utf-8-sig'))))
    assert len(exported)==len(data[table])
    for row,original in zip(exported,data[table]):
        assert row['scope_mode']==data['scope']['mode']
        for key,value in original.items():assert row[key]==('' if value is None else str(value))
    if table=='cohort':assert sum(row['retention']=='' for row in exported)==298


@pytest.mark.parametrize('page',['products','delivery'])
def test_empty_and_invalid_combinations(client,page):
    response=client.get('/api/analysis/'+page,params={'start':'2020-01-01','end':'2020-01-02'})
    assert response.status_code==200 and response.json()['kpis'][0]['orders']==0
    export=client.get('/api/analysis/'+page+'/export',params={'start':'2020-01-01','end':'2020-01-02','table':'categories' if page=='products' else 'association'})
    assert export.status_code==200 and len(export.text.splitlines())==1
    assert client.get('/api/analysis/'+page,params={'category':"' OR true--"}).status_code==422
    assert client.get('/api/analysis/'+page+'/export',params={'table':'arbitrary_sql'}).status_code==422


def test_analysis_read_only_and_sanitized_failure(client,monkeypatch,caplog):
    with main.database().connect() as conn:
        assert conn.execute(text('SHOW transaction_read_only')).scalar()=='on'
    def failed():raise RuntimeError('postgresql://private:secret@local/db')
    monkeypatch.setattr(analysis,'database',failed)
    for page in ('users','products','delivery'):
        response=client.get('/api/analysis/'+page)
        assert response.status_code==503 and 'secret' not in response.text
    assert 'secret' not in caplog.text
