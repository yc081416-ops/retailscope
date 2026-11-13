"""V2 live database contract and independent filtered reconciliation, without altering raw/mart."""
from retailscope.bi.components import evidence_path
from decimal import Decimal
from io import StringIO
import csv
import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text
from api import main

@pytest.fixture(scope='module')
def client():
    with TestClient(main.app,raise_server_exceptions=False) as value:yield value


def test_v2_defaults_equal_p1(client):
    response=client.get('/api/overview')
    assert response.status_code==200
    data=response.json()
    assert data['kpis']['orders']==96478 and data['kpis']['users']==93358
    assert Decimal(data['kpis']['merchandise'])==Decimal('13221498.11')
    assert round(Decimal(data['kpis']['average_order_value']),2)==Decimal('137.04')
    assert sum(r['orders'] for r in data['statuses'])==99441
    assert sum(Decimal(r['merchandise']) for r in data['monthly'])==Decimal(data['kpis']['merchandise'])
    assert sum(r['orders'] for r in data['regions'])==data['kpis']['orders']
    assert any(not r['is_complete'] for r in data['monthly'])
    assert data['metadata']['read_only']


@pytest.mark.parametrize('scope',[{'start':'2017-05-10','end':'2017-06-20','state':'SP'},
    {'start':'2018-01-01','end':'2018-01-01','state':'RJ'},{'state':'AC'}])
def test_v2_filters_reconcile_independently(client,scope):
    data=client.get('/api/overview',params=scope).json()
    params={**data['scope']}
    with main.database().connect() as conn:
        actual=conn.execute(text("""SELECT count(*) AS orders,count(DISTINCT customer_unique_id) AS users,
            coalesce(sum(merchandise),0) AS amount FROM mart.order_wide
            WHERE is_eligible AND purchased_at>=CAST(:start AS date)
              AND purchased_at<CAST(:end AS date)+interval '1 day'
              AND customer_state=:state"""),params).mappings().one()
    assert data['kpis']['orders']==actual['orders']
    assert data['kpis']['users']==actual['users']
    assert Decimal(data['kpis']['merchandise'])==actual['amount']
    assert sum(r['orders'] for r in data['monthly'])==actual['orders']
    assert sum(r['orders'] for r in data['regions'])==actual['orders']
    assert all(r['state']==scope['state'] for r in data['regions'])
    assert sum(Decimal(r['merchandise']) for r in data['regions'])==actual['amount']


@pytest.mark.parametrize('table',['kpis','monthly','statuses','regions'])
def test_v2_export_matches_applied_filter(client,table):
    scope={'start':'2017-01-01','end':'2017-02-28','state':'SP'}
    data=client.get('/api/overview',params=scope).json()
    response=client.get('/api/overview/export',params={**scope,'table':table})
    assert response.status_code==200 and response.content.startswith(b'\xef\xbb\xbf')
    exported=list(csv.DictReader(StringIO(response.content.decode('utf-8-sig'))))
    expected=[data[table]] if table=='kpis' else data[table]
    assert len(exported)==len(expected)
    for row,source in zip(exported,expected):
        assert row['scope_state']=='SP' and row['scope_start']==scope['start'] and row['scope_end']==scope['end']
        for key,value in source.items():assert row[key]==('' if value is None else str(value))


@pytest.mark.parametrize('scope',[{'start':'2018-02-01','end':'2017-01-01'},{'state':'XX'},
    {'state':"SP' OR true--"},{'end':'9999-12-31'},{'start':'invalid'}])
def test_v2_invalid_filters_rejected(client,scope):
    assert client.get('/api/overview',params=scope).status_code==422


def test_v2_empty_and_partial_window(client):
    data=client.get('/api/overview',params={'start':'2020-01-01','end':'2020-01-02'}).json()
    assert data['kpis']['orders']==0 and data['kpis']['average_order_value'] is None
    assert data['monthly']==data['regions']==data['statuses']==[]
    partial=client.get('/api/overview',params={'start':'2017-01-02','end':'2017-02-28'}).json()
    assert not partial['monthly'][0]['is_complete'] and partial['monthly'][1]['is_complete']


def test_v2_connection_is_read_only():
    with main.database().connect() as conn:
        assert conn.execute(text('SHOW transaction_read_only')).scalar()=='on'
        assert conn.execute(text('SHOW transaction_isolation')).scalar()=='repeatable read'


def test_v2_database_failure_is_sanitized(client,monkeypatch,caplog):
    def failed():raise RuntimeError('postgresql://private:secret@host/database')
    monkeypatch.setattr(main,'database',failed)
    response=client.get('/api/overview')
    assert response.status_code==503 and response.json()['code']=='DATA_UNAVAILABLE'
    assert 'secret' not in response.text and 'postgresql' not in response.text
    assert 'secret' not in caplog.text and 'postgresql://' not in caplog.text


def test_v2_findings_reuse_accepted_results(client):
    result=client.get('/api/findings').json()
    expected=json.loads(evidence_path('reports/p3/analysis.json').read_text(encoding='utf-8'))
    assert len(result['findings'])==7 and result['findings']==expected['findings']
    assert '不随' in result['scope']
