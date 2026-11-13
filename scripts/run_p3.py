"""Compute P3 diagnostics against the existing warehouse; no DDL or raw writes."""
from dotenv import load_dotenv
from retailscope.diagnostics import ROOT,run_analysis

load_dotenv(ROOT/'.env')
result=run_analysis()
print('Generated',len(result['findings']),'findings')
print('Association groups:',result['association']['groups'])
print('Cluster CI:',result['association']['cluster_bootstrap'])
print('HHI:',result['concentration']['hhi'])
