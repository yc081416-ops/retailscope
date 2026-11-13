"""P4 safe startup, stale snapshot detection and presentation-unit regressions."""
import json
import os
from pathlib import Path
import subprocess
import sys

from dotenv import dotenv_values
import pytest
from streamlit.testing.v1 import AppTest

from retailscope import runtime
from retailscope.bi import components
from retailscope.diagnostics import ROOT


def test_existing_evidence_is_never_overwritten(tmp_path):
    path=tmp_path/'accepted.json'
    assert runtime.save_if_absent({'value':'accepted'},path)
    before=path.read_bytes()
    assert not runtime.save_if_absent({'value':'replacement'},path)
    assert path.read_bytes()==before


def test_real_startup_env_generator_is_parseable_and_repeat_safe(tmp_path):
    script=(ROOT/'start.ps1').read_text(encoding='utf-8')
    python=script.split("    @'\n",1)[1].split("\n'@ |",1)[0]
    first=subprocess.run([sys.executable,'-c',python],cwd=tmp_path,capture_output=True,text=True)
    assert first.returncode==0,first.stderr
    config=dotenv_values(tmp_path/'.env')
    assert len(config)==4 and len(config['POSTGRES_PASSWORD'])==48
    assert config['POSTGRES_PASSWORD'] not in first.stdout
    before=(tmp_path/'.env').read_bytes()
    assert subprocess.run([sys.executable,'-c',python],cwd=tmp_path,capture_output=True).returncode==0
    assert (tmp_path/'.env').read_bytes()==before


def test_snapshot_staleness_detects_changed_sql_and_data(monkeypatch):
    accepted=json.loads(components.evidence_path('reports/p3/analysis.json').read_text(encoding='utf-8'))
    monkeypatch.setattr(runtime,'input_hashes',lambda:accepted['input_csv_sha256'])
    runtime.validate_analysis(accepted)
    changed=json.loads(json.dumps(accepted))
    changed['sql_sha256']['monthly']='changed'
    with pytest.raises(RuntimeError,match='过期'):
        runtime.validate_analysis(changed)
    monkeypatch.setattr(runtime,'input_hashes',lambda:{'changed':'data'})
    with pytest.raises(RuntimeError,match='过期'):
        runtime.validate_analysis(accepted)


def test_partial_database_is_not_reported_as_ready(monkeypatch,tmp_path):
    monkeypatch.setattr(runtime,'db_status',lambda:{'server':'PostgreSQL 16.16'})
    monkeypatch.setattr(runtime,'raw_state',lambda:{'orders':1,'customers':None})
    with pytest.raises(RuntimeError,match='初始化'):
        runtime.readiness(tmp_path,tmp_path)


def test_pointer_cannot_read_outside_reports(monkeypatch,tmp_path):
    monkeypatch.setattr(components,'ROOT',tmp_path)
    folder=tmp_path/'reports/runtime'
    folder.mkdir(parents=True)
    outside=tmp_path/'private.json'
    outside.write_text('{}')
    (folder/'active.json').write_text(json.dumps({'analysis':'private.json','report':'private.json'}))
    assert components.evidence_path('reports/p3/analysis.json')==tmp_path/'reports/p3/analysis.json'
    assert components.analysis_report_path()==tmp_path/'docs/P3_BUSINESS_REPORT.md'


def test_low_score_units_are_orders_not_people():
    at=AppTest.from_file(str(ROOT/'app/Home.py'),default_timeout=45).run()
    at.switch_page('pages/findings.py').run(timeout=45)
    assert not at.exception
    groups=next(frame.value for frame in at.dataframe if '低评分订单数（单）' in frame.value.columns)
    assert int(groups['订单数（单）'].sum())==95824
    assert int(groups['低评分订单数（单）'].sum())==12272
    assert '去重用户数（人）' in groups


def test_powershell_startup_parses_without_errors():
    command="$tokens=$null; $parseErrors=$null; [System.Management.Automation.Language.Parser]::ParseFile('start.ps1',[ref]$tokens,[ref]$parseErrors) | Out-Null; if ($parseErrors.Count) { exit 1 }"
    result=subprocess.run(['powershell.exe','-NoProfile','-Command',command],cwd=ROOT,capture_output=True)
    assert result.returncode==0,result.stderr.decode(errors='replace')


def test_isolated_service_uses_its_own_generated_snapshot(monkeypatch,tmp_path):
    monkeypatch.setattr(components,'ROOT',tmp_path)
    run=tmp_path/'reports/repro/runs/test'
    (run/'p3').mkdir(parents=True)
    analysis=run/'p3/analysis.json'
    analysis.write_text('{}')
    manifest=tmp_path/'reports/repro/manifest.json'
    manifest.write_text(json.dumps({'analysis_path':str(analysis)}))
    monkeypatch.setenv('RETAILSCOPE_RUNTIME_MANIFEST',str(manifest))
    assert components.evidence_path('reports/p3/analysis.json')==analysis
    assert components.analysis_report_path()==run/'P3_BUSINESS_REPORT.md'
