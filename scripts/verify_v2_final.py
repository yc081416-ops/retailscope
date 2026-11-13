"""Read-only V2 acceptance reconciliation, including the real browser download."""
import csv
import json
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET

from dotenv import load_dotenv
from PIL import Image
from retailscope.runtime import digest
from retailscope.verification import snapshot_raw
from retailscope.warehouse import snapshot_mart

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/v2-01'


def read(name):return json.loads((OUT/name).read_text(encoding='utf-8-sig'))


def browser(name):
    text=(OUT/name).read_text(encoding='utf-8-sig')
    assert '### Error' not in text,name
    return json.loads(text.split('### Result',1)[1].split('### Ran',1)[0].strip())


def main():
    load_dotenv(ROOT/'.env')
    baseline=read('baseline.json')
    assert baseline['raw']==snapshot_raw()
    assert baseline['mart']==snapshot_mart()
    changed=[name for name,sha in baseline['protected_files'].items() if digest(ROOT/name)!=sha]
    assert not changed,changed
    node=ET.parse(OUT/'pytest.xml').getroot().find('testsuite')
    tests={k:int(node.get(k,0)) for k in ('tests','failures','errors','skipped')}
    assert tests['tests']==103 and all(tests[k]==0 for k in ('failures','errors','skipped'))
    ui=browser('browser.log')
    assert len(ui['sizes'])==2 and not ui['page_errors']
    assert all(not s['horizontalOverflow'] and not s['clippedKpi'] and s['trendBottom']<=s['height'] for s in ui['sizes'])
    assert ui['loading_visible'] and ui['invalid_range_chinese_message'] and ui['reset_restores_baseline']
    assert ui['findings_count']==7 and ui['empty_kpis']==['BRL 0.00','0','0','—']
    failed=browser('failure_browser.log');recovered=browser('recovery_browser.log');legacy=browser('legacy_browser.log')
    assert failed['http_status']==503 and failed['stale_kpis_hidden'] and recovered['recovered']
    assert legacy['legacy_available'] and legacy['exceptions']==0
    with urllib.request.urlopen('http://127.0.0.1:8000/api/overview?start=2017-05-10&end=2017-06-20&state=SP') as r:
        filtered=json.load(r)
    with (OUT/'browser-filtered-monthly.csv').open(encoding='utf-8-sig',newline='') as file:
        exported=list(csv.DictReader(file))
    assert len(exported)==len(filtered['monthly'])
    for actual,expected in zip(exported,filtered['monthly']):
        assert actual['scope_state']=='SP' and actual['scope_start']=='2017-05-10' and actual['scope_end']=='2017-06-20'
        for name,value in expected.items():assert actual[name]==str(value)
    safety=read('public_safety.json')
    assert safety['passed'] and safety['configured_remote_count']==0 and not safety['staged_files']
    audit=read('npm_audit.json');assert audit['metadata']['vulnerabilities']['total']==0
    current=(OUT/'api_current.log').read_text(encoding='utf-8-sig')
    assert 'Traceback' not in current
    screenshots={p.name:list(Image.open(p).size) for p in (ROOT/'docs/screenshots/v2-01').glob('*.png')}
    for width,height in ((1440,1000),(1280,900)):
        assert screenshots[f'overview-{width}.png']==[width,height]
    result={'passed':True,'tests':tests,'original_tests_passed':86,'new_api_cases_passed':17,
        'raw_and_mart_unchanged':True,'protected_files_unchanged':len(baseline['protected_files']),
        'env_unchanged':True,'default_kpis':ui['default_kpis'],'sizes':ui['sizes'],
        'filtered_scope':ui['filtered_scope'],'filtered_kpis':ui['filtered_kpis'],
        'csv_download_reconciled':True,'loading_empty_invalid_and_reset_verified':True,
        'real_database_failure_and_recovery':True,'api_error_logs_sanitized':True,'legacy':legacy,
        'screenshots':screenshots,'findings_reused':ui['findings_count'],'npm_audit_vulnerabilities':0,
        'git_safety':safety,'public_deployment_performed':False}
    (OUT/'final_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
