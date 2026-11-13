"""Three read-only adapters over the accepted P1/P2 SQL; no new statistical model."""
import csv
from datetime import timedelta
from io import StringIO
from typing import Annotated,Literal

from fastapi import APIRouter,Depends,HTTPException,Query
from fastapi.responses import Response
from sqlalchemy import text

from .queries import database,rows,query,scope_params,STATES
from retailscope.bi.data import FIXED,Filters

router=APIRouter(prefix='/api/analysis')
Page=Literal['users','products','delivery']
TABLES={
    'users':{'segments':'rfm','frequency':'frequency','summary':'repurchase','cohort':'cohort','new_users':'new_users'},
    'products':{'kpis':'product_kpis','categories':'categories','monthly':'category_monthly'},
    'delivery':{'kpis':'overview','histogram':'delivery_histogram','reviews':'reviews','regions':'delivery_regions','association':'late_reviews'},
}
EMPTY_COLUMNS={
    'summary':['users','repeat_users','repeat_rate'],
    'segments':['segment','users','user_share','merchandise','contribution'],
    'frequency':['frequency','users','share'],
    'cohort':['cohort_month','month_age','target_month','new_users','cohort_left_truncated','is_observed','active_users','retention'],
    'new_users':['cohort_month','new_users'],
    'categories':['category','orders','items','merchandise','freight','contribution'],
    'monthly':['month_start','category','merchandise','items','orders'],
    'histogram':['day_start','orders'],'reviews':['score','orders'],
    'regions':['state','orders','delivery_days','delivery_n','late_rate','late_n'],
    'association':['delivery_group','orders','review_mean','low_score_rate','low_score_n','low_score_orders'],
}


def load_analysis(page,params,category=None):
    if page=='users' and (any(v is not None for v in params) or category is not None):
        raise HTTPException(422,'用户分层与留存采用固定全样本，不支持局部筛选。')
    with database().connect() as conn,conn.begin():
        bounds=rows(conn,text(FIXED['bounds']))[0]
        context=rows(conn,text(FIXED['context']))[0]
        if page=='users':
            result={'scope':{'mode':'fixed','start':context['first_purchase'],'end':context['last_purchase'],'state':None,'category':None},
                'metadata':{'context':context,'bounds':{'start':bounds['first_date'],'end':bounds['last_date']},
                    'read_only':True,'query_sources':list(TABLES[page].values())}}
            for name,sql_name in TABLES[page].items():result[name]=rows(conn,text(FIXED[sql_name]))
            return result
        from datetime import date
        first,last=date.fromisoformat(bounds['first_date']),date.fromisoformat(bounds['last_date'])
        start,end,state=params
        start,end=start or first,end or last
        if start>end:raise HTTPException(422,'开始日期不能晚于结束日期。')
        categories=[r['category'] for r in rows(conn,text(FIXED['category_options']))]
        if category is not None and category not in categories:
            raise HTTPException(422,'请选择已有的商品类目。')
        scope=Filters(start,end+timedelta(days=1),states=(state,) if state else (),categories=(category,) if category else ())
        result={'scope':{'mode':'filtered','start':start.isoformat(),'end':end.isoformat(),'state':state,'category':category},
            'metadata':{'context':context,'bounds':{'start':first.isoformat(),'end':last.isoformat()},
                'states':[r['state'] for r in rows(conn,text(FIXED['states'])) if r['state'] in STATES],
                'categories':categories,'read_only':True,'query_sources':list(TABLES[page].values())}}
        for name,sql_name in TABLES[page].items():result[name]=query(conn,sql_name,scope)
        if page=='delivery':
            # Expose the exact latest-score denominator, distinct from the order-mean denominator.
            from .queries import SCOPE,String,bindparam
            sql=SCOPE+"""SELECT CASE WHEN is_late THEN '逾期' ELSE '未逾期' END AS delivery_group,
                count(latest_review_score) AS low_score_n,
                count(*) FILTER (WHERE latest_review_score<=2) AS low_score_orders
                FROM eligible WHERE is_late IS NOT NULL AND review_mean IS NOT NULL GROUP BY is_late"""
            statement=text(sql).bindparams(bindparam('states',expanding=True,type_=String()),bindparam('categories',expanding=True,type_=String()))
            counts={r['delivery_group']:r for r in rows(conn,statement,scope.params())}
            result['association']=[{**r,**counts[r['delivery_group']]} for r in result['association']]
            result['metadata']['query_sources'].append('association_latest_score_denominators')
        return result


@router.get('/{page}')
def analysis(page:Page,params=Depends(scope_params),category:Annotated[str|None,Query(max_length=100)]=None):
    return load_analysis(page,params,category)


@router.get('/{page}/export')
def export_analysis(page:Page,table:Annotated[str,Query(max_length=30)],params=Depends(scope_params),
                    category:Annotated[str|None,Query(max_length=100)]=None):
    if table not in TABLES[page]:raise HTTPException(422,'不支持的导出结果。')
    result=load_analysis(page,params,category)
    records=result[table]
    columns=list(records[0]) if records else EMPTY_COLUMNS[table]
    scope=result['scope']
    scope_columns={f'scope_{key}':value if value is not None else 'ALL' for key,value in scope.items()}
    buffer=StringIO(newline='')
    writer=csv.DictWriter(buffer,fieldnames=[*scope_columns,*columns])
    writer.writeheader()
    for record in records:writer.writerow({**scope_columns,**record})
    return Response(content=('\ufeff'+buffer.getvalue()).encode('utf-8'),media_type='text/csv',
        headers={'Content-Disposition':f'attachment; filename="retailscope-{page}-{table}.csv"','Cache-Control':'no-store'})
