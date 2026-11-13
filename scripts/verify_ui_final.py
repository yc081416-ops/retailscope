"""Read-only reconciliation of final UI, unchanged data and original export fields."""
import csv
import hashlib
import json
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
from retailscope.bi.components import analysis_report_path
from retailscope.verification import snapshot_raw
from retailscope.warehouse import snapshot_mart

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/ui-final'
FIXES=ROOT/'reports/ui-final-fixes'


def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))


def get(path):
    with urllib.request.urlopen('http://127.0.0.1:8000/api/'+path,timeout=45) as response:return json.load(response)


def main():
    load_dotenv(ROOT/'.env')
    baseline=read(OUT/'baseline.json')
    for name,sha in baseline['protected'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
    for endpoint,data in baseline['api'].items():assert get(endpoint)==data,endpoint
    accepted=read(ROOT/'reports/v2-04/baseline.json')
    for name,sha in accepted['protected'].items():
        if name.startswith('docs'):
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
    assert snapshot_raw()==accepted['raw'] and snapshot_mart()==accepted['mart']
    p1=read(ROOT/'reports/p1/run.json')
    files=read(ROOT/'reports/v2-03/accepted_artifact_check.json')['checked']
    for name in files:assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==p1['p0_file_sha256'][name]
    log=(OUT/'browser.log').read_text(encoding='utf-8-sig');assert '### Error' not in log
    ui=json.loads(log.split('### Result',1)[1].split('### Ran',1)[0].strip())
    assert 'pages' not in ui,'Deprecated screenshot placeholder must not reappear in interaction records'
    assert len(ui['visited_routes'])==6 and all(r['loaded'] for r in ui['visited_routes'])
    assert {r['path'] for r in ui['visited_routes']}=={'/','/users','/products','/delivery','/findings','/quality'}
    assert not ui['page_errors'] and ui['navigation'] and ui['loading_error_recovery']
    assert all('F0'+str(i) in ui['evidence_preserved'] for i in range(1,8))
    screen_results={}
    state_results={}
    for zoom in ['100','125']:
        value=(OUT/f'screens_{zoom}.log').read_text(encoding='utf-8-sig');assert '### Error' not in value
        screens=json.loads(value.split('### Result',1)[1].split('### Ran',1)[0].strip())
        assert len(screens['pages'])==12 and all(not p['horizontalOverflow'] and not p['clippedKpis'] for p in screens['pages'])
        assert all(abs(p['dpr']-(1.25 if zoom=='125' else 1))<.001 for p in screens['pages'])
        screen_results[zoom]=screens
        value=(OUT/f'states_{zoom}.log').read_text(encoding='utf-8-sig');assert '### Error' not in value
        states=json.loads(value.split('### Result',1)[1].split('### Ran',1)[0].strip());assert len(states['checks'])==12
        state_results[zoom]=states
    extra_log=(OUT/'details.log').read_text(encoding='utf-8-sig');assert '### Error' not in extra_log
    extra=json.loads(extra_log.split('### Result',1)[1].split('### Ran',1)[0].strip())
    assert extra['keyboard_and_tooltips']
    assert ui['overview_draft_and_reset'] and len(ui['filters'])==2 and len(set(ui['downloads']+extra['downloads']))==9
    export_columns={}
    for filename,endpoint,table in [('users-cohort.csv','analysis/users','cohort'),('users-rfm.csv','analysis/users','segments'),('products-all.csv','analysis/products','categories'),('delivery-all.csv','analysis/delivery','association'),
        ('products-filtered.csv','analysis/products?start=2017-05-10&end=2017-06-20&state=SP&category=beleza_saude','categories'),
        ('delivery-filtered.csv','analysis/delivery?start=2017-05-10&end=2017-06-20&state=SP&category=beleza_saude','association'),
        ('overview-filtered.csv','overview?start=2017-05-10&end=2017-06-20&state=SP','monthly')]:
        with (OUT/filename).open(encoding='utf-8-sig',newline='') as f:actual=list(csv.DictReader(f))
        payload=get(endpoint);expected=payload[table];assert len(actual)==len(expected)
        export_columns[filename]=list(actual[0])
        for row,source in zip(actual,expected):
            for key,value in source.items():assert row[key]==('' if value is None else str(value)),(filename,key)
            for key,value in payload['scope'].items():
                column='scope_'+key
                if column in row:assert row[column]==str(value or 'ALL'),(filename,column)
        if filename=='products-all.csv':
            assert len(actual)==74 and sum(Decimal(r['merchandise']) for r in actual)==Decimal('13221498.11')
    assert (OUT/'report.md').read_bytes()==analysis_report_path().read_bytes()
    quality=read(OUT/'quality.json')
    assert len(quality['live']['raw_counts'])==9 and sum(r['rows'] for r in quality['live']['raw_counts'])==1550922
    assert quality['historical']['source']['executed_at'] is None
    names_log=(FIXES/'names.log').read_text(encoding='utf-8-sig');assert '### Error' not in names_log
    names=json.loads(names_log.split('### Result',1)[1].split('### Ran',1)[0].strip())
    assert len(names['checks'])==6
    approved={'cool_stuff':'Cool Stuff','la_cuisine':'La Cuisine','seguros_e_servicos':'Seguros e Serviços'}
    for check in names['checks']:
        assert check['display_name']==approved[check['code']] and check['raw_query_value']==check['code']
        with (FIXES/check['export']).open(encoding='utf-8-sig',newline='') as file:exported=list(csv.DictReader(file))
        endpoint=f"analysis/{check['page']}?category={check['code']}"
        data=get(endpoint);table='categories' if check['page']=='products' else 'association'
        assert len(exported)==len(data[table])
        for actual,expected in zip(exported,data[table]):
            assert actual['scope_category']==check['code']
            for key,value in expected.items():assert actual[key]==('' if value is None else str(value))
    node=ET.parse(FIXES/'pytest.xml').getroot().find('testsuite')
    tests={k:int(node.get(k,0)) for k in ('tests','failures','errors','skipped')}
    assert tests==dict(tests=144,failures=0,errors=0,skipped=0)
    assert '28 passed' in (FIXES/'frontend_tests.log').read_text(encoding='utf-8-sig')
    assert read(FIXES/'typecheck_result.json')['exit_code']==0
    assert 'built in' in (FIXES/'build.log').read_text(encoding='utf-8-sig')
    labels=read(ROOT/'frontend/src/categoryLabels.json')
    assert set(labels)==set(baseline['api']['analysis/products']['metadata']['categories'])
    for code,name in approved.items():assert labels[code]['zh']==name and labels[code]['status']=='preserved_name'
    assert '125%' in read(OUT/'native_zoom_receipt.json')['zoomControl']
    shots={}
    for p in (ROOT/'docs/screenshots/ui-final').glob('*.png'):
        with Image.open(p) as im:assert im.format=='PNG';shots[p.name]=list(im.size);im.verify()
    for page in ('overview','users','products','delivery','findings','quality'):
        assert shots[f'{page}-1440-z100.png']==[1440,1000] and shots[f'{page}-1280-z100.png']==[1280,900]
        assert shots[f'{page}-1440-z100-full.png'][1]>=1000 and shots[f'{page}-1280-z100-full.png'][1]>=900
    evidence_summary={
        'automated_tests':{'backend':tests,'frontend_passed':28,'source':'reports/ui-final-fixes','backend_executed_at':node.get('timestamp')},
        'browser_interactions':{'visited_routes':len(ui['visited_routes']),'checked_at':ui['checked_at'],'source':'reports/ui-final/browser.log','record_kind':'fresh_interaction_run'},
        'special_category_interactions':{'checks':len(names['checks']),'checked_at':names['checked_at'],'source':'reports/ui-final-fixes/names.log','record_kind':'fresh_interaction_run'},
        'screenshot_checks':{'records':sum(len(s['pages']) for s in screen_results.values()),'source_logs':['reports/ui-final/screens_100.log','reports/ui-final/screens_125.log'],'record_kind':'preceding_ui_final_snapshot','refreshed_this_fix':False},
        'state_checks':{'records':sum(len(s['checks']) for s in state_results.values()),'source_logs':['reports/ui-final/states_100.log','reports/ui-final/states_125.log'],'record_kind':'preceding_ui_final_snapshot','refreshed_this_fix':False},
        'detail_checks':{'source':'reports/ui-final/details.log','record_kind':'preceding_ui_final_snapshot','refreshed_this_fix':False},
    }
    result={'schema_version':2,'verified_at':datetime.now(timezone.utc).isoformat(),'evidence_summary':evidence_summary,'passed':True,'protected_sources_unchanged':len(baseline['protected']),
        'accepted_p0_files_unchanged':len(files),'raw_mart_fingerprints_unchanged':True,
        'five_api_payloads_identical':True,'backend':tests,'frontend_passed':28,
        'typecheck_passed':True,'build_passed':True,'csv_exports_reconciled':13,'baseline_csv_exports_reconciled':7,'special_category_csv_exports_reconciled':6,
        'markdown_exact_bytes':True,'quality_json_reconciled':True,'browser':ui,'special_category_checks':names,'final_screens':screen_results,'state_checks':state_results,'detail_checks':extra,'export_columns':export_columns,'category_status_counts':dict(Counter(r['status'] for r in labels.values())),'screenshots':shots}
    (OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
