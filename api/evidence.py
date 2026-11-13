"""Bounded read-only evidence projections. Never rebuild or run a full audit on page load."""
from datetime import datetime,timezone
import hashlib
import json
import logging
from pathlib import Path
from typing import Literal
import xml.etree.ElementTree as ET

from fastapi import APIRouter,HTTPException
from fastapi.responses import Response
from sqlalchemy import text

from .queries import database,rows
from retailscope.contracts import SOURCES
from retailscope.bi.data import FIXED
from retailscope.bi.components import evidence_path,analysis_report_path
from retailscope.diagnostics import markdown_report

ROOT=Path(__file__).resolve().parents[1]
router=APIRouter(prefix='/api/evidence')
LOGGER=logging.getLogger('retailscope.evidence')
TEST_FILES=[('P0','reports/pytest.xml'),('P1','reports/p1/pytest.xml'),('P3','reports/p3/pytest.xml'),
    ('P4','reports/p4/pytest.xml'),('V2-01','reports/v2-01/pytest.xml'),('V2-01.1','reports/v2-01-1/pytest.xml'),
    ('V2-02','reports/v2-02/pytest.xml'),('V2-03','reports/v2-03/pytest.xml'),('V2-04','reports/v2-04/pytest.xml')]


def safe_path(path):
    path=Path(path).resolve()
    if not path.is_relative_to(ROOT.resolve()):raise ValueError('Evidence path outside project')
    return path


def provenance(path,kind,executed_at=None):
    path=safe_path(path)
    source={'kind':kind,'path':path.relative_to(ROOT.resolve()).as_posix(),
        'executed_at':executed_at,'execution_time_recorded':executed_at is not None,'available':path.is_file()}
    if path.is_file():
        source.update({'file_saved_at':datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat(),
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    return source


def optional_json(relative,kind,recorded_key=None):
    path=safe_path(ROOT/relative)
    source=provenance(path,kind)
    if not source['available']:return None,source
    try:
        data=json.loads(path.read_text(encoding='utf-8-sig'))
        if recorded_key and data.get(recorded_key):
            source.update({'executed_at':data[recorded_key],'execution_time_recorded':True})
        return data,source
    except (ValueError,OSError):
        source.update({'available':False,'error':'证据文件无法解析；未当作通过记录。'})
        return None,source


def accepted_findings():
    path=safe_path(evidence_path('reports/p3/analysis.json'))
    if not path.is_relative_to((ROOT/'reports').resolve()) or path.suffix!='.json':
        raise ValueError('Invalid analytical snapshot location')
    data=json.loads(path.read_text(encoding='utf-8-sig'))
    if data.get('schema_version')!=1 or len(data.get('findings',[]))!=7:
        raise ValueError('Incomplete accepted P3 findings')
    return data,provenance(path,'P3_fixed_snapshot',data.get('generated_at'))


def accepted_report(data):
    path=safe_path(analysis_report_path())
    if path.suffix!='.md' or not any(path.is_relative_to((ROOT/folder).resolve()) for folder in ('docs','reports')):
        raise ValueError('Invalid report location')
    payload=path.read_bytes()
    if path.read_text(encoding='utf-8-sig')!=markdown_report(data):
        raise ValueError('Report and analytical snapshot do not match')
    return payload,provenance(path,'P3_verified_report',data.get('generated_at'))


@router.get('/findings')
def findings_evidence():
    data,source=accepted_findings()
    _,report=accepted_report(data)
    return {'scope':'P3 固定全样本，不随其他页面日期、地区或类目筛选联动。',
        'context':data['context'],'findings':data['findings'],'source':source,
        'report':{**report,'matches_snapshot':True},'read_only':True}


@router.get('/findings/report')
def findings_report():
    data,_=accepted_findings()
    payload,_=accepted_report(data)
    return Response(content=payload,media_type='text/markdown; charset=utf-8',
        headers={'Content-Disposition':'attachment; filename="RetailScope_P3_BUSINESS_REPORT.md"','Cache-Control':'no-store'})


def live_quality():
    try:
        with database().connect() as conn,conn.begin():
            as_of=rows(conn,text('SELECT transaction_timestamp() AS as_of'))[0]['as_of']
            sql=' UNION ALL '.join(f"SELECT '{s.table_name}' AS table_name,count(*) AS rows FROM raw.{s.table_name}" for s in SOURCES)
            counts=rows(conn,text(sql))
            objects=rows(conn,text("""SELECT n.nspname AS schema,c.relname AS object,
                CASE c.relkind WHEN 'r' THEN 'table' WHEN 'p' THEN 'partitioned_table'
                WHEN 'v' THEN 'view' ELSE 'materialized_view' END AS type
                FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname IN ('raw','core','mart') AND c.relkind IN ('r','p','v','m')
                ORDER BY n.nspname,c.relname"""))
            constraints=rows(conn,text("""SELECT n.nspname AS schema,c.relname AS object,
                con.conname AS name,CASE con.contype WHEN 'p' THEN 'PRIMARY KEY'
                WHEN 'f' THEN 'FOREIGN KEY' ELSE 'UNIQUE' END AS type,
                pg_get_constraintdef(con.oid) AS definition FROM pg_constraint con
                JOIN pg_class c ON c.oid=con.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname IN ('raw','core','mart') AND con.contype IN ('p','f','u')
                ORDER BY n.nspname,c.relname,con.conname"""))
            warehouse_checks=rows(conn,text(FIXED['quality']))
        return {'status':'available','as_of':as_of,'kind':'live_database_read_only',
            'query_ids':['V203_RAW_COUNTS','V203_SCHEMA_CATALOG','V203_CONSTRAINT_CATALOG','P1_QUALITY_CHECKS'],
            'raw_counts':counts,'objects':objects,'constraints':constraints,'warehouse_checks':warehouse_checks,
            'note':'当前数据库计数/目录与当前派生仓库查询；不是重新执行CSV全量审计，也不证明快照已重新构建。'}
    except Exception as exc:
        LOGGER.warning('live_quality_unavailable type=%s',type(exc).__name__)
        return {'status':'unavailable','as_of':datetime.now(timezone.utc).isoformat(),
            'kind':'live_database_read_only','raw_counts':[],'objects':[],'constraints':[],'warehouse_checks':[],
            'error':'当前数据库查询不可用，请确认 PostgreSQL 已启动。历史证据仍可查看，不代表当前数据通过检查。'}


def historical_quality():
    audit,source=optional_json('reports/raw_quality.json','P0_historical_audit')
    tables=[];missing=[]
    specs={s.table_name:s for s in SOURCES}
    if audit:
        for table in audit.get('tables',[]):
            spec=specs.get(table['table'])
            tables.append({'table':table['table'],'audit_rows':table['row_count'],
                'full_duplicate_rows':table['duplicate_full_rows'],'logical_key':list(spec.unique_key) if spec else [],
                'key_duplicates':table['duplicate_unique_key_rows'] if spec and spec.unique_key else None,
                'missing_key_rows':table.get('missing_unique_key_rows') if spec and spec.unique_key else None,
                'malformed_rows':table['malformed_rows'],'invalid_numeric':sum(table['invalid_numeric_by_column'].values()),
                'invalid_date':sum(table['invalid_date_by_column'].values())})
            for column in spec.columns if spec else table.get('missing_by_column',{}):
                n=table['missing_by_column'].get(column,0)
                missing.append({'table':table['table'],'column':column,'missing_rows':n,
                    'missing_rate':n/table['row_count'] if table['row_count'] else None})
    relational=(audit or {}).get('relational_quality',{})
    return {'source':source,'tables':tables,'missing':missing,
        'relations':[{'check':key,'rows':value} for key,value in relational.get('checks',{}).items()],
        'nonunique_references':[{'check':key,'rows':value} for key,value in relational.get('nonunique_reference_fields',{}).items()],
        'has_blocking_issues':audit.get('has_blocking_issues') if audit else None,
        'note':'P0历史CSV审计；原文件未记录审计执行时间，文件保存时间不等于审计时间。地理重复、评价文本缺失与非唯一邮编/评价ID/用户标识为源数据特征，不能自动判为程序错误。'}


def test_history():
    history=[]
    for stage,relative in TEST_FILES:
        path=safe_path(ROOT/relative)
        if not path.is_file():continue
        try:
            node=ET.parse(path).getroot()
            suite=node if node.tag=='testsuite' else node.find('testsuite')
            if suite is None:continue
            counts={key:int(suite.get(key,0)) for key in ('tests','failures','errors','skipped')}
            cases=list(suite.iter('testcase'))
            consistent=counts['tests']==len(cases) and all(counts[key]==len(list(suite.iter(tag)))
                for key,tag in [('failures','failure'),('errors','error'),('skipped','skipped')])
            if not consistent:continue
            history.append({'stage':stage,**counts,'passed':counts['tests']-counts['failures']-counts['errors']-counts['skipped'],
                'successful':counts['tests']>0 and not counts['failures'] and not counts['errors'],
                'source':provenance(path,'historical_test_log',suite.get('timestamp')),
                'note':'完整XML逐项计数核对；仅历史执行记录，页面访问不运行测试。XML时间保留原记录，未补造时区。'})
        except (ET.ParseError,ValueError,OSError):continue
    history.sort(key=lambda r:r['source']['file_saved_at'])
    return {'history':history,'latest':history[-1] if history else None,
        'selection':'按完整且计数一致的XML文件保存时间选择最近记录；不等同当前代码自动重测。'}


def quality_evidence():
    download,download_source=optional_json('reports/download_manifest.json','P0_download_record','checked_at_utc')
    run,run_source=optional_json('reports/p1/run.json','P1_build_record','started_at')
    reconcile,reconcile_source=optional_json('reports/p1/pandas_reconciliation.json','P1_independent_reconciliation')
    manifest,manifest_source=optional_json('reports/runtime/manifest.json','runtime_initialization_record')
    p3_status={'available':False}
    try:
        data,p3_source=accepted_findings();_,report=accepted_report(data)
        p3_status={'available':True,'source':p3_source,'findings':len(data['findings']),
            'report_matches':True,'report_source':report,'note':'文件和已验证P3报告一致；未在页面加载时重跑统计或对全库输入做指纹审计。'}
    except (ValueError,OSError,KeyError):
        p3_status['note']='P3快照或报告不可用/不一致；未标记为通过。'
    return {'read_at':datetime.now(timezone.utc).isoformat(),'read_only':True,
        'dataset':{'name':'Olist Brazilian E-Commerce Public Dataset','url':'https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce',
            'license':'CC BY-NC-SA 4.0','version':download.get('cache_version') if download else None,'source':download_source},
        'live':live_quality(),'historical':historical_quality(),
        'warehouse':{'source':run_source,'status':run.get('status') if run else None,
            'idempotent':run.get('idempotent') if run else None,'raw_unchanged_at_run':run.get('raw_unchanged') if run else None,
            'pandas_passed':run.get('pandas_passed') if run else None},
        'reconciliation':{'source':reconcile_source,'passed':reconcile.get('passed') if reconcile else None,
            'checks':reconcile.get('checks',[]) if reconcile else [],'money_comparison':reconcile.get('money_comparison') if reconcile else None},
        'runtime':{'source':manifest_source,'record_present':bool(manifest),
            'expected_raw_rows':{key:value['rows'] for key,value in (manifest or {}).get('raw',{}).items()},
            'note':'初始化历史清单，不在页面执行runtime check、数据重建或全量哈希。'},
        'analysis_snapshot':p3_status,'tests':test_history()}


@router.get('/quality')
def quality():return quality_evidence()


@router.get('/quality/export')
def quality_export(section:Literal['all','historical','tests']='all'):
    # Bounded projected evidence only; no user-chosen file path and no user-level records.
    data=quality_evidence()
    payload=data if section=='all' else {'read_at':data['read_at'],section:data[section]}
    return Response(content=json.dumps(payload,ensure_ascii=False,indent=2).encode('utf-8'),media_type='application/json',
        headers={'Content-Disposition':f'attachment; filename="retailscope-quality-{section}.json"','Cache-Control':'no-store'})
