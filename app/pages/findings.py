import pandas as pd
import streamlit as st

from retailscope.bi.components import header, load_evidence, safe_page, table_download
from retailscope.bi.data import ROOT, fetch
from retailscope.bi.diagnostic_page import render_diagnostics


@safe_page
def render():
    header('BUSINESS DIAGNOSTICS / 05','经营发现','真实经营统计、解释边界与可供后续验证的业务建议。')
    context = fetch('context').iloc[0]
    st.info(f'固定 P1 全样本范围：{context.first_purchase} 至 {context.last_purchase}。本页不随其他页面局部筛选联动；不包含预测、AI诊断或因果结论。')
    render_diagnostics()
    st.divider()
    st.subheader('P1 已验收描述性事实')
    evidence = load_evidence('reports/p1/run.json')
    if not evidence or evidence.get('status') != 'passed':
        st.warning('未找到已通过的P1运行证据，无法将发现标记为已验证。')
        return
    document = ROOT / 'docs/P1_ANALYSIS_FINDINGS.md'
    if not document.is_file():
        st.warning('P1发现文档不可用，请恢复已验收文档。')
        return
    facts = [p.strip() for p in document.read_text(encoding='utf-8').split('\n\n') if p.strip()[:1].isdigit() and '. ' in p]
    records = []
    for fact in facts:
        with st.container(border=True):
            st.markdown(fact)
            st.caption(f'适用范围：{context.first_purchase}—{context.last_purchase}，delivered有效购买订单；来源为P1已验收SQL与独立CSV对账。')
        records.append({'finding':fact,'scope_start':context.first_purchase,'scope_end':context.last_purchase,'evidence':'P1_ACCEPTANCE_REPORT / reports/p1/pandas_reconciliation.json'})
    table_download(pd.DataFrame(records),'verified_findings','事实来源索引与导出')
    st.caption('P1事实与P3统计结果并列保留；规则分层标签不表示已经验证的营销效果。')


render()
