"""P3 presentation consumes generated results; never runs inference during UI interaction."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from .components import bar,chart,load_evidence,number,table_download
from .data import ROOT
from retailscope.diagnostics import markdown_report


def render_diagnostics():
    result=load_evidence('reports/p3/analysis.json')
    st.subheader('P3 经营诊断与统计分析')
    if not result:
        st.info('尚未生成P3统计结果。请运行 python scripts/run_p3.py；不会用示例发现替代。')
        return
    st.caption(f"结果生成时间：{result['generated_at']}。固定P1历史范围，不随其他页面局部筛选联动。")
    st.info('以下结果是历史样本的描述性诊断。置信区间不消除样本选择和混杂，也不代表未来预测或营销实验效果。')
    trend=pd.DataFrame(result['trend']['months'])
    comparable=trend.mom_merchandise.notna().sum()
    difference=result['association']['differences_late_minus_on_time']['mean_difference']
    for col,label,value in zip(st.columns(4),['有效订单','可比环比月份','逾期−未逾期均分差','核心发现'],
        [number(result['kpis']['orders']),number(comparable),number(difference,4),number(len(result['findings']))]):
        col.metric(label,value)
    st.download_button('下载 P3 经营诊断报告（Markdown）',markdown_report(result).encode('utf-8'),
        'RetailScope_P3_BUSINESS_REPORT.md','text/markdown',key='download_p3_report',on_click='ignore')
    for index,finding in enumerate(result['findings']):
        with st.expander(f"{finding['id']} · {finding['title']}",expanded=index<2):
            st.markdown(finding['result'])
            st.caption(f"范围：{finding['scope']} · 来源SQL：{', '.join(finding['source_sql'])}")
            st.markdown(f"**方法：** {finding['method']}")
            st.markdown(f"**解释边界：** {finding['limitations']}")
            st.markdown(f"**待验证建议：** {finding['suggestion']}")
            st.markdown('**样本与计算分母**')
            st.json(finding['sample'],expanded=False)
    with st.expander('查看完整月趋势与稳健异常筛查'):
        observed=trend[trend.complete].copy()
        observed['商品成交额']=observed.merchandise.astype(float)
        fig=go.Figure(go.Bar(x=observed.month,y=observed['商品成交额'],name='完整月商品金额 · BRL',marker_color='#2457D6'))
        flagged=observed[observed.merchandise_flag.eq(True)]
        fig.add_trace(go.Scatter(x=flagged.month,y=flagged['商品成交额'],mode='markers',marker=dict(color='#D18B28',size=12),name='MAD回顾提示'))
        fig.update_yaxes(title='商品成交额 · BRL',rangemode='tozero')
        chart(fig,'p3_monthly')
        st.caption('仅完整日历月绘图。表格保留不完整月，但不输出其环比/同比；少于100单、基线不足或MAD不可用时不判断异常。')
        table_download(trend,'p3_monthly_diagnostics')
    with st.expander('查看类目集中度、帕累托与地区样本'):
        categories=pd.DataFrame(result['concentration']['rows'])
        bar(categories.head(10).iloc[::-1],'merchandise','category','p3_category',{'merchandise':'商品成交额 · BRL','category':'类目'},True,420)
        table_download(categories,'p3_category_concentration')
        regions=pd.DataFrame(result['regions'])
        st.dataframe(regions,hide_index=True,width='stretch')
        table_download(regions,'p3_region_comparison')
        st.caption('小样本州和类目明确标记；HHI仅描述本数据商品类目结构，不套用市场垄断判断。')
    with st.expander('查看配送与评价差异及95%区间'):
        association=result['association']
        groups=pd.DataFrame(association['groups'])
        bar(groups,'group','mean_score','p3_association',{'group':'配送分组','mean_score':'订单等权评价均分'})
        display_groups=groups.rename(columns={'group':'配送分组','n':'订单数（单）','users':'去重用户数（人）',
            'mean_score':'订单等权评价均分','low_scores':'低评分订单数（单）','low_rate':'低评分订单占比',
            'wilson_ci':'低评分比例95%区间（工作独立近似）'})
        st.dataframe(display_groups,hide_index=True,width='stretch')
        st.markdown('**主区间：按唯一用户整群 bootstrap；差值方向均为逾期减未逾期。**')
        interval=association['cluster_bootstrap']
        st.write({'评分均分差95%区间':interval['mean_ci'],
                  '低评分比例差95%区间（百分点）':[v*100 for v in interval['low_rate_ci']] if interval['low_rate_ci'] else None,
                  '重采样次数':interval.get('replications'),'排除订单数（单）':association['excluded_orders']})
        st.caption('低评分指订单最新评分≤2。Wilson/Newcombe和Welch为工作独立近似对照，不能替代主区间；不展示仅凭p值的商业判断。')
        table_download(display_groups,'p3_delivery_review_groups')
    with st.expander('查看用户结构和观察机会差异'):
        segments=pd.DataFrame(result['users']['segments'])
        comparison=pd.DataFrame(result['users']['repeat_comparison'])
        st.dataframe(segments,hide_index=True,width='stretch')
        st.dataframe(comparison,hide_index=True,width='stretch')
        table_download(segments,'p3_rfm_structure')
        table_download(comparison,'p3_repeat_comparison')
        st.caption(result['users']['interpretation'])
    st.caption('P3诊断结果、区间和报告均由统计代码生成；原P1事实及其证据在下方保留。')
