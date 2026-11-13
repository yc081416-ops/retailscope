"""Serve only the isolated P4 database/snapshot on localhost:8503 for reproduction QA."""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.engine import make_url
from retailscope.diagnostics import ROOT

os.chdir(ROOT)
load_dotenv(ROOT/'.env')
url=make_url(os.environ['DATABASE_URL']).set(database='retailscope_p4_repro')
os.environ['DATABASE_URL']=url.render_as_string(hide_password=False)
os.environ['RETAILSCOPE_RUNTIME_MANIFEST']=str(ROOT/'reports/p4/repro/manifest.json')
sys.argv=['streamlit','run','app/Home.py','--server.port','8503','--server.headless','true']
from streamlit.web import cli
raise SystemExit(cli.main())
