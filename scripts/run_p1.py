"""Execute P1 twice, preserve P0, independently reconcile and run all tests."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from retailscope.database import db_status
from retailscope.verification import snapshot_raw
from retailscope.warehouse import SCRIPTS, build_warehouse, export_results, save_json, snapshot_mart

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/p1'


def frozen_p0():
    paths = [ROOT / 'docs/P0_ACCEPTANCE_REPORT.md', ROOT / 'docs/quality_report.md', ROOT / 'sql/00_raw.sql']
    paths += list((ROOT / 'data/raw').glob('*.csv'))
    paths += [p for p in (ROOT / 'reports').iterdir() if p.is_file()]
    paths += [p for p in (ROOT / 'tests').glob('*.py') if p.name != 'test_p1.py']
    result = {}
    for path in paths:
        with path.open('rb') as handle:
            result[str(path.relative_to(ROOT))] = hashlib.file_digest(handle, 'sha256').hexdigest()
    return result


def main():
    os.chdir(ROOT)
    load_dotenv()
    OUT.mkdir(exist_ok=True)
    start = time.perf_counter()
    evidence = {'started_at': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(), 'status': 'running', 'database': db_status()}
    save_json(evidence, OUT / 'run.json')
    files_before, raw_before = frozen_p0(), snapshot_raw()
    baseline = json.loads((ROOT / 'reports/import_verification.json').read_text())
    assert raw_before == baseline['second_snapshot'], 'P0 raw fingerprint changed'
    snapshots = []
    for run in (1, 2):
        build_warehouse(ROOT / 'sql')
        snapshot = snapshot_mart()
        save_json(snapshot, OUT / f'mart_snapshot_{run}.json')
        snapshots.append(snapshot)
        print(f'Build {run}: {len(snapshot)} mart objects checked', flush=True)
    evidence['idempotent'] = snapshots[0] == snapshots[1]
    assert evidence['idempotent'], 'P1 rebuild changed result content'
    export_results(OUT)
    env = dict(os.environ, PYTHONUTF8='1')
    with (OUT / 'pytest.log').open('w', encoding='utf-8') as log:
        tests = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-rA', '--junitxml=reports/p1/pytest.xml'], stdout=log, stderr=subprocess.STDOUT, env=env)
    evidence['pytest_exit_code'] = tests.returncode
    evidence['pandas_passed'] = json.loads((OUT / 'pandas_reconciliation.json').read_text())['passed']
    evidence['raw_unchanged'] = raw_before == snapshot_raw()
    evidence['p0_files_unchanged'] = files_before == frozen_p0()
    evidence['p0_file_sha256'] = files_before
    evidence['sql_sha256'] = {name: hashlib.sha256((ROOT / 'sql' / name).read_bytes()).hexdigest() for name in SCRIPTS}
    evidence['elapsed_seconds'] = round(time.perf_counter() - start, 3)
    evidence['status'] = 'passed' if all((evidence['idempotent'], evidence['pandas_passed'], evidence['raw_unchanged'], evidence['p0_files_unchanged'], tests.returncode == 0)) else 'failed'
    save_json(evidence, OUT / 'run.json')
    print(json.dumps({k: v for k, v in evidence.items() if k not in ('p0_file_sha256', 'sql_sha256')}, ensure_ascii=False, indent=2))
    return 0 if evidence['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
