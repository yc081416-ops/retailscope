"""Read-only final comparison of accepted data, frozen design, real exports and browser evidence."""
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
OUT=ROOT/'reports/v2-02'


def read(name):return json.loads((OUT/name).read_text(encoding='utf-8-sig'))


def browser(name):
    value=(OUT/name).read_text(encoding='utf-8-sig')
    assert '### Error' not in value,name
    return json.loads(value.split('### Result',1)[1].split('### Ran',1)[0].strip())


def get(path):
    with urllib.request.urlopen('http://127.0.0.1:8000'+path,timeout=30) as response:return json.load(response)


def main():
    load_dotenv(ROOT/'.env')
    baseline=read('baseline.json')
    assert baseline['raw']==snapshot_raw()
    assert baseline['mart']==snapshot_mart()
    changed=[name for name,sha in baseline['protected'].items() if digest(ROOT/name)!=sha]
    assert not changed,changed
    suite=ET.parse(OUT/'pytest.xml').getroot().find('testsuite')
    tests={key:int(suite.get(key,0)) for key in ('tests','failures','errors','skipped')}
    assert tests=={'tests':129,'failures':0,'errors':0,'skipped':0}
    assert '13 passed' in (OUT/'frontend_tests.log').read_text(encoding='utf-8-sig')
    assert 'built in' in (OUT/'build.log').read_text(encoding='utf-8-sig')
    ui=browser('browser.log');assert len(ui['pages'])==6 and not ui['page_errors']
    assert all(not r['horizontalOverflow'] and not r['clippedKpis'] and r['chartCount']==4 for r in ui['pages'])
    assert ui['overview_draft_preserved']=={'start':'2017-05-10','end':'2017-06-20','state':'SP'}
    assert ui['overview_local_complete_months']==0 and ui['history_navigation_verified']
    assert all(ui[page+'_error_verified'] and ui[page+'_empty_verified'] for page in ('users','products','delivery'))
    assert not any('/'+name+'-' in asset for name in ('Users','Products','Delivery') for asset in ui['home_loaded_assets'])
    legacy=browser('legacy_browser.log');assert legacy['legacy_available'] and not legacy['exceptions']
    reconciliations={}
    for page,table,file in [('users','cohort','users-cohort.csv'),('products','categories','products-filtered.csv'),('delivery','association','delivery-filtered.csv')]:
        query='' if page=='users' else '?start=2017-05-10&end=2017-06-20&state=SP&category=beleza_saude'
        data=get('/api/analysis/'+page+query)
        with (OUT/file).open(encoding='utf-8-sig',newline='') as handle:exported=list(csv.DictReader(handle))
        assert len(exported)==len(data[table])
        for record,source in zip(exported,data[table]):
            assert record['scope_mode']==data['scope']['mode']
            if page!='users':
                assert record['scope_start']=='2017-05-10' and record['scope_state']=='SP' and record['scope_category']=='beleza_saude'
            for name,value in source.items():assert record[name]==('' if value is None else str(value))
        reconciliations[page]={'rows':len(exported),'matched':True}
        if page=='users':
            assert sum(row['retention']=='' for row in exported)==298
            reconciliations[page]['unobserved_nulls']=298
    snapshot=get('/api/overview')
    assert snapshot['kpis']['orders']==96478 and snapshot['kpis']['merchandise']=='13221498.11'
    manifest=json.loads((ROOT/'frontend/dist/.vite/manifest.json').read_text(encoding='utf-8'))
    page_chunks={}
    for name in ('Overview','Users','Products','Delivery'):
        record=manifest[f'src/pages/{name}.tsx']
        assert record['isDynamicEntry']
        page_chunks[name]={'file':record['file'],'bytes':(ROOT/'frontend/dist'/record['file']).stat().st_size}
    screenshots={p.name:list(Image.open(p).size) for p in (ROOT/'docs/screenshots/v2-02').glob('*.png')}
    for name in ('users','products','delivery'):
        assert screenshots[f'{name}-1440.png']==[1440,1000] and screenshots[f'{name}-1280.png']==[1280,900]
    assert len(screenshots)==15
    safety=read('public_safety.json');assert safety['passed'] and not safety['configured_remote_count']
    assert read('npm_audit.json')['metadata']['vulnerabilities']['total']==0
    value={'passed':True,'backend_tests':tests,'original_backend_cases':103,'new_backend_cases':26,
        'frontend_passed':13,'protected_files_unchanged':len(baseline['protected']),
        'frozen_design_css_unchanged':True,'raw_mart_models_and_env_unchanged':True,
        'browser':ui,'legacy':legacy,'exports':reconciliations,'page_chunks':page_chunks,'screenshots':screenshots,
        'safety':safety,'production_preview_url':'http://127.0.0.1:5174',
        'edge_state_scope':'商品/履约空结果为真实SQL零样本；固定用户页空概要与三页503为浏览器拦截验证，恢复后使用真实API。'}
    (OUT/'final_verification.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(value,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
