"""Final P3 evidence gate; read-only snapshots and exact downloaded-report comparison."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from retailscope.diagnostics import ROOT,QUERY_NAMES,markdown_report,save
from retailscope.verification import snapshot_raw
from retailscope.warehouse import snapshot_mart

OUT=ROOT/'reports/p3'


def main():
    load_dotenv(ROOT/'.env')
    baseline=json.loads((OUT/'baseline.json').read_text(encoding='utf-8'))
    files={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in baseline['protected_files'].items()}
    assert all(files.values()),[name for name,ok in files.items() if not ok]
    assert snapshot_raw()==baseline['raw'],'P0 raw changed'
    assert snapshot_mart()==baseline['mart'],'P1 mart changed'
    result=json.loads((OUT/'analysis.json').read_text(encoding='utf-8'))
    original=json.loads((OUT/'initial_analysis.json').read_text(encoding='utf-8'))
    assert result['association']['cluster_bootstrap']==original['association']['cluster_bootstrap']
    assert result['input_csv_sha256']==original['input_csv_sha256']
    assert all(hashlib.sha256((ROOT/'sql/p3'/f'{name}.sql').read_bytes()).hexdigest()==digest for name,digest in result['sql_sha256'].items())
    document=markdown_report(result)
    assert (ROOT/'docs/P3_BUSINESS_REPORT.md').read_text(encoding='utf-8')==document
    downloaded=(ROOT/'output/playwright/p3/downloaded_P3_BUSINESS_REPORT.md').read_text(encoding='utf-8')
    assert downloaded==document,'Browser export is stale or inconsistent'
    browser_text=(OUT/'browser.log').read_text(encoding='utf-8-sig')
    assert '### Error' not in browser_text
    browser=json.loads(browser_text.split('### Result\n',1)[1].split('\n### Ran Playwright code',1)[0])
    assert len(browser['pages'])==6 and all(not p['exceptions'] and not p['horizontalOverflow'] for p in browser['pages'])
    assert browser['axes']['orders'][0]==browser['axes']['amount'][0]==0
    assert all(p.get('placeholder','请选择（留空为全部）')=='请选择（留空为全部）' for p in browser['pages'])
    tests=ET.parse(OUT/'pytest.xml').getroot().find('testsuite')
    counts={k:int(tests.get(k,0)) for k in ('tests','failures','errors','skipped')}
    assert counts['failures']==counts['errors']==counts['skipped']==0
    assert 'warnings summary' not in (OUT/'pytest.log').read_text(encoding='utf-8-sig')
    proof={'passed':True,'verified_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
           'protected_files_unchanged':True,'protected_file_count':len(files),'raw_unchanged':True,'mart_unchanged':True,
           'same_input_and_seed_reproduced_bootstrap':True,'browser_export_equals_generated_report':True,
           'tests':counts,'browser':browser,'analysis_sha256':hashlib.sha256((OUT/'analysis.json').read_bytes()).hexdigest(),
           'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'src/retailscope/diagnostics.py',ROOT/'src/retailscope/bi/diagnostic_page.py']},
           'screenshots':[str(p.relative_to(ROOT)) for p in sorted((ROOT/'output/playwright/p3').glob('*.png'))]}
    save(proof,OUT/'verification.json')
    print(f"P3 verified: {counts['tests']} passing tests; six live browser pages; report download matches; P0/P1 and prior reports preserved.")


if __name__=='__main__':
    main()
