"""P3 descriptive diagnostics. No warehouse writes, forecasting or causal estimates."""
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from scipy import stats
from sqlalchemy import text

from .bi.data import ROOT, engine

MIN_MONTH_ORDERS=100
MIN_INFERENCE_N=30
MIN_MAD_MONTHS=12
BOOTSTRAP_REPS=2000
SEED=20261113
QUERY_NAMES=('context','kpis','monthly','categories','regions','association_orders','rfm_users','cohort')


def clean(value):
    """JSON-safe, exact money strings; missing numbers are NULL, never NaN."""
    if isinstance(value,dict):
        return {str(k):clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):
        return [clean(v) for v in value]
    if isinstance(value,Decimal):
        return str(value)
    if isinstance(value,(datetime,pd.Timestamp)) or hasattr(value,'isoformat'):
        return value.isoformat()
    if isinstance(value,np.generic):
        return clean(value.item())
    if value is None or value is pd.NA or (isinstance(value,float) and not np.isfinite(value)):
        return None
    return value


def save(value,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(clean(value),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')


def load_sources():
    result={}
    with engine().connect().execution_options(isolation_level='REPEATABLE READ') as conn:
        for name in QUERY_NAMES:
            sql=(ROOT/'sql/p3'/f'{name}.sql').read_text(encoding='utf-8')
            result[name]=pd.read_sql_query(text(sql),conn,coerce_float=False)
    return result


def wilson_interval(successes,n,confidence=.95):
    if n<=0 or successes<0 or successes>n:
        return (None,None)
    z=stats.norm.ppf((1+confidence)/2)
    p=successes/n
    denominator=1+z*z/n
    center=(p+z*z/(2*n))/denominator
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/denominator
    return (max(0,float(center-half)),min(1,float(center+half)))


def difference_intervals(a,b,confidence=.95):
    """Secondary working-independent-order intervals. Primary CIs are customer-cluster bootstrap."""
    a,b=np.asarray(a,dtype=float),np.asarray(b,dtype=float)
    a,b=a[np.isfinite(a)],b[np.isfinite(b)]
    if min(len(a),len(b))<MIN_INFERENCE_N:
        return {'mean_difference':float(a.mean()-b.mean()) if len(a) and len(b) else None,
                'welch_ci':None,'status':'样本不足，不计算推断区间'}
    va,vb=a.var(ddof=1)/len(a),b.var(ddof=1)/len(b)
    difference=float(a.mean()-b.mean())
    if va+vb==0:
        return {'mean_difference':difference,'welch_ci':[difference,difference],'status':'两组均无样本变异，区间退化'}
    df=(va+vb)**2/(va*va/(len(a)-1)+vb*vb/(len(b)-1))
    half=stats.t.ppf((1+confidence)/2,df)*np.sqrt(va+vb)
    return {'mean_difference':difference,'welch_ci':[float(difference-half),float(difference+half)],'welch_df':float(df),'status':'大样本工作独立近似；未作为主推断区间'}


def proportion_difference(xa,na,xb,nb):
    if min(na,nb)<MIN_INFERENCE_N:
        return {'difference':xa/na-xb/nb if na and nb else None,'newcombe_ci':None}
    pa,pb=xa/na,xb/nb
    la,ua=wilson_interval(xa,na)
    lb,ub=wilson_interval(xb,nb)
    d=pa-pb
    return {'difference':d,'newcombe_ci':[max(-1,d-np.hypot(pa-la,ub-pb)),min(1,d+np.hypot(ua-pa,pb-lb))]}


def cluster_bootstrap(frame,reps=BOOTSTRAP_REPS,seed=SEED):
    """Resample unique users; all their late/on-time order contributions travel together."""
    if reps<100:
        raise ValueError('至少需要100次重采样。')
    valid=frame.dropna(subset=['customer_unique_id','is_late','review_mean','latest_review_score']).copy()
    if valid.empty:
        return {'status':'无有效样本','mean_ci':None,'low_rate_ci':None}
    valid['review_mean']=valid.review_mean.astype(float)
    for late,label in ((True,'late'),(False,'on_time')):
        mask=valid.is_late.eq(late)
        valid[f'{label}_n']=mask.astype(int)
        valid[f'{label}_score']=valid.review_mean.where(mask,0)
        valid[f'{label}_low']=(valid.latest_review_score.astype(int).le(2)&mask).astype(int)
    cols=['late_n','late_score','late_low','on_time_n','on_time_score','on_time_low']
    grouped=valid.groupby('customer_unique_id',sort=True)[cols].sum()
    counts=grouped[['late_n','on_time_n']].sum()
    if min(counts)<MIN_INFERENCE_N or len(grouped)<MIN_INFERENCE_N:
        return {'status':'样本不足，不计算聚类区间','users':len(grouped),'mean_ci':None,'low_rate_ci':None}
    array=grouped.to_numpy(dtype=float)
    rng=np.random.default_rng(seed)
    draws=[]
    # Batch size bounds memory independently of the number of bootstrap replications.
    for start in range(0,reps,20):
        indices=rng.integers(0,len(array),size=(min(20,reps-start),len(array)))
        sums=array[indices].sum(axis=1)
        good=(sums[:,0]>0)&(sums[:,3]>0)
        sums=sums[good]
        draws.extend(np.column_stack((sums[:,1]/sums[:,0]-sums[:,4]/sums[:,3],
                                      sums[:,2]/sums[:,0]-sums[:,5]/sums[:,3])).tolist())
    draws=np.asarray(draws)
    if len(draws)<.99*reps:
        return {'status':'有效重采样不足','mean_ci':None,'low_rate_ci':None}
    interval=np.quantile(draws,[.025,.975],axis=0)
    return {'status':'通过','users':len(grouped),'replications':len(draws),'seed':seed,
            'mean_ci':interval[:,0].tolist(),'low_rate_ci':interval[:,1].tolist(),
            'method':'customer_unique_id整群percentile bootstrap，条件于历史样本，95%区间'}


def association_analysis(orders,reps=BOOTSTRAP_REPS):
    if not orders.order_id.is_unique:
        raise ValueError('关联分析要求一订单一行。')
    valid=orders.dropna(subset=['is_late','review_mean','latest_review_score','customer_unique_id']).copy()
    if not valid.empty and not (valid.review_mean.astype(float).between(1,5).all() and valid.latest_review_score.astype(float).between(1,5).all()):
        raise ValueError('评价评分必须在1–5之间。')
    groups=[]
    for is_late,label in ((False,'未逾期'),(True,'逾期')):
        group=valid[valid.is_late.eq(is_late)]
        n=len(group)
        low=int(group.latest_review_score.astype(int).le(2).sum())
        groups.append({'group':label,'n':n,'users':int(group.customer_unique_id.nunique()),
                       'mean_score':float(group.review_mean.astype(float).mean()) if n else None,
                       'low_scores':low,'low_rate':low/n if n else None,
                       'wilson_ci':list(wilson_interval(low,n)) if n>=MIN_INFERENCE_N else None})
    late=valid[valid.is_late.eq(True)].review_mean.astype(float)
    on_time=valid[valid.is_late.eq(False)].review_mean.astype(float)
    differences=difference_intervals(late,on_time)
    differences.update(proportion_difference(groups[1]['low_scores'],groups[1]['n'],groups[0]['low_scores'],groups[0]['n']))
    return {'eligible_orders':len(orders),'valid_orders':len(valid),'excluded_orders':len(orders)-len(valid),
            'assumption_checks':{'one_order_one_row':True,'score_within_1_5':True,
                'both_groups_at_least_30':all(g['n']>=MIN_INFERENCE_N for g in groups),
                'largest_user_cluster':int(valid.groupby('customer_unique_id').size().max()) if len(valid) else 0,
                'users_in_both_groups':int(valid.groupby('customer_unique_id').is_late.nunique().eq(2).sum())},
            'missing_late_judgment':int(orders.is_late.isna().sum()),
            'missing_review':int(orders.review_mean.isna().sum()),
            'missing_user':int(orders.customer_unique_id.isna().sum()),
            'repeated_user_orders':len(valid)-int(valid.customer_unique_id.nunique()),
            'groups':groups,'differences_late_minus_on_time':differences,
            'cluster_bootstrap':cluster_bootstrap(valid,reps),
            'limitations':'组间差异为描述性关联；评价是有界有序评分；存在评价缺失、地区/类目/时间混杂与同用户相关。聚类区间不能修复选择偏差或证明因果。缺失项可重叠，不能相加作为排除总数。'}


def trend_analysis(monthly):
    frame=monthly.copy().sort_values('month_start').reset_index(drop=True)
    frame['month_start']=pd.to_datetime(frame.month_start)
    lookup=frame.set_index('month_start')
    rows=[]
    for _,row in frame.iterrows():
        result={'month':row.month_start.date(),'orders':int(row.orders),'merchandise':row.merchandise,
                'complete':bool(row.is_complete),'adequate_sample':int(row.orders)>=MIN_MONTH_ORDERS}
        for lag,label in ((1,'mom'),(12,'yoy')):
            base_month=row.month_start-pd.DateOffset(months=lag)
            base=lookup.loc[base_month] if base_month in lookup.index else None
            valid=bool(row.is_complete and row.orders>=MIN_MONTH_ORDERS and base is not None and base.is_complete and base.orders>=MIN_MONTH_ORDERS and base.merchandise>0)
            result[f'{label}_reason']='可比较' if valid else '月份不完整、样本不足或缺少合格比较基线'
            result[f'{label}_merchandise']=float(row.merchandise/base.merchandise-1) if valid else None
            result[f'{label}_orders']=float(row.orders/base.orders-1) if valid else None
        rows.append(result)
    thresholds={}
    for field in ('merchandise','orders'):
        usable=[r for r in rows if r[f'mom_{field}'] is not None and r[f'mom_{field}']>-1]
        values=np.log1p([r[f'mom_{field}'] for r in usable])
        median=float(np.median(values)) if len(values) else None
        mad=float(np.median(np.abs(values-median))) if len(values) else None
        can_flag=len(values)>=MIN_MAD_MONTHS and mad is not None and mad>1e-12
        thresholds[field]={'usable_pairs':len(values),'median_log_growth':median,'mad_log_growth':mad,'available':can_flag}
        for r in rows:
            growth=r[f'mom_{field}']
            score=.6744897501960817*(np.log1p(growth)-median)/mad if can_flag and growth is not None and growth>-1 else None
            r[f'{field}_robust_z']=float(score) if score is not None else None
            r[f'{field}_flag']=bool(abs(score)>3.5) if score is not None else None
    return {'months':rows,'mad_reference':thresholds,'rules':{'min_orders_per_month':MIN_MONTH_ORDERS,'min_mad_pairs':MIN_MAD_MONTHS,'absolute_modified_z_threshold':3.5},
            'interpretation':'对数环比的全历史中位数/MAD回顾筛查；不删除异常，不作预测或季节调整；无合格基线不输出增长率。100单门槛是诊断精度保护规则，不是数据覆盖完整性的证明。'}


def concentration_analysis(categories):
    frame=categories.copy().sort_values(['merchandise','category'],ascending=[False,True])
    total=sum(frame.merchandise,Decimal(0))
    if not len(frame) or total<=0:
        return {'available':False,'hhi':None,'top5_share':None,'top10_share':None,'rows':[]}
    shares=np.array([float(v/total) for v in frame.merchandise])
    frame['small_sample']=frame.orders<MIN_MONTH_ORDERS
    frame['cumulative_contribution']=np.cumsum(shares)
    return {'available':True,'categories':len(frame),'total_merchandise':total,'hhi':float(np.square(shares).sum()),
            'hhi_10000':float(np.square(shares).sum()*10000),'top5_share':float(shares[:5].sum()),
            'top10_share':float(shares[:10].sum()),'categories_to_80pct':int(np.searchsorted(np.cumsum(shares),.8)+1),
            'rows':frame.to_dict('records'),'interpretation':'HHI度量本样本商品类目金额结构，非市场垄断度；跨类目订单数不相加。少于100个类目内订单标为小样本。'}


def region_analysis(regions):
    frame=regions.copy()
    result=[]
    for _,r in frame.iterrows():
        record=r.to_dict()
        record['small_sample']=int(r.orders)<MIN_MONTH_ORDERS
        record['late_rate_ci']=list(wilson_interval(int(r.late_orders),int(r.late_n))) if r.late_n>=MIN_INFERENCE_N else None
        result.append(record)
    return result


def user_analysis(users,cohort):
    if users.empty:
        return {'users':0,'segments':[],'repeat_comparison':[],'single_purchase_share':None}
    frame=users.copy()
    total=sum(frame.monetary.dropna(),Decimal(0))
    segments=[]
    for segment,g in frame.groupby('segment',sort=True):
        amount=sum(g.monetary.dropna(),Decimal(0))
        segments.append({'segment':segment,'users':len(g),'user_share':len(g)/len(frame),'merchandise':amount,
                         'contribution':float(amount/total) if total else None,
                         'median_frequency':float(g.frequency.median()),'median_recency':float(g.recency.median())})
    comparisons=[]
    frame['observed_exposure_days']=(pd.to_datetime(frame.rfm_reference_date)-pd.to_datetime(frame.cohort_month)).dt.days
    for is_repeat,label in ((False,'一次购买'),(True,'复购')):
        g=frame[frame.frequency.ge(2).eq(is_repeat)]
        amount=sum(g.monetary.dropna(),Decimal(0))
        comparisons.append({'group':label,'users':len(g),'orders':int(g.frequency.sum()),'merchandise':amount,
                            'mean_user_merchandise':float(amount/len(g)) if len(g) else None,
                            'median_observed_month_exposure_days':float(g.observed_exposure_days.median()) if len(g) else None})
    observed=cohort[cohort.is_observed & cohort.month_age.eq(1) & ~cohort.cohort_left_truncated]
    return {'users':len(frame),'single_purchase_users':int(frame.frequency.eq(1).sum()),
            'single_purchase_share':float(frame.frequency.eq(1).mean()),'segments':segments,'repeat_comparison':comparisons,
            'observed_m1_cohorts':len(observed),'m1_weighted_retention':float(observed.active_users.sum()/observed.new_users.sum()) if len(observed) else None,
            'm1_active_users_total':int(observed.active_users.sum()),'m1_baseline_users_total':int(observed.new_users.sum()),
            'unobserved_cohort_cells':int((~cohort.is_observed).sum()),
            'interpretation':'用户分层为P1固定规则。复购组累计金额较高部分由分组定义决定；首购月到基准日仅是观测机会代理，不能作获客时间。首cohort左截断及未观察Cohort单元保持原样。'}


def findings_from_result(result):
    context=result['context']
    full=f"{context['first_purchase']} 至 {context['last_purchase']}（有效购买订单）"
    cards=[]
    def add(identifier,title,text_result,sources,scope,sample,method,limitations,suggestion,statistics):
        cards.append(dict(id=identifier,title=title,result=text_result,source_sql=sources,scope=scope,
                          sample=sample,method=method,limitations=limitations,suggestion=suggestion,statistics=statistics))
    trend=result['trend']
    comparable=[r for r in trend['months'] if r['mom_merchandise'] is not None]
    if comparable:
        last=comparable[-1]
        base=pd.Timestamp(last['month'])-pd.DateOffset(months=1)
        prior=next(r for r in trend['months'] if pd.Timestamp(r['month'])==base)
        add('F01','完整月商品金额与订单变化',
            f"{str(last['month'])[:7]} 商品金额 BRL {Decimal(str(last['merchandise'])):,.2f}，环比 {last['mom_merchandise']:+.2%}；有效订单 {last['orders']:,} 单，环比 {last['mom_orders']:+.2%}。",
            ['P3_MONTHLY'],f"{base.date()} 至 {(pd.Timestamp(last['month'])+pd.offsets.MonthEnd()).date()}",
            {'current_orders':last['orders'],'baseline_orders':prior['orders'],'denominator':'对应上月金额或有效订单数'},
            '仅完整日历月、当月及上月均至少100单；相邻月环比',
            '历史样本变化不代表未来走势；可能受季节、样本覆盖及品类结构影响，未控制混杂。',
            '后续核对活动与类目结构；若提出促销调整，使用对照试验验证增量效果。',last)
    flagged=[r for r in trend['months'] if r['merchandise_flag'] or r['orders_flag']]
    references=trend['mad_reference']
    available=all(r['available'] for r in references.values())
    add('F02','稳健异常月份回顾筛查',
        (f"金额/订单对数环比筛查共标记 {len(flagged)} 个月："+('、'.join(str(r['month'])[:7] for r in flagged) or '无')+'。') if available else '有效比较月份不足或MAD为零，未作异常判断。',
        ['P3_MONTHLY'],full,{'usable_pairs':references,'denominator':'具备完整月和样本门槛的相邻月份对'},
        'modified Z=0.67449×(对数环比−中位数)/MAD；绝对值>3.5提示，至少12对比较',
        '回顾性经验阈值，不是显著性检验；没有季节调整，也不证明错误数据或异常经营原因。',
        '逐一核对被提示月份的记录覆盖、促销和履约情况；保留原数据后再决定是否调查。',{'flagged_months':flagged,'references':references})
    concentration=result['concentration']
    if concentration['available']:
        add('F03','商品类目贡献集中度',
            f"TOP5 类目贡献 {concentration['top5_share']:.2%}，TOP10 贡献 {concentration['top10_share']:.2%}；HHI={concentration['hhi']:.4f}（万分制 {concentration['hhi_10000']:.2f}）；{concentration['categories_to_80pct']} 个类目覆盖80%商品金额。",
            ['P3_CATEGORIES'],full,{'categories':concentration['categories'],'merchandise':concentration['total_merchandise'],'denominator':'全部有效商品明细金额'},
            '按类目商品金额份额计算HHI=Σshare²及帕累托累计贡献',
            '描述样本商品结构，不是全市场集中度；类目订单数存在交叉，不能相加。缺类目商品仍进入unknown组。',
            '针对高贡献类目核验供货和履约容量；小类目先补充样本，避免仅因金额低就削减投入。',concentration)
    if result['regions']:
        top=result['regions'][0]
        small=sum(r['small_sample'] for r in result['regions'])
        add('F04','地区规模与履约的联合观察',
            f"{top['state']} 有效订单 {top['orders']:,} 单，商品金额 BRL {Decimal(str(top['merchandise'])):,.2f}；平均配送 {float(top['delivery_days']):.2f} 天，逾期率 {float(top['late_rate']):.2%}。{small} 个州少于100单，已标注小样本。",
            ['P3_REGIONS'],full,{'orders':top['orders'],'delivery_n':top['delivery_n'],'late_n':top['late_n'],'denominator':'订单客户州；配送/逾期分别使用有效日期分母'},
            '订单级州汇总；样本数与Wilson工作独立近似区间并列展示',
            '地区客户、类目与配送距离不同，不能直接按原始均值评价物流团队；小州不作稳定排名判断。',
            '在同类目、相近线路和承运商中进一步分层；用前瞻性试点验证改进方案。',top)
    association=result['association']
    a,b=association['groups'][1],association['groups'][0]
    bootstrap=association['cluster_bootstrap']
    difference=association['differences_late_minus_on_time']
    if a['n'] and b['n']:
        ci=bootstrap['mean_ci']
        lowci=bootstrap['low_rate_ci']
        ci_text=f"[{ci[0]:.4f}, {ci[1]:.4f}]" if ci else '样本不足'
        low_text=f"[{lowci[0]*100:.2f}, {lowci[1]*100:.2f}] 个百分点" if lowci else '样本不足'
        add('F05','逾期与评价存在描述性差异',
            f"逾期 {a['n']:,} 单均分 {a['mean_score']:.4f}，未逾期 {b['n']:,} 单均分 {b['mean_score']:.4f}；差值（逾期−未逾期）{difference['mean_difference']:.4f} 分，用户聚类95%区间 {ci_text}。低评分率分别 {a['low_rate']:.2%} 与 {b['low_rate']:.2%}，差值95%区间 {low_text}。",
            ['P3_ASSOCIATION'],full,{'groups':association['groups'],'valid_orders':association['valid_orders'],'excluded_orders':association['excluded_orders'],'denominator':'有有效逾期判断、订单评价及唯一用户标识的有效订单'},
            '用户整群percentile bootstrap 2000次，固定种子；Welch与Newcombe区间作工作独立近似对照',
            association['limitations'],
            '优先核查逾期与低评分集中的线路/类目；沟通或补偿方案必须前瞻试验验证，不把差异当成延迟的因果效应。',association)
    users=result['users']
    if users['users']:
        repeat=next(r for r in users['repeat_comparison'] if r['group']=='复购')
        total=sum(Decimal(str(r['merchandise'])) for r in users['repeat_comparison'])
        add('F06','一次购买用户占多数，复购结构需结合窗口解读',
            f"一次购买用户 {users['single_purchase_users']:,} 人，占 {users['single_purchase_share']:.4%}；复购用户 {repeat['users']:,} 人，累计商品金额 BRL {Decimal(str(repeat['merchandise'])):,.2f}，占全部用户金额 {float(Decimal(str(repeat['merchandise']))/total):.2%}。",
            ['P3_RFM_USERS'],full,{'users':users['users'],'repeat_users':repeat['users'],'denominator':'P1全观察期内至少一次有效购买的唯一用户'},
            '复用P1 RFM规则，分别汇总人数、金额及观测首购月到基准日的机会代理',
            users['interpretation'],
            '按固定进入月份和统一回购观察长度复核；召回或服务方案作为待验证假设，不把分层标签解释为实验效果。',users)
        add('F07','留存分析必须保留不可观察月份',
            f"{users['observed_m1_cohorts']} 个非左截断cohort具备完整次月观察，其M1回购活跃人数 {users['m1_active_users_total']:,} / 首购用户 {users['m1_baseline_users_total']:,}，加权留存为 {users['m1_weighted_retention']:.4%}；{users['unobserved_cohort_cells']} 个cohort/月龄单元不可观察，仍为NULL。",
            ['P3_COHORT'],f"完整目标月 [{context['first_complete_month']}, {context['observation_end_exclusive']})",
            {'eligible_cohorts':users['observed_m1_cohorts'],'active_users':users['m1_active_users_total'],
             'baseline_users':users['m1_baseline_users_total'],'denominator':'合格cohort首购人数之和；分子为其完整次月活跃人数之和'},
            'P1购买活跃留存、同月去重，M1汇总排除首cohort左截断与不完整目标月',
            '汇总留存混合不同进入月份；不是连续订阅留存，不能从NA推断零回购。',
            '后续按统一30/60/90天窗口跟踪新进入用户，并为服务实验保留未干预对照组。',{'observed_m1_cohorts':users['observed_m1_cohorts'],'m1_weighted_retention':users['m1_weighted_retention'],'unobserved_cells':users['unobserved_cohort_cells']})
    return cards


def markdown_report(result):
    context=result['context']
    lines=['# RetailScope P3 经营诊断与统计分析报告','',
           f"生成时间：{result['generated_at']}。数据：Olist / Kaggle，CC BY-NC-SA 4.0。",
           f"有效购买研究范围：{context['first_purchase']} 至 {context['last_purchase']}；固定P1 delivered口径，BRL金额。",
           '完整月趋势与全样本结构/关联分析的窗口不同，逐条标明。所有发现均为历史描述与待验证假设，不是未来预测或因果结论。','',
           '## 核心经营指标','',
           '| 指标 | SQL实际值 |','|---|---|']
    for key,val in result['kpis'].items():
        lines.append(f'| {key} | {val} |')
    for finding in result['findings']:
        lines += ['',f"## {finding['id']} {finding['title']}",'',finding['result'],'',
                  f"- 观察范围：{finding['scope']}",f"- 样本与分母：{json.dumps(clean(finding['sample']),ensure_ascii=False)}",
                  f"- SQL来源：{', '.join(finding['source_sql'])}，对应sql/p3中的只读查询。",
                  f"- 统计方法：{finding['method']}",f"- 局限与可能解释：{finding['limitations']}",
                  f"- 待验证建议：{finding['suggestion']}"]
    lines += ['','## 方法、数据局限与复现','',
              '详细方法、预设阈值、缺失与CI解释见docs/P3_ANALYSIS_METHODS.md。没有成本、完整退款或曝光数据，不能推断利润、ROI及转化率。',
              '独立复核：tests/test_p3.py；SQL源及其SHA-256、分析配置、输入查询哈希、完整统计结果见reports/p3/analysis.json与sql_results目录。',
              '运行：python scripts/run_p3.py。此命令只读现有仓库，生成结构化JSON、结果CSV与本Markdown；不执行P0/P1重建。','']
    return '\n'.join(lines)


def run_analysis(output=ROOT/'reports/p3',report_path=None):
    sources=load_sources()
    context=sources['context'].iloc[0].to_dict()
    result={'schema_version':1,'generated_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds'),
            'context':context,'kpis':sources['kpis'].iloc[0].to_dict(),
            'config':{'min_month_orders':MIN_MONTH_ORDERS,'min_inference_n':MIN_INFERENCE_N,
                      'min_mad_pairs':MIN_MAD_MONTHS,'bootstrap_reps':BOOTSTRAP_REPS,'seed':SEED},
            'sql_sha256':{name:hashlib.sha256((ROOT/'sql/p3'/f'{name}.sql').read_bytes()).hexdigest() for name in QUERY_NAMES},
            'source_queries':{name:('P3_ASSOCIATION' if name=='association_orders' else f'P3_{name.upper()}') for name in QUERY_NAMES},
            'source_rows':{name:len(frame) for name,frame in sources.items()}}
    result['trend']=trend_analysis(sources['monthly'])
    result['concentration']=concentration_analysis(sources['categories'])
    result['regions']=region_analysis(sources['regions'])
    result['association']=association_analysis(sources['association_orders'])
    result['users']=user_analysis(sources['rfm_users'],sources['cohort'])
    result['findings']=findings_from_result(result)
    result=clean(result)
    for name,frame in sources.items():
        folder=output/'sql_results'
        folder.mkdir(parents=True,exist_ok=True)
        path=folder/f'{name}.csv'
        frame.to_csv(path,index=False,na_rep='NA',encoding='utf-8-sig')
        result.setdefault('input_csv_sha256',{})[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    save(result,output/'analysis.json')
    pd.DataFrame(result['trend']['months']).to_csv(output/'monthly_diagnostics.csv',index=False,na_rep='NA',encoding='utf-8-sig')
    destination=Path(report_path) if report_path is not None else ROOT/'docs/P3_BUSINESS_REPORT.md'
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(markdown_report(result),encoding='utf-8')
    return result
