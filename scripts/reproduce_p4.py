"""Run full setup on a separate empty DB and clean venv; never print the connection URL."""
import json
import os
from pathlib import Path
import subprocess

from dotenv import load_dotenv
from sqlalchemy.engine import make_url
from retailscope.diagnostics import ROOT,save


def main():
    load_dotenv(ROOT/'.env')
    python=ROOT/'.venv-repro/Scripts/python.exe'
    if not python.is_file():
        raise RuntimeError('请先创建干净的.venv-repro并按requirements-lock.txt安装依赖。')
    url=make_url(os.environ['DATABASE_URL']).set(database='retailscope_p4_repro')
    env=dict(os.environ,DATABASE_URL=url.render_as_string(hide_password=False),PYTHONUTF8='1')
    out=ROOT/'reports/p4/repro'
    out.mkdir(parents=True,exist_ok=True)
    command=[str(python),'-m','retailscope.runtime']
    options=['--isolated','--source',str(out/'raw'),'--output',str(out)]
    results=[]
    for name,action in [('initialization','init'),('repeat_init','init'),('readiness','check'),('versioned_refresh','refresh'),('after_refresh','check')]:
        with (out/f'{name}.log').open('w',encoding='utf-8') as log:
            completed=subprocess.run(command+[action]+options,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        results.append({'step':name,'exit_code':completed.returncode})
        print(name,completed.returncode,flush=True)
        if completed.returncode:
            save({'passed':False,'steps':results},out/'reproduction.json')
            return 1
    manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    result=json.loads(Path(manifest['analysis_path']).read_text(encoding='utf-8'))
    accepted=json.loads((ROOT/'reports/p3/analysis.json').read_text(encoding='utf-8'))
    # Execution timestamps are expected to differ; all scientific inputs and results must match.
    stable=lambda r:{k:v for k,v in r.items() if k!='generated_at'}
    assert stable(result)==stable(accepted),'Full reproduced diagnostics differ from accepted P3'
    with (out/'pytest.log').open('w',encoding='utf-8') as log:
        tested=subprocess.run([str(python),'-m','pytest','-q','-rA','--junitxml=reports/p4/repro/pytest.xml'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
    results.append({'step':'full_tests_clean_venv_and_new_db','exit_code':tested.returncode})
    evidence={'passed':tested.returncode==0,'steps':results,'independent_database':'retailscope_p4_repro',
        'clean_virtual_environment':str(python),'all_seven_findings_equal':True,
        'all_scientific_results_equal':True,'raw_rows':sum(v['rows'] for v in manifest['raw'].values()),
        'manifest':str(out/'manifest.json'),
        'scope_limit':'同一Windows主机、同一Docker PostgreSQL服务的新空数据库；复用官方Kagglehub缓存和pip缓存，未声称新OS或清空网络缓存验证。'}
    save(evidence,out/'reproduction.json')
    print('Full pipeline reproduction and repeated-init/refresh checks passed:',evidence['passed'])
    return tested.returncode


if __name__=='__main__':
    raise SystemExit(main())
