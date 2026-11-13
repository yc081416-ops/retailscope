"""Read-only release reconciliation; requires local services and accepted artifacts."""
import hashlib
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
from retailscope.bi.components import evidence_path
from retailscope.verification import snapshot_raw
from retailscope.warehouse import snapshot_mart

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/github-release'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    load_dotenv(ROOT / '.env')
    baseline = read(ROOT / 'reports/github-release/baseline.json')
    for name, digest in baseline['protected'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    for endpoint, expected in baseline['api'].items():
        with urllib.request.urlopen('http://127.0.0.1:8000/api/' + endpoint, timeout=60) as response:
            assert json.load(response) == expected, endpoint
    accepted = read(ROOT / 'reports/v2-04/baseline.json')
    assert snapshot_raw() == accepted['raw']
    assert snapshot_mart() == accepted['mart']
    p1 = read(ROOT / 'reports/p1/run.json')
    artifacts = read(ROOT / 'reports/v2-03/accepted_artifact_check.json')['checked']
    for name in artifacts:
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == p1['p0_file_sha256'][name], name
    p3 = read(ROOT / 'reports/p3/verification.json')
    assert hashlib.sha256(evidence_path('reports/p3/analysis.json').read_bytes()).hexdigest() == p3['analysis_sha256']
    suite = ET.parse(OUT / 'pytest.xml').getroot().find('testsuite')
    tests = {key: int(suite.get(key, 0)) for key in ('tests', 'failures', 'errors', 'skipped')}
    assert tests == dict(tests=144, failures=0, errors=0, skipped=0)
    assert '28 passed' in (OUT / 'frontend_tests.log').read_text(encoding='utf-8-sig')
    assert read(OUT / 'typecheck_result.json')['exit_code'] == 0
    assert 'built in' in (OUT / 'build.log').read_text(encoding='utf-8-sig')
    links = []
    for source in ('README.md', 'docs/GITHUB_RELEASE_CHECKLIST.md', 'docs/GITHUB_FINAL_RELEASE_REPORT.md', 'docs/DATA_LICENSE.md', 'docs/THIRD_PARTY_LICENSES.md'):
        text = (ROOT / source).read_text(encoding='utf-8')
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', text):
            if '://' in target or target.startswith('#'):
                continue
            assert (ROOT / source).parent.joinpath(target.split('#')[0]).exists(), (source, target)
            links.append(target)
    screenshots = {}
    for path in (ROOT / 'docs/screenshots/showcase').glob('*.png'):
        with Image.open(path) as image:
            assert image.format == 'PNG'
            screenshots[path.name] = list(image.size)
            image.verify()
    assert len(screenshots) == 9
    fresh_browser = (OUT / 'browser.log').is_file()
    browser_log = (OUT / ('browser.log' if fresh_browser else 'showcase.log')).read_text(encoding='utf-8-sig')
    browser = json.loads(browser_log.split('### Result', 1)[1].split('### Ran', 1)[0].strip())
    if fresh_browser:
        assert len(browser['visited_routes']) == 6 and all(row['loaded'] and row['status'] == 200 for row in browser['visited_routes'])
        assert '13,221,498.11' in browser['kpi']
    else:
        assert len(browser['pages']) == 6 and '13,221,498.11' in browser['real_database_kpi']
    license_text = (ROOT / 'LICENSE').read_text(encoding='utf-8')
    assert license_text.startswith('MIT License\n\nCopyright (c) 2026 [yan]\n')
    assert 'TO BE CONFIRMED' not in license_text
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    assert 'Copyright (c) 2026 [yan]' in readme and 'CC BY-NC-SA 4.0' in readme
    safety = read(OUT / 'public_safety.json')
    assert safety['passed'] and safety['configured_remote_count'] == 0
    assert not safety['staged_files'] and safety['branch_commits'] == 0
    result = dict(passed=True, checked_at=datetime.now().astimezone().isoformat(),
                  protected_files_unchanged=len(baseline['protected']), api_payloads_unchanged=len(baseline['api']),
                  raw_and_mart_match_accepted=True, original_artifacts_unchanged=len(artifacts),
                  accepted_analysis_unchanged=True, backend_tests=tests, frontend_tests_passed=28,
                  typecheck_and_build=True, local_links_checked=len(links), screenshots=screenshots,
                  browser_page_loading_run=browser, public_safety_passed=True,
                  license_and_readme_consistent=True,
                  scope='Existing initialized Windows environment; no fresh OS/database initialization this round. Browser evidence is six-page navigation and screenshots, not a new full interaction acceptance.')
    (OUT / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
