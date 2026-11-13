"""Read-only evidence reconciliation for visual-only V2-01.1."""
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
OUT=ROOT/'reports/v2-01-1'


def read(name):return json.loads((OUT/name).read_text(encoding='utf-8-sig'))


def browser(name):
    value=(OUT/name).read_text(encoding='utf-8-sig')
    assert '### Error' not in value,name
    return json.loads(value.split('### Result',1)[1].split('### Ran',1)[0].strip())


def main():
    load_dotenv(ROOT/'.env')
    baseline=read('baseline.json')
    assert baseline['raw']==snapshot_raw()
    assert baseline['mart']==snapshot_mart()
    modified=[name for name,sha in baseline['protected'].items() if digest(ROOT/name)!=sha]
    assert not modified,modified
    suite=ET.parse(OUT/'pytest.xml').getroot().find('testsuite')
    tests={key:int(suite.get(key,0)) for key in ('tests','failures','errors','skipped')}
    assert tests=={'tests':103,'failures':0,'errors':0,'skipped':0}
    frontend_log=(OUT/'frontend_tests.log').read_text(encoding='utf-8-sig')
    assert '8 passed' in frontend_log
    build=(OUT/'build.log').read_text(encoding='utf-8-sig')
    assert 'built in' in build and 'error TS' not in build
    ui=browser('browser.log')
    assert not ui['page_errors'] and ui['fixed_reading_matches_p3'] and ui['local_reading_explicit']
    assert ui['complete_months']==22 and ui['all_months']==24 and ui['tooltip_visible']
    assert ui['empty_kpis']==['BRL 0.00','0','0','—'] and ui['reset_restores_baseline']
    for size in ui['sizes']:
        assert not size['horizontalOverflow'] and not size['clippedKpis']
        assert 28<=size['titleSize']<=30 and size['navSize']>=14 and size['bodySize']>=14
        assert size['auxiliarySize']>=12 and size['importantNoteSize']>=13
        assert min(size['chartLabelSizes'])>=12 and size['secondaryContrastOnWhite']>=4.5
    legacy=browser('legacy_browser.log')
    assert legacy['legacy_available'] and not legacy['exceptions']
    with urllib.request.urlopen('http://127.0.0.1:8000/api/overview?start=2017-05-10&end=2017-06-20&state=SP') as response:
        data=json.load(response)
    with (OUT/'filtered-monthly.csv').open(encoding='utf-8-sig',newline='') as handle:
        exported=list(csv.DictReader(handle))
    assert len(exported)==len(data['monthly'])
    for record,actual in zip(exported,data['monthly']):
        assert record['scope_start']=='2017-05-10' and record['scope_end']=='2017-06-20' and record['scope_state']=='SP'
        for field,value in actual.items():assert record[field]==str(value)
    safety=read('public_safety.json');assert safety['passed'] and safety['configured_remote_count']==0
    audit=read('npm_audit.json');assert audit['metadata']['vulnerabilities']['total']==0
    screenshots={p.name:list(Image.open(p).size) for p in (ROOT/'docs/screenshots/v2-01-1').glob('*.png')}
    assert screenshots['overview-1440.png']==[1440,1000] and screenshots['overview-1280.png']==[1280,900]
    value={'passed':True,'protected_files_unchanged':len(baseline['protected']),
        'raw_unchanged':True,'mart_unchanged':True,'api_sql_statistics_unchanged':True,'env_unchanged':True,
        'backend_tests':tests,'frontend_tests_passed':8,'typecheck_and_build_passed':True,
        'browser':ui,'legacy':legacy,'download_matches_api_sql':True,'screenshots':screenshots,
        'safety':safety,'npm_audit_vulnerabilities':0,
        'error_state_scope':'本阶段浏览器拦截模拟503验证展示/恢复；不声称本阶段再次真实停止数据库。V2-01真实停库证据保留。'}
    (OUT/'final_verification.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(value,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
