"""Shared bounded read-only connections and parameterized accepted SQL adapters."""
from datetime import date
from decimal import Decimal
from functools import lru_cache
import os
from pathlib import Path
from typing import Annotated
from dotenv import load_dotenv
from fastapi import HTTPException,Query
from sqlalchemy import String,bindparam,create_engine,text
from sqlalchemy.engine import make_url
from retailscope.bi.data import SCOPE,FILTERED,FIXED,Filters
ROOT=Path(__file__).resolve().parents[1]
STATES=set('AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split())
@lru_cache(maxsize=1)
def database():
    load_dotenv(ROOT/'.env')
    url=make_url(os.environ['DATABASE_URL']).set(drivername='postgresql+psycopg')
    return create_engine(url,pool_pre_ping=True,pool_size=3,max_overflow=2,hide_parameters=True,
        isolation_level='REPEATABLE READ',connect_args={'connect_timeout':5,
        'options':'-c default_transaction_read_only=on -c statement_timeout=20000'})


def scalar(value):
    if isinstance(value,Decimal):return str(value)
    if isinstance(value,date):return value.isoformat()
    return value


def rows(conn,statement,params=None):
    return [{key:scalar(value) for key,value in row.items()}
        for row in conn.execute(statement,params or {}).mappings()]


def query(conn,name,scope):
    statement=text(SCOPE+FILTERED[name]).bindparams(bindparam('states',expanding=True,type_=String()),
        bindparam('categories',expanding=True,type_=String()))
    return rows(conn,statement,scope.params())


def scope_params(start:date|None=None,end:date|None=None,
                 state:Annotated[str|None,Query(pattern='^[A-Z]{2}$')]=None):
    if state is not None and state not in STATES:
        raise HTTPException(422,'请选择有效的巴西客户州。')
    if start and end and start>end:
        raise HTTPException(422,'开始日期不能晚于结束日期。')
    if end==date.max:
        raise HTTPException(422,'结束日期超出支持范围。')
    return start,end,state
