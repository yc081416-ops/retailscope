"""Read-only P2 acceptance: compare live SQL, browser downloads and preserved P0/P1."""
from datetime import date, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pandas as pd
from dotenv import load_dotenv
from retailscope.bi.components import money, number
from retailscope.bi.data import Filters, execute
from retailscope.verification import snapshot_raw
from retailscope.warehouse import save_json, snapshot_mart

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/p2'


def browser_result(name):
    content=(OUT/name).read_text(encoding='utf-8-sig')
    assert '### Error' not in content, f'Browser check failed: {name}'
    return json.loads(content.split('### Result\n',1)[1].split('\n### Ran Playwright code',1)[0].strip())


def main():
    load_dotenv(ROOT/'.env')
    baseline=json.loads((OUT/'baseline.json').read_text())
    files_same=all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in baseline['protected_files'].items())
    raw,mart=snapshot_raw(),snapshot_mart()
    assert files_same and raw==baseline['raw'] and mart==baseline['mart'], 'P0/P1 changed'
    browser=browser_result('browser.log')
    assert len(browser['pages'])==6 and all(not p['exceptions'] and not p['horizontalOverflow'] for p in browser['pages'])
    assert [p['plots'] for p in browser['pages']]==[3,5,5,4,0,0]
    bounds=execute('bounds').iloc[0]
    full=Filters(bounds.first_date,bounds.last_date+timedelta(days=1))
    kpi=execute('overview',full).iloc[0]
    expected=json.loads((ROOT/'reports/p1/kpi_overview.json').read_text())[0]
    assert all(kpi[key]==(Decimal(value) if isinstance(value,str) else value) for key,value in expected.items())
    assert browser['pages'][0]['metrics']==[money(kpi.merchandise),number(kpi.orders),number(kpi.users),money(kpi.average_order_value)]
    filtered=Filters(full.start,full.end,('SP',),('beleza_saude',))
    query=execute('categories',filtered)
    downloaded=pd.read_csv(ROOT/'output/playwright/filtered-category.csv',dtype={'merchandise':str,'freight':str,'contribution':str})
    assert len(downloaded)==len(query)==1
    for key in ('merchandise','freight','contribution'):
        assert Decimal(downloaded.iloc[0][key])==query.iloc[0][key]
    assert downloaded.iloc[0].category==query.iloc[0].category
    assert int(downloaded.iloc[0].orders)==int(query.iloc[0].orders)
    dates=browser_result('browser-date.log')
    dated=execute('product_kpis',Filters(date(2018,1,1),date(2018,2,1))).iloc[0]
    assert dates['metrics']==[money(dated.merchandise),number(dated['items']),number(dated.orders),money(dated.freight)]
    failure=(OUT/'failure-browser.log').read_text(encoding='utf-8-sig')
    assert '数据暂时无法读取' in failure and '重新连接' in failure
    assert 'postgresql://' not in failure and 'unavailable@' not in failure
    tests=ET.parse(OUT/'pytest.xml').getroot().find('testsuite')
    test_counts={k:int(tests.get(k,0)) for k in ('tests','failures','errors','skipped')}
    assert test_counts['failures']==test_counts['errors']==test_counts['skipped']==0
    screenshots={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'output/playwright').glob('*.png')}
    assert len(screenshots)>=10
    report={
        'passed':True,'p0_p1_files_unchanged':files_same,'raw_unchanged':True,'mart_unchanged':True,
        'kpis':{key:value.item() if hasattr(value,'item') else value for key,value in kpi.items()},
        'repeat_rate':execute('repurchase').iloc[0].repeat_rate,
        'browser':browser,'date_filter':dates,'download_matches_sql':True,
        'isolated_database_failure_message_verified':True,'tests':test_counts,'screenshots':screenshots,
    }
    save_json(report,OUT/'acceptance.json')
    print(f"P2 acceptance passed: {test_counts['tests']} tests; six browser pages; downloads reconciled; P0/P1 unchanged.")


if __name__=='__main__':
    main()
