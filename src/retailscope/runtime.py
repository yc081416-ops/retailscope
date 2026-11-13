"""Safe first setup, daily readiness and versioned refresh; never rewrites .env or accepted reports."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from psycopg import sql

from .audit import audit_all,audit_relations
from .contracts import SOURCES
from .database import _connect,basic_relational_quality,db_status,init_db,load_raw
from .diagnostics import ROOT,QUERY_NAMES,load_sources,run_analysis,save
from .download import download_data
from .p1_validation import validate_pandas
from .verification import snapshot_raw
from .warehouse import TABLES,SCRIPTS,build_warehouse,export_results,snapshot_mart


def digest(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle,'sha256').hexdigest()


def json_read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save_if_absent(value,path):
    """Exclusive creation protects every existing evidence file, even on a repeated init."""
    path=Path(path)
    if path.exists():
        return False
    from .diagnostics import clean
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as handle:
        json.dump(clean(value),handle,ensure_ascii=False,indent=2,allow_nan=False)
    return True


def source_hashes(source):
    return {s.file_name:digest(source/s.file_name) for s in SOURCES}


def input_hashes():
    return {name:hashlib.sha256(frame.to_csv(index=False,na_rep='NA').encode('utf-8-sig')).hexdigest()
            for name,frame in load_sources().items()}


def validate_analysis(result):
    if result.get('schema_version')!=1 or len(result.get('findings',[]))<5:
        raise RuntimeError('经营分析快照不完整；请运行 refresh。')
    current={name:digest(ROOT/'sql/p3'/f'{name}.sql') for name in QUERY_NAMES}
    if current!=result.get('sql_sha256') or input_hashes()!=result.get('input_csv_sha256'):
        raise RuntimeError('经营分析快照已过期：SQL或数据库输入发生变化。请先核对来源，再运行 refresh。')


def raw_state():
    with _connect() as conn:
        result={}
        for spec in SOURCES:
            exists=conn.execute('SELECT to_regclass(%s)',(f'raw.{spec.table_name}',)).fetchone()[0]
            result[spec.table_name]=None if not exists else conn.execute(sql.SQL('SELECT count(*) FROM raw.{}').format(sql.Identifier(spec.table_name))).fetchone()[0]
    return result


def mart_exists():
    with _connect() as conn:
        return all(conn.execute('SELECT to_regclass(%s)',(f'mart.{name}',)).fetchone()[0] for name in TABLES)


def default_analysis():
    pointer=ROOT/'reports/runtime/active.json'
    if pointer.is_file():
        path=(ROOT/json_read(pointer)['analysis']).resolve()
        if not path.is_relative_to(ROOT/'reports'):
            raise RuntimeError('分析指针超出本地报告目录。')
        return path
    return ROOT/'reports/p3/analysis.json'


def readiness(output=ROOT/'reports/runtime',source=ROOT/'data/raw',isolated=False):
    status=db_status()
    if 'PostgreSQL 16.' not in status['server']:
        raise RuntimeError('需要PostgreSQL 16。')
    counts=raw_state()
    if any(n is None or n==0 for n in counts.values()) or not mart_exists():
        raise RuntimeError('数据仓库未初始化完成，请先运行 init；不会以Docker已启动代替系统就绪。')
    manifest_path=output/'manifest.json'
    manifest=json_read(manifest_path) if manifest_path.is_file() else None
    analysis_path=Path(manifest['analysis_path']) if manifest else default_analysis()
    if not analysis_path.is_file():
        raise RuntimeError('经营分析结果不存在，请运行 init 或 refresh。')
    if manifest:
        if manifest['source_sha256']!=source_hashes(source):
            raise RuntimeError('源CSV发生变化，停止启动；请在新空数据库验证更新，不自动覆盖旧raw。')
        if manifest['warehouse_sql_sha256']!={name:digest(ROOT/'sql'/name) for name in SCRIPTS}:
            raise RuntimeError('仓库SQL已变化；请备份并运行 refresh，不自动重建。')
        if manifest['analysis_code_sha256']!=digest(ROOT/'src/retailscope/diagnostics.py'):
            raise RuntimeError('统计计算代码已变化，请运行 refresh 生成新版本快照。')
        if manifest['raw']!=snapshot_raw() or manifest['mart']!=snapshot_mart():
            raise RuntimeError('数据库内容与上次初始化/更新不一致，请核对后运行 refresh。')
    validate_analysis(json_read(analysis_path))
    return {'ready':True,'database':status,'raw_rows':counts,'analysis_path':str(analysis_path),
            'findings':len(json_read(analysis_path)['findings'])}


def initialize(output=ROOT/'reports/runtime',source=ROOT/'data/raw',isolated=False,refresh=False):
    output,source=Path(output).resolve(),Path(source).resolve()
    output.mkdir(parents=True,exist_ok=True)
    # Repeated init is a read-only check; it does not regenerate an otherwise valid report.
    if (output/'manifest.json').is_file() and not refresh:
        result=readiness(output,source,isolated)
        result.update(skipped_existing=True)
        return result
    run=output/'runs'/datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%d-%H%M%S-%f')
    run.mkdir(parents=True,exist_ok=False)
    save({'status':'running','action':'refresh' if refresh else 'init'},run/'status.json')
    download=download_data(source,run/'download_manifest.json')
    audit=audit_all(source)
    audit['relational_quality']=audit_relations(source)
    if audit['has_blocking_issues']:
        raise RuntimeError('真实CSV审计未通过；未执行数据替换。')
    save(audit,run/'raw_quality.json')
    state=raw_state()
    any_rows=any((n or 0)>0 for n in state.values())
    if any_rows:
        expected={row['table']:row['row_count'] for row in audit['tables']}
        if state!=expected:
            raise RuntimeError('已有raw与CSV不一致，拒绝覆盖。请保留旧库并在新空库初始化。')
        imported=False
    else:
        init_db(ROOT/'sql/00_raw.sql')
        save(load_raw(source),run/'import.json')
        imported=True
    warehouse_present=mart_exists()
    if not warehouse_present:
        with _connect() as conn:
            existing=conn.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='mart'").fetchone()[0]
        if existing and not refresh:
            raise RuntimeError('发现部分mart对象，拒绝隐式重建；请核查后运行 refresh。')
    if refresh or not warehouse_present:
        build_warehouse(ROOT/'sql')
    validation=validate_pandas(source,run/'pandas_reconciliation.json')
    raw,mart=snapshot_raw(),snapshot_mart()
    exported=export_results(run/'p1')
    save(basic_relational_quality(),run/'db_quality.json')
    accepted=ROOT/'reports/p3/analysis.json'
    reuse=False
    if not isolated and not refresh and accepted.is_file():
        try:
            validate_analysis(json_read(accepted))
            reuse=True
        except RuntimeError:
            pass
    if reuse:
        analysis_path=accepted
    else:
        analysis_path=run/'p3/analysis.json'
        run_analysis(run/'p3',run/'P3_BUSINESS_REPORT.md')
        validate_analysis(json_read(analysis_path))
    manifest={'database':db_status(),'raw':raw,'mart':mart,'source_sha256':source_hashes(source),
              'analysis_path':str(analysis_path),'analysis_code_sha256':digest(ROOT/'src/retailscope/diagnostics.py'),
              'warehouse_sql_sha256':{name:digest(ROOT/'sql'/name) for name in SCRIPTS},
              'run_dir':str(run),'source_path':str(source),'imported':imported,'built_warehouse':refresh or not warehouse_present,
              'reused_analysis':reuse,'independent_pandas_passed':validation['passed']}
    save(manifest,output/'manifest.json')
    save({'status':'passed','imported':imported,'built_warehouse':manifest['built_warehouse'],'reused_analysis':reuse},run/'status.json')
    if not isolated:
        save_if_absent(download,ROOT/'reports/download_manifest.json')
        save_if_absent(audit,ROOT/'reports/raw_quality.json')
        for name,rows in exported.items():
            save_if_absent(rows,ROOT/'reports/p1'/f'{name}.json')
        save_if_absent({'status':'passed','started_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
            'idempotent':None,'raw_unchanged':True,'note':'首装完成独立Pandas对账；未宣称已执行两次建仓验收。'},ROOT/'reports/p1/run.json')
        save_if_absent(validation,ROOT/'reports/p1/pandas_reconciliation.json')
        if analysis_path!=accepted:
            save({'analysis':str(analysis_path.relative_to(ROOT)),
                  'report':str((run/'P3_BUSINESS_REPORT.md').relative_to(ROOT))},ROOT/'reports/runtime/active.json')
    return {'ready':True,'skipped_existing':False,'imported':imported,'built_warehouse':manifest['built_warehouse'],
            'analysis_path':str(analysis_path),'run_dir':str(run),'findings':len(json_read(analysis_path)['findings'])}


def main(argv=None):
    p=argparse.ArgumentParser(description='RetailScope安全初始化与就绪检查')
    p.add_argument('action',choices=['init','check','refresh'])
    p.add_argument('--output',type=Path,default=ROOT/'reports/runtime')
    p.add_argument('--source',type=Path,default=ROOT/'data/raw')
    p.add_argument('--isolated',action='store_true',help='不写入公共证据路径或当前快照指针，用于隔离复现')
    args=p.parse_args(argv)
    load_dotenv(ROOT/'.env')
    try:
        result=readiness(args.output,args.source,args.isolated) if args.action=='check' else initialize(args.output,args.source,args.isolated,args.action=='refresh')
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except Exception as exc:
        # Underlying driver messages may include URLs. Print only our curated messages.
        message=str(exc) if isinstance(exc,(RuntimeError,ValueError)) else f'运行失败（{type(exc).__name__}）；请检查依赖、数据库和本地输入。'
        print(message,file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
