"""Final full test pass in the already reproduced clean environment and separate database."""
import os
import subprocess
from dotenv import load_dotenv
from sqlalchemy.engine import make_url
from retailscope.diagnostics import ROOT,save

load_dotenv(ROOT/'.env')
url=make_url(os.environ['DATABASE_URL']).set(database='retailscope_p4_repro')
env=dict(os.environ,DATABASE_URL=url.render_as_string(hide_password=False),PYTHONUTF8='1')
out=ROOT/'reports/p4/repro'
with (out/'pytest_final.log').open('w',encoding='utf-8') as log:
    process=subprocess.run([str(ROOT/'.venv-repro/Scripts/python.exe'),'-m','pytest','-q','-rA',
        '--junitxml=reports/p4/repro/pytest_final.xml'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
save({'exit_code':process.returncode,'clean_environment':True,'database':'retailscope_p4_repro'},out/'final_tests.json')
print('Final clean-environment test exit code:',process.returncode)
raise SystemExit(process.returncode)
