import pandas as pd
import streamlit as st

from retailscope.bi.components import header, load_evidence, number, safe_page, table_download
from retailscope.bi.data import fetch, raw_counts


@safe_page
def render():
    header('DATA TRUST / 06','数据质量中心','将源数据特征、运行状态与真正的程序错误区分开来。')
    st.markdown('来源：[Olist Brazilian E-Commerce Dataset / Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) · CC BY-NC-SA 4.0 · 2016–2018历史样本。原始CSV保存在本地，不进入公开仓库。')
    counts = raw_counts()
    audit = load_evidence('reports/raw_quality.json')
    run = load_evidence('reports/p1/run.json')
    reconciliation = load_evidence('reports/p1/pandas_reconciliation.json')
    columns = st.columns(3)
    columns[0].metric('原始表',number(len(counts)))
    columns[1].metric('原始记录数',number(counts.rows.sum()))
    columns[2].metric('P1最近验收状态','通过' if run and run.get('status')=='passed' else '待核查')
    st.caption('原始记录数由当前数据库实时SQL查询；缺失、重复和关联详情来自已验收P0/P1审计快照，不冒充实时重审计。')
    with st.container(border=True):
        st.subheader('九张原始表 · 当前数据库行数')
        table_download(counts,'raw_table_counts','查看九表与导出')
        st.dataframe(counts,hide_index=True,width='stretch')
    if audit:
        rows,missing = [],[]
        for t in audit['tables']:
            rows.append({'table':t['table'],'audit_rows':t['row_count'],'full_duplicate_rows':t['duplicate_full_rows'],
                'unique_key_duplicates':t['duplicate_unique_key_rows'],'malformed_rows':t['malformed_rows'],
                'invalid_numeric':sum(t['invalid_numeric_by_column'].values()),'invalid_date':sum(t['invalid_date_by_column'].values())})
            missing.extend({'table':t['table'],'column':name,'missing_rows':n,'missing_rate':n/t['row_count']} for name,n in t['missing_by_column'].items())
        with st.container(border=True):
            st.subheader('缺失与重复 · 已验收源文件快照')
            st.warning('地理表整行重复、空评价文本及缺配送日期是保留的源数据特征，不自动判定为程序错误。review_id、唯一用户标识和邮编前缀不应被误设为原始表主键。')
            st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch')
            table_download(pd.DataFrame(rows),'raw_duplicates')
            st.dataframe(pd.DataFrame(missing),hide_index=True,width='stretch')
            table_download(pd.DataFrame(missing),'raw_missingness')
        relations = pd.DataFrame(list(audit.get('relational_quality',{}).get('checks',{}).items()),columns=['check','rows'])
        with st.container(border=True):
            st.subheader('关联异常与多明细现象 · P0快照')
            st.dataframe(relations,hide_index=True,width='stretch')
            table_download(relations,'relational_checks')
    else:
        st.warning('缺少P0质量审计文件；当前仅显示数据库查询结果。')
    with st.container(border=True):
        st.subheader('有效订单异常 · 当前仓库')
        current = fetch('quality').T.reset_index()
        current.columns = ['check','rows']
        st.dataframe(current,hide_index=True,width='stretch')
        table_download(current,'eligible_quality')
    with st.container(border=True):
        st.subheader('仓库构建与指标复核')
        if run:
            st.write(f"P1最近运行：{run.get('started_at')} · 两次构建一致：{run.get('idempotent')} · 原始数据保留：{run.get('raw_unchanged')}")
        if reconciliation:
            check_frame = pd.DataFrame(reconciliation['checks'])
            st.dataframe(check_frame,hide_index=True,width='stretch')
            table_download(check_frame,'warehouse_reconciliation')
    with st.expander('核心指标计算说明',expanded=True):
        st.markdown('''- 核心范围：delivered 且购买时间有效，日期采用购买时间。
- 商品金额 SUM(price)、运费 SUM(freight)、支付金额分别汇总；不代表利润。
- 用户按 customer_unique_id 去重；订单、支付、评价先预聚合，禁止多对多放大。
- 无支付仍保留商品金额；无商品保留订单并标记，不凭空补金额。
- RFM和Cohort使用P1全样本，未完整观察的目标月为NULL。
- 查看 docs/METRICS.md 和 docs/P1_DATA_MODEL.md 可复核完整口径。''')


render()
