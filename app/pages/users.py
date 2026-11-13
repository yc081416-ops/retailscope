import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from retailscope.bi.components import bar, chart, header, money, number, percent, safe_page, table_download
from retailscope.bi.data import fetch


@safe_page
def render():
    header('CUSTOMER VALUE / 02','用户价值分析','以跨订单唯一用户为单位，查看价值分层和回购活跃留存。')
    context = fetch('context').iloc[0]
    st.info(f'固定 P1 全样本：{context.first_purchase} 至 {context.last_purchase}；RFM 基准日 {context.rfm_reference_date}。本页不受其他页面日期、地区或类目筛选影响。')
    summary = fetch('repurchase').iloc[0]
    frequency,segments = fetch('frequency'),fetch('rfm')
    single = int(frequency.loc[frequency.frequency.eq(1),'users'].sum())
    columns = st.columns(4)
    for col,label,value in zip(columns,['购买用户','复购用户','整体复购率','仅一次购买用户占比'],
        [number(summary.users),number(summary.repeat_users),percent(summary.repeat_rate),percent(single/int(summary.users))]):
        col.metric(label,value)
    st.caption('复购率为全观察期内有效订单≥2的用户占比。用户进入样本的时间不同，观察时长不等。')
    left,right = st.columns(2)
    with left,st.container(border=True):
        st.subheader('RFM 六类用户分层')
        bar(segments.iloc[::-1],'users','segment','users_segments',{'users':'唯一用户数 · 人','segment':'规则分层'},True,370)
        table_download(segments,'rfm_segments','分层人数、占比与金额贡献')
    with right,st.container(border=True):
        st.subheader('分层商品金额贡献')
        values = segments.copy()
        values['占比'] = values.contribution.astype(float)
        fig = px.bar(values,x='占比',y='segment',orientation='h',labels={'segment':'规则分层','占比':'商品金额贡献'},color_discrete_sequence=['#148A9B'])
        fig.update_xaxes(tickformat='.0%')
        chart(fig,'users_contribution',370)
        st.caption('分层名称为规则标签；不代表营销干预已经产生效果。“数据待核对”在P1样本为0人，不混入六个非空层。')
    with st.container(border=True):
        st.subheader('购买频次分布')
        st.caption(f'{number(single)} 人仅购买一次。Frequency 的20/40/60/80%分位点均为1，同值同分，因此F评分2–4为空属于数据特征。')
        fig = px.bar(frequency,x='frequency',y='users',log_y=True,labels={'frequency':'有效订单次数 · 次','users':'用户数 · 人（对数轴）'})
        chart(fig,'users_frequency',290)
        table_download(frequency,'purchase_frequency')
    with st.container(border=True):
        st.subheader('Cohort 月度回购活跃留存')
        st.caption(f'完整目标月：[{context.first_complete_month}, {context.observation_end_exclusive})。同一用户同月多单仅计一次；灰白空格为NA，已观察无回购为0%。')
        cohort = fetch('cohort').copy()
        pivot = cohort.pivot(index='cohort_month',columns='month_age',values='retention')
        matrix = pivot.map(lambda v: None if v is None or pd.isna(v) else float(v))
        text = matrix.map(lambda v: '' if pd.isna(v) else (f'{v:.0%}' if v>=.1 else f'{v:.1%}'))
        fig = go.Figure(go.Heatmap(x=[f'M{c}' for c in matrix.columns],y=[str(i)[:7] for i in matrix.index],
            z=matrix.values.tolist(),text=text.values.tolist(),texttemplate='%{text}',textfont_size=10,
            colorscale='Blues',zmin=0,zmax=.02,hoverongaps=False,
            hovertemplate='首购月 %{y}<br>月龄 %{x}<br>留存 %{z:.4%}<extra></extra>',
            colorbar=dict(title='留存率',tickvals=[0,.01,.02],ticktext=['0%','1%','≥2%'])))
        fig.update_yaxes(type='category',autorange='reversed',dtick=1)
        fig.update_xaxes(side='top')
        chart(fig,'users_cohort',650)
        st.caption('色阶在2%封顶以便阅读低留存单元；文字与悬停保留真实比例，M0可为100%。2016-09首cohort获客左截断，未观察月份绝不补0。')
        table_download(cohort,'cohort_retention','查看留存长表与NA导出')
    with st.container(border=True):
        st.subheader('每月观测新增购买用户')
        newcomers = fetch('new_users')
        bar(newcomers,'cohort_month','new_users','users_new',{'cohort_month':'首次有效购买月','new_users':'观测新增用户 · 人'})
        st.caption('数据中首次购买，不等同于平台真实历史首购；首尾月份样本不完整。')
        table_download(newcomers,'cohort_new_users')


render()
