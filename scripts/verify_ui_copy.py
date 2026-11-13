"""Read-only data and presentation reconciliation for the UI copy pass."""
import csv
import hashlib
import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
from retailscope.bi.components import analysis_report_path
from retailscope.verification import snapshot_raw
from retailscope.warehouse import snapshot_mart

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/ui-copy'


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
    assert len(ui['pages'])==12 and not ui['page_errors'] and ui['navigation'] and ui['loading_error_recovery']
    assert all(not p['overflow'] and not p['clippedKpis'] for p in ui['pages'])
    assert all('F0'+str(i) in ui['evidence_preserved'] for i in range(1,8))
    screen_log=(OUT/'screens.log').read_text(encoding='utf-8-sig');assert '### Error' not in screen_log
    screens=json.loads(screen_log.split('### Result',1)[1].split('### Ran',1)[0].strip())
    assert screens['final_screens_verified'] and len(screens['pages'])==12
    assert ui['overview_draft_and_reset'] and len(ui['filters'])==2 and len(ui['downloads'])==6
    for filename,endpoint,table in [('users-cohort.csv','analysis/users','cohort'),
        ('products-filtered.csv','analysis/products?start=2017-05-10&end=2017-06-20&state=SP&category=beleza_saude','categories'),
        ('delivery-filtered.csv','analysis/delivery?start=2017-05-10&end=2017-06-20&state=SP&category=beleza_saude','association'),
        ('overview-filtered.csv','overview?start=2017-05-10&end=2017-06-20&state=SP','monthly')]:
        with (OUT/filename).open(encoding='utf-8-sig',newline='') as f:actual=list(csv.DictReader(f))
        expected=get(endpoint)[table];assert len(actual)==len(expected)
        for row,source in zip(actual,expected):
            for key,value in source.items():assert row[key]==('' if value is None else str(value)),(filename,key)
    assert (OUT/'report.md').read_bytes()==analysis_report_path().read_bytes()
    quality=read(OUT/'quality.json')
    assert len(quality['live']['raw_counts'])==9 and sum(r['rows'] for r in quality['live']['raw_counts'])==1550922
    assert quality['historical']['source']['executed_at'] is None
    node=ET.parse(OUT/'pytest.xml').getroot().find('testsuite')
    tests={k:int(node.get(k,0)) for k in ('tests','failures','errors','skipped')}
    assert tests==dict(tests=144,failures=0,errors=0,skipped=0)
    assert '23 passed' in (OUT/'frontend_tests.log').read_text(encoding='utf-8-sig')
    assert read(OUT/'typecheck_result.json')['exit_code']==0
    assert 'built in' in (OUT/'build.log').read_text(encoding='utf-8-sig')
    shots={}
    for p in (ROOT/'docs/screenshots/ui-copy').glob('*.png'):
        with Image.open(p) as im:assert im.format=='PNG';shots[p.name]=list(im.size);im.verify()
    for page in ('overview','users','products','delivery','findings','quality'):
        assert shots[f'{page}-1440.png']==[1440,1000] and shots[f'{page}-1280.png']==[1280,900]
        assert shots[f'{page}-1440-full.png'][1]>=1000 and shots[f'{page}-1280-full.png'][1]>=900
    result={'passed':True,'protected_sources_unchanged':len(baseline['protected']),
        'accepted_p0_files_unchanged':len(files),'raw_mart_fingerprints_unchanged':True,
        'five_api_payloads_identical':True,'backend':tests,'frontend_passed':23,
        'typecheck_passed':True,'build_passed':True,'csv_exports_reconciled':4,
        'markdown_exact_bytes':True,'quality_json_reconciled':True,'browser':ui,'final_screens':screens,'screenshots':shots}
    (OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
