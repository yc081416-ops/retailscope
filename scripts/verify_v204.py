"""Read-only final reconciliation. Never rebuild accepted data or statistical models."""
import csv
import gzip
import json
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image
from retailscope.runtime import digest
from retailscope.verification import snapshot_raw
from retailscope.warehouse import snapshot_mart
from retailscope.bi.components import evidence_path, analysis_report_path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/v2-04'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def browser(name):
    value = (OUT / name).read_text(encoding='utf-8-sig')
    assert '### Error' not in value, name
    return json.loads(value.split('### Result', 1)[1].split('### Ran', 1)[0].strip())


def get(path):
    with urllib.request.urlopen('http://127.0.0.1:8000/api/' + path, timeout=45) as response:
        return json.load(response)


def main():
    load_dotenv(ROOT / '.env')
    baseline = read(OUT / 'baseline.json')
    assert baseline['raw'] == snapshot_raw() and baseline['mart'] == snapshot_mart()
    changed = [name for name, sha in baseline['protected'].items() if digest(ROOT / name) != sha]
    assert not changed, changed
    accepted = read(ROOT / 'reports/v2-03/accepted_artifact_check.json')
    p1 = read(ROOT / 'reports/p1/run.json')
    for name in accepted['checked']:
        assert digest(ROOT / name) == p1['p0_file_sha256'][name], name
    p3_path = evidence_path('reports/p3/analysis.json')
    assert digest(p3_path) == read(ROOT / 'reports/p3/verification.json')['analysis_sha256']
    findings = get('evidence/findings')
    assert findings['findings'] == read(p3_path)['findings'] and len(findings['findings']) == 7
    home = get('overview')
    assert home['kpis']['orders'] == 96478 and home['kpis']['users'] == 93358
    assert str(home['kpis']['merchandise']) == '13221498.11'
    users = get('analysis/users')
    assert sum(r['users'] for r in users['segments']) == 93358
    assert len(users['segments']) == 6 and len(users['cohort']) == 552
    assert sum(r['retention'] is None for r in users['cohort']) == 298
    # CSV values are independently reconciled to a fresh read-only API query.
    for filename, endpoint, table in [
        ('users-cohort.csv', 'analysis/users', 'cohort'),
        ('products-filtered.csv', 'analysis/products?start=2017-05-10&end=2017-06-20&state=SP&category=beleza_saude', 'categories'),
        ('delivery-filtered.csv', 'analysis/delivery?start=2017-05-10&end=2017-06-20&state=SP&category=beleza_saude', 'association'),
    ]:
        with (OUT / filename).open(encoding='utf-8-sig', newline='') as file:
            exported = list(csv.DictReader(file))
        data = get(endpoint)
        expected = data[table]
        assert len(exported) == len(expected), filename
        for actual, row in zip(exported, expected):
            for key, value in row.items():
                if isinstance(value, bool): value = str(value)
                assert actual[key] == ('' if value is None else str(value)), (filename, key, actual[key], value)
            for key in ('mode', 'start', 'end', 'state', 'category'):
                assert actual['scope_' + key] == str(data['scope'][key] or 'ALL')
    assert (OUT / 'downloaded_report.md').read_bytes() == analysis_report_path().read_bytes()
    with (OUT / 'overview-filtered.csv').open(encoding='utf-8-sig', newline='') as file:
        exported_home = list(csv.DictReader(file))
    expected_home = get('overview?start=2017-05-10&end=2017-06-20&state=SP')['monthly']
    assert len(exported_home) == len(expected_home)
    for actual, row in zip(exported_home, expected_home):
        assert actual['scope_start'] == '2017-05-10' and actual['scope_end'] == '2017-06-20' and actual['scope_state'] == 'SP'
        for key, value in row.items(): assert actual[key] == str(value)
    quality = read(OUT / 'downloaded_quality.json')
    assert quality['live']['status'] == 'available' and len(quality['live']['raw_counts']) == 9
    assert sum(row['rows'] for row in quality['live']['raw_counts']) == 1550922
    audit = read(ROOT / 'reports/raw_quality.json')
    assert {r['table']:r['audit_rows'] for r in quality['historical']['tables']} == {r['table']:r['row_count'] for r in audit['tables']}
    assert quality['historical']['source']['executed_at'] is None
    assert quality['historical']['source']['file_saved_at'] and quality['analysis_snapshot']['report_matches']
    assert quality['tests']['latest']['stage'] == 'V2-04' and quality['tests']['latest']['tests'] == 144
    node = ET.parse(OUT / 'pytest.xml').getroot().find('testsuite')
    tests = {key:int(node.get(key, 0)) for key in ('tests','failures','errors','skipped')}
    assert tests == dict(tests=144, failures=0, errors=0, skipped=0)
    assert '22 passed' in (OUT / 'frontend_tests.log').read_text(encoding='utf-8-sig')
    assert read(OUT / 'typecheck_result.json')['exit_code'] == 0
    build = (OUT / 'build.log').read_text(encoding='utf-8-sig')
    assert 'built in' in build and 'larger than' not in build
    ui = browser('browser.log')
    assert len(ui['pages']) == 12 and len(ui['direct_urls']) == 6 and not ui['page_errors']
    assert all(not p['horizontalOverflow'] and not p['clippedKpis'] and p['titleFont'] == 29 for p in ui['pages'])
    assert all(p['loaded'] for p in ui['direct_urls'])
    assert all(ui[k] for k in ['rfm_cohort_verified','f05_semantics_verified','seven_findings_verified','quality_provenance_verified','navigation_history_verified','products_empty','delivery_empty','overview_draft_preserved','overview_reset','all_api_error_loading_recovery_verified'])
    assert browser('tooltips.log')['all_visible'] and len(browser('tooltips.log')['tooltips']) == 5
    assert all(browser('extra_interactions.log').values())
    assert browser('legend.log')['legend_click_toggles'] and browser('legend.log')['restored']
    failed, recovered = browser('db_failure.log'), browser('db_recovery.log')
    assert failed['actual_database_failure'] and failed['stale_kpis_hidden'] and recovered['recovered']
    legacy = browser('legacy_browser.log')
    assert legacy['legacy_available'] and legacy['exceptions'] == 0
    screenshots = {}
    for path in (ROOT / 'docs/screenshots/v2-04').glob('*.png'):
        with Image.open(path) as im:
            assert im.format == 'PNG'
            screenshots[path.name] = list(im.size)
            im.verify()
    assert len(screenshots) == 26
    for page in ('overview','users','products','delivery','findings','quality'):
        assert screenshots[f'{page}-1440.png'] == [1440,1000]
        assert screenshots[f'{page}-1280.png'] == [1280,900]
        for width, height in ((1440,1000),(1280,900)):
            size = screenshots[f'{page}-{width}-full.png']
            assert size[0] in (width, width-15) and size[1] >= height
    dist = ROOT / 'frontend/dist'
    manifest = read(dist / '.vite/manifest.json')
    for name in ('Overview','Users','Products','Delivery','FindingsPage','Quality'):
        assert manifest[f'src/pages/{name}.tsx']['isDynamicEntry']
    for name in ('Users','Products','Delivery','FindingsPage','Quality'):
        assert not any('/' + name + '-' in url for url in ui['home_assets'])
    files = [{'file':str(p.relative_to(dist)), 'bytes':p.stat().st_size,
              'gzip_bytes':len(gzip.compress(p.read_bytes(), mtime=0))} for p in sorted(dist.glob('assets/*.js'))]
    performance = {'files':files, 'max_chunk_bytes':max(r['bytes'] for r in files),
                   'total_js_bytes':sum(r['bytes'] for r in files)}
    assert performance['max_chunk_bytes'] < 500000
    (OUT / 'performance_after.json').write_text(json.dumps(performance, indent=2), encoding='utf-8')
    safety = read(OUT / 'public_safety.json')
    assert safety['passed'] and not safety['configured_remote_count'] and not safety['staged_files']
    assert read(OUT / 'npm_audit.json')['metadata']['vulnerabilities']['total'] == 0
    result = {'passed':True,'backend':tests,'frontend_passed':22,'typecheck_passed':True,'production_build_passed':True,
        'protected_files_unchanged':len(baseline['protected']),'accepted_p0_files_unchanged':len(accepted['checked']),
        'raw_mart_fingerprints_unchanged':True,'p3_analysis_matches_accepted_sha':True,'seven_findings_match':True,
        'rfm_users':93358,'cohort_cells':552,'cohort_null_cells':298,'kpis':home['kpis'],
        'csv_exports_reconciled':4,'markdown_export_exact_bytes':True,'quality_json_reconciled':True,
        'browser':ui,'tooltips':browser('tooltips.log'),'real_database_failure':failed,'database_recovery':recovered,
        'legacy':legacy,'screenshots':screenshots,'performance':performance,'public_safety':safety,
        'limits':['同机最终验收；未在另一台干净Windows重装。','未测公网认证、多用户负载或生产部署。','未录制视频；提供可执行录制步骤。']}
    (OUT / 'final_verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
