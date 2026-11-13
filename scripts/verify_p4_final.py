"""Read-only final reconciliation of database, protected files and actual run evidence."""
import json
from datetime import date
from pathlib import Path
import platform
import sys
import xml.etree.ElementTree as ET

import pandas as pd
from dotenv import load_dotenv
from PIL import Image
from retailscope.diagnostics import ROOT,save
from retailscope.runtime import digest,json_read,readiness
from retailscope.verification import snapshot_raw
from retailscope.warehouse import snapshot_mart
from retailscope.bi.data import execute,Filters


def browser(name):
    value=(ROOT/'reports/p4'/name).read_text(encoding='utf-8-sig')
    return json.loads(value.split('### Result',1)[1].split('### Ran',1)[0].strip())


def suite(path):
    node=ET.parse(path).getroot().find('testsuite')
    result={k:int(node.get(k,0)) for k in ('tests','failures','errors','skipped')}
    assert result['tests']>0 and not any(result[k] for k in ('failures','errors','skipped'))
    return result


def main():
    load_dotenv(ROOT/'.env')
    baseline=json_read(ROOT/'reports/p4/baseline.json')
    changed=[name for name,sha in baseline['protected_files'].items() if digest(ROOT/name)!=sha]
    assert not changed,changed
    assert baseline['raw']==snapshot_raw()
    assert baseline['mart']==snapshot_mart()
    current=readiness()
    assert current['ready']
    tests=suite(ROOT/'reports/p4/pytest.xml')
    clean=suite(ROOT/'reports/p4/repro/pytest_final.xml')
    assert tests==clean
    reproduction=json_read(ROOT/'reports/p4/repro/reproduction.json')
    assert reproduction['passed'] and reproduction['all_scientific_results_equal']
    primary=json_read(ROOT/'reports/p3/analysis.json')
    manifest=json_read(ROOT/'reports/p4/repro/manifest.json')
    copied=json_read(manifest['analysis_path'])
    assert {k:v for k,v in primary.items() if k!='generated_at'}=={k:v for k,v in copied.items() if k!='generated_at'}
    assert (ROOT/'reports/p4/downloaded_report.md').read_text(encoding='utf-8-sig')==(ROOT/'docs/P3_BUSINESS_REPORT.md').read_text(encoding='utf-8-sig')
    assert (ROOT/'reports/p4/repro/downloaded_report.md').read_text(encoding='utf-8-sig')==Path(manifest['run_dir'],'P3_BUSINESS_REPORT.md').read_text(encoding='utf-8-sig')
    ui=browser('browser.log')
    assert len(ui['pages'])==6 and all(p['exceptions']==0 and not p['horizontalOverflow'] for p in ui['pages'])
    assert ui['cohort_nulls']==298 and ui['reset_restored_full_sample']
    assert browser('failure_browser.log')['database_failure_message_visible']
    assert browser('recovery_browser.log')['recovered']
    isolated=browser('repro/browser.log')
    assert isolated['exceptions']==0 and isolated['overview']==ui['pages'][0]['metrics']
    downloaded=pd.read_csv(ROOT/'reports/p4/filtered-category.csv')
    query=execute('categories',Filters(date(2016,1,1),date(2019,1,1),states=('SP',),categories=('beleza_saude',)))
    for column in ('merchandise','freight','contribution'):
        query[column]=query[column].astype(float)
    pd.testing.assert_frame_equal(downloaded,query,check_dtype=False,rtol=1e-12)
    safety=json_read(ROOT/'reports/p4/public_safety.json')
    assert safety['passed'] and not safety['staged_files'] and safety['configured_remote_count']==0
    screenshots={p.name:list(Image.open(p).size) for p in (ROOT/'docs/screenshots').glob('*.png')}
    assert len(screenshots)>=12 and screenshots['01-overview-full.png'][1]>=1800
    result={'passed':True,'python':sys.version.split()[0],'platform':platform.platform(),
        'database':current['database'],'protected_files_unchanged':len(baseline['protected_files']),
        'raw_unchanged':True,'mart_unchanged':True,'env_unchanged':True,'primary_tests':tests,
        'clean_environment_tests':clean,'scientific_results_reproduced':True,'findings':len(primary['findings']),
        'six_pages_verified':True,'database_failure_and_recovery_verified':True,'filtered_export_matches_sql':True,
        'report_downloads_match_generated_text':True,'screenshots':screenshots,'public_safety':safety,
        'raw_counts':current['raw_rows'],'reproduction_scope':reproduction['scope_limit'],
        'video_created':False,'public_deployment_performed':False}
    save(result,ROOT/'reports/p4/final_verification.json')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
