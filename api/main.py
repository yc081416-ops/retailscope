"""Overview and analytical HTTP entry point over accepted read-only SQL adapters."""
from contextlib import asynccontextmanager
from datetime import date,timedelta
from decimal import Decimal
from functools import lru_cache
from io import StringIO
import csv
import json
import logging
import os
from pathlib import Path
from typing import Annotated,Literal

from dotenv import load_dotenv
from fastapi import Depends,FastAPI,HTTPException,Query,Request
from fastapi.responses import JSONResponse,Response
from sqlalchemy import String,bindparam,create_engine,text
from sqlalchemy.engine import make_url

from retailscope.bi.data import SCOPE,FILTERED,FIXED,Filters

ROOT=Path(__file__).resolve().parents[1]
LOGGER=logging.getLogger('retailscope.api')
from .queries import database,scalar,rows,query,scope_params,STATES


@asynccontextmanager
async def lifespan(app):
    yield
    if database.cache_info().currsize:
        database().dispose()
        database.cache_clear()


app=FastAPI(title='RetailScope V2 · 经营总览',version='2.1.0',lifespan=lifespan)


async def database_error(request:Request,exc:Exception):
    # Connection errors can contain secrets: log the type, never the exception/URL.
    LOGGER.error('request_failed path=%s type=%s',request.url.path,type(exc).__name__)
    return JSONResponse(status_code=503,content={'detail':'暂时无法读取经营数据，请确认 PostgreSQL 已启动后重试。','code':'DATA_UNAVAILABLE'})


@app.middleware('http')
async def sanitize_unexpected_errors(request:Request,call_next):
    # Handle here rather than ServerErrorMiddleware, which re-raises to the server logger.
    try:
        return await call_next(request)
    except Exception as exc:
        return await database_error(request,exc)


def load_overview(params):
    start,end,state=params
    with database().connect() as conn,conn.begin():
        bounds=conn.execute(text(FIXED['bounds'])).mappings().one()
        first,last=bounds['first_date'],bounds['last_date']
        start,end=start or first,end or last
        if start>end:raise HTTPException(422,'开始日期不能晚于结束日期。')
        scope=Filters(start,end+timedelta(days=1),states=(state,) if state else ())
        context=rows(conn,text(FIXED['context']))[0]
        states=rows(conn,text(FIXED['states']))
        return {'scope':{'start':start.isoformat(),'end':end.isoformat(),'state':state},
            'metadata':{'source':'Olist · Kaggle / 版本 2','license':'CC BY-NC-SA 4.0',
                'bounds':{'start':first.isoformat(),'end':last.isoformat()},'context':context,
                'states':[r['state'] for r in states if r['state'] in STATES],
                'query_source':'retailscope.bi.data / SCOPE + overview, monthly, statuses, regions',
                'read_only':True},
            'kpis':query(conn,'overview',scope)[0],
            'monthly':query(conn,'monthly',scope),'statuses':query(conn,'statuses',scope),
            'regions':query(conn,'regions',scope)}


@app.get('/api/overview')
def overview(params=Depends(scope_params)):
    return load_overview(params)


@app.get('/api/overview/export')
def export(params=Depends(scope_params),table:Literal['kpis','monthly','statuses','regions']='monthly'):
    result=load_overview(params)
    records=[result[table]] if table=='kpis' else result[table]
    # Include the applied scope in the download, even when the selection has no rows.
    columns={'kpis':list(result['kpis']),'monthly':['month_start','orders','users','merchandise','is_complete'],
        'statuses':['status','orders'],'regions':['state','orders','merchandise','contribution']}[table]
    fields=['scope_start','scope_end','scope_state',*columns]
    stream=StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=fields)
    writer.writeheader()
    for row in records:
        writer.writerow({'scope_start':result['scope']['start'],'scope_end':result['scope']['end'],
            'scope_state':result['scope']['state'] or 'ALL',**row})
    return Response(content=('\ufeff'+stream.getvalue()).encode('utf-8'),media_type='text/csv',
        headers={'Content-Disposition':f'attachment; filename="retailscope-{table}.csv"','Cache-Control':'no-store'})


@app.get('/api/findings')
def findings():
    # Entry to accepted P3 facts only; there is no new diagnostic calculation or page.
    from retailscope.runtime import default_analysis
    data=json.loads(default_analysis().read_text(encoding='utf-8'))
    return {'scope':'P3 固定全样本；不随总览筛选联动','generated_at':data['generated_at'],
        'findings':data['findings']}


from .analysis import router as analysis_router
app.include_router(analysis_router)

from .evidence import router as evidence_router
app.include_router(evidence_router)
