"""Final read-only reconciliation of six-page evidence and protected accepted artifacts."""
import hashlib
import json
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET

from dotenv import load_dotenv
from PIL import Image
from retailscope.runtime import digest
from retailscope.verification import snapshot_raw
from retailscope.warehouse import snapshot_mart
from retailscope.bi.components import analysis_report_path,evidence_path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/v2-03'


def read(name):return json.loads((OUT/name).read_text(encoding='utf-8-sig'))


def browser(name):
    value=(OUT/name).read_text(encoding='utf-8-sig')
    assert '### Error' not in value,name
    return json.loads(value.split('### Result',1)[1].split('### Ran',1)[0].strip())


def main():
    load_dotenv(ROOT/'.env')
    baseline=read('baseline.json')
    assert baseline['raw']==snapshot_raw() and baseline['mart']==snapshot_mart()
    changed=[name for name,sha in baseline['protected'].items() if digest(ROOT/name)!=sha]
    assert not changed,changed
    artifacts=read('accepted_artifact_check.json')
    assert not artifacts['changed'] and artifacts['p3_analysis_matches_accepted_sha']
    # Recheck inherited P0 accepted hashes, not merely this phase's start state.
    p1=json.loads((ROOT/'reports/p1/run.json').read_text(encoding='utf-8'))
    for name in artifacts['checked']:assert digest(ROOT/name)==p1['p0_file_sha256'][name]
    suite=ET.parse(OUT/'pytest.xml').getroot().find('testsuite')
    tests={key:int(suite.get(key,0)) for key in ('tests','failures','errors','skipped')}
    assert tests=={'tests':143,'failures':0,'errors':0,'skipped':0}
    assert '20 passed' in (OUT/'frontend_tests.log').read_text(encoding='utf-8-sig')
    assert 'built in' in (OUT/'build.log').read_text(encoding='utf-8-sig')
    ui=browser('browser.log')
    assert len(ui['navigation'])==6 and all(r['loaded'] for r in ui['navigation'])
    assert len(ui['screens'])==4 and all(not r['horizontalOverflow'] and r['titleFont']==29 and r['navFont']==14 for r in ui['screens'])
    assert all(ui[key] for key in ['history_verified','seven_results_match','topic_filter_and_details','audit_time_honest','nine_tables','missing_field_filter','quality_empty_filter_verified','quality_partial_live_failure','legacy_entry_migrated','findings_empty_verified','findings_error_verified','quality_error_verified','findings_loading_verified','quality_loading_verified'])
    assert not ui['page_errors']
    assert not any('/'+name+'-' in url for name in ('FindingsPage','Quality') for url in ui['home_assets'])
    payload=(OUT/'downloaded_report.md').read_bytes()
    assert payload==analysis_report_path().read_bytes()
    quality=read('downloaded_quality.json')
    assert quality['live']['status']=='available' and len(quality['live']['raw_counts'])==9
    assert sum(r['rows'] for r in quality['live']['raw_counts'])==1550922
    audit=json.loads((ROOT/'reports/raw_quality.json').read_text(encoding='utf-8'))
    assert {r['table']:r['audit_rows'] for r in quality['historical']['tables']}=={r['table']:r['row_count'] for r in audit['tables']}
    assert quality['historical']['source']['executed_at'] is None
    assert quality['historical']['source']['file_saved_at'] and quality['analysis_snapshot']['report_matches']
    assert quality['tests']['latest']['stage']=='V2-03' and quality['tests']['latest']['tests']==143
    with urllib.request.urlopen('http://127.0.0.1:8000/api/evidence/findings',timeout=20) as response:data=json.load(response)
    p3=json.loads(evidence_path('reports/p3/analysis.json').read_text(encoding='utf-8'))
    assert data['findings']==p3['findings']
    manifest=json.loads((ROOT/'frontend/dist/.vite/manifest.json').read_text(encoding='utf-8'))
    chunks={}
    for name in ('FindingsPage','Quality'):
        record=manifest[f'src/pages/{name}.tsx'];assert record['isDynamicEntry']
        chunks[name]={'file':record['file'],'bytes':(ROOT/'frontend/dist'/record['file']).stat().st_size}
    screenshots={p.name:list(Image.open(p).size) for p in (ROOT/'docs/screenshots/v2-03').glob('*.png')}
    for name in ('findings','quality'):
        assert screenshots[f'{name}-1440.png']==[1440,1000] and screenshots[f'{name}-1280.png']==[1280,900]
    assert len(screenshots)==10
    safety=read('public_safety.json');assert safety['passed'] and not safety['configured_remote_count']
    assert read('npm_audit.json')['metadata']['vulnerabilities']['total']==0
    result={'passed':True,'backend_tests':tests,'original_backend_cases':129,'new_backend_cases':14,
        'frontend_passed':20,'original_frontend_cases':13,'new_frontend_cases':7,
        'protected_files_unchanged':len(baseline['protected']),'four_existing_pages_and_frozen_css_unchanged':True,
        'raw_mart_models_and_env_unchanged':True,'accepted_p0_artifact_files_unchanged':len(artifacts['checked']),
        'p3_analysis_matches_accepted_sha':True,'browser':ui,
        'report_download_sha256':hashlib.sha256(payload).hexdigest(),'report_download_exact_bytes':True,
        'quality_download_rows':sum(r['rows'] for r in quality['live']['raw_counts']),
        'p0_missing_execution_time_preserved':True,'page_chunks':chunks,'screenshots':screenshots,'safety':safety,
        'edge_state_scope':'质量缺失字段空结果为真实历史快照筛选；发现空数组、API503和当前DB不可用局部态为浏览器拦截测试。未执行停库、重建或全量质量审计。'}
    (OUT/'final_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
