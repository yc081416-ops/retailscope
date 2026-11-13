"""Read-only P3 and quality evidence contracts, including provenance and safe degradation."""
import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text

from api import main,evidence
from retailscope.bi.components import evidence_path,analysis_report_path
from retailscope.contracts import SOURCES

@pytest.fixture(scope='module')
def client():
    with TestClient(main.app,raise_server_exceptions=False) as value:yield value


def test_all_seven_findings_equal_accepted_p3(client):
    response=client.get('/api/evidence/findings');assert response.status_code==200
    actual=response.json();expected=json.loads(evidence_path('reports/p3/analysis.json').read_text(encoding='utf-8'))
    assert actual['findings']==expected['findings']
    assert actual['context']==expected['context'] and actual['source']['executed_at']==expected['generated_at']
    assert actual['report']['matches_snapshot'] and actual['read_only']
    assert actual['source']['kind']=='P3_fixed_snapshot'
    assert actual['source']['sha256']==hashlib.sha256(evidence_path('reports/p3/analysis.json').read_bytes()).hexdigest()


def test_markdown_download_is_exact_file_bytes(client):
    response=client.get('/api/evidence/findings/report')
    assert response.status_code==200 and response.content==analysis_report_path().read_bytes()
    assert response.headers['content-disposition'].startswith('attachment;')
    assert 'text/markdown' in response.headers['content-type']


def test_live_counts_and_catalog_reconcile_real_database(client):
    data=client.get('/api/evidence/quality').json();live=data['live']
    assert live['status']=='available' and live['kind']=='live_database_read_only' and live['as_of']
    expected={}
    with main.database().connect() as conn:
        assert conn.execute(text('SHOW transaction_read_only')).scalar()=='on'
        for source in SOURCES:
            expected[source.table_name]=conn.execute(text(f'SELECT count(*) FROM raw.{source.table_name}')).scalar()
    assert {r['table_name']:r['rows'] for r in live['raw_counts']}==expected
    assert len(expected)==9 and sum(expected.values())==1550922
    assert {r['schema'] for r in live['objects']}=={'raw','core','mart'}
    assert any(r['type']=='PRIMARY KEY' and r['schema']=='mart' for r in live['constraints'])


def test_p0_audit_missingness_duplicates_and_time_are_historical(client):
    result=client.get('/api/evidence/quality').json()['historical']
    audit=json.loads(Path('reports/raw_quality.json').read_text(encoding='utf-8'))
    assert result['source']['kind']=='P0_historical_audit'
    assert result['source']['executed_at'] is None and not result['source']['execution_time_recorded']
    assert result['source']['file_saved_at'] and result['has_blocking_issues'] is False
    for row in result['tables']:
        original=next(r for r in audit['tables'] if r['table']==row['table'])
        assert row['full_duplicate_rows']==original['duplicate_full_rows']
        if not row['logical_key']:assert row['key_duplicates'] is None
        for missing in (r for r in result['missing'] if r['table']==row['table']):
            count=original['missing_by_column'].get(missing['column'],0)
            assert missing['missing_rows']==count
            assert missing['missing_rate']==pytest.approx(count/original['row_count'])
    assert {r['check']:r['rows'] for r in result['relations']}==audit['relational_quality']['checks']


def test_p1_p3_status_and_reconciliation_are_provenanced_records(client):
    result=client.get('/api/evidence/quality').json()
    expected=json.loads(Path('reports/p1/pandas_reconciliation.json').read_text(encoding='utf-8'))
    assert result['reconciliation']['checks']==expected['checks']
    assert result['warehouse']['source']['kind']=='P1_build_record' and result['warehouse']['source']['executed_at']
    assert result['analysis_snapshot']['available'] and result['analysis_snapshot']['report_matches']
    assert result['analysis_snapshot']['findings']==7
    assert result['dataset']['version']=='2' and result['dataset']['source']['kind']=='P0_download_record'


@pytest.mark.parametrize('section',['all','historical','tests'])
def test_quality_download_is_bounded_aggregate_projection(client,section):
    response=client.get('/api/evidence/quality/export',params={'section':section})
    assert response.status_code==200 and response.headers['content-disposition'].startswith('attachment;')
    data=response.json();assert data['read_at']
    if section=='all':
        assert data['live']['raw_counts'] and 'database' not in data['runtime']
    else:assert list(data)==['read_at',section]
    assert 'DATABASE_URL' not in response.text and 'POSTGRES_PASSWORD' not in response.text


def test_paths_and_export_sections_cannot_read_credentials(client,tmp_path):
    with pytest.raises(ValueError):evidence.safe_path(tmp_path/'outside.md')
    assert client.get('/api/evidence/quality/export',params={'section':'../../.env'}).status_code==422
    assert client.get('/api/evidence/findings/report',params={'path':'.env'}).content==analysis_report_path().read_bytes()


def test_live_database_failure_keeps_history_without_fake_live_success(client,monkeypatch,caplog):
    def failed():raise RuntimeError('postgresql://private:secret@local/db')
    monkeypatch.setattr(evidence,'database',failed)
    response=client.get('/api/evidence/quality');assert response.status_code==200
    data=response.json();assert data['live']['status']=='unavailable' and data['live']['raw_counts']==[]
    assert len(data['historical']['tables'])==9
    assert 'secret' not in response.text and 'secret' not in caplog.text


def test_missing_evidence_is_not_treated_as_passing_history(client,monkeypatch,tmp_path):
    monkeypatch.setattr(evidence,'ROOT',tmp_path)
    response=client.get('/api/evidence/quality');assert response.status_code==200
    data=response.json()
    assert data['historical']['tables']==[] and data['historical']['has_blocking_issues'] is None
    assert data['warehouse']['status'] is None and data['reconciliation']['passed'] is None
    assert not data['analysis_snapshot']['available'] and data['tests']['latest'] is None
    assert data['live']['raw_counts']


def test_mismatched_report_is_blocked_without_disclosing_content(client,monkeypatch,tmp_path):
    (tmp_path/'reports').mkdir();(tmp_path/'docs').mkdir()
    snapshot=tmp_path/'reports/analysis.json';snapshot.write_bytes(evidence_path('reports/p3/analysis.json').read_bytes())
    report=tmp_path/'docs/report.md';report.write_text('private:secret mismatched report',encoding='utf-8')
    monkeypatch.setattr(evidence,'ROOT',tmp_path)
    monkeypatch.setattr(evidence,'evidence_path',lambda _:snapshot)
    monkeypatch.setattr(evidence,'analysis_report_path',lambda:report)
    response=client.get('/api/evidence/findings/report')
    assert response.status_code==503 and 'secret' not in response.text


def test_test_history_rejects_incomplete_or_inconsistent_xml(monkeypatch,tmp_path):
    good=tmp_path/'good.xml';good.write_text('<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0" timestamp="2026-11-13T01:00:00"><testcase name="ok"/></testsuite></testsuites>')
    bad=tmp_path/'bad.xml';bad.write_text('<testsuites><testsuite tests="2"><testcase name="not_complete"/></testsuite></testsuites>')
    broken=tmp_path/'broken.xml';broken.write_text('<testsuites>')
    monkeypatch.setattr(evidence,'ROOT',tmp_path)
    monkeypatch.setattr(evidence,'TEST_FILES',[('good','good.xml'),('bad','bad.xml'),('broken','broken.xml')])
    result=evidence.test_history()
    assert len(result['history'])==1 and result['latest']['stage']=='good'
    assert result['latest']['tests']==result['latest']['passed']==1


def test_page_read_does_not_call_audit_rebuild_or_runtime_verification(client,monkeypatch):
    from retailscope import audit,warehouse,runtime
    def forbidden(*args,**kwargs):raise AssertionError('Expensive rebuild/audit called')
    monkeypatch.setattr(audit,'audit_all',forbidden)
    monkeypatch.setattr(warehouse,'build_warehouse',forbidden)
    monkeypatch.setattr(runtime,'readiness',forbidden)
    assert client.get('/api/evidence/quality').status_code==200
