import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from retailscope.bi.components import BLUE, bar, chart, filters, header, money, number, safe_page, table_download
from retailscope.bi.data import fetch


@safe_page
def render():
    header('BUSINESS OVERVIEW / 01', '经营总览', '从商品金额、订单与地区贡献，理解历史经营规模。')
    scope = filters('overview')
    kpi = fetch('overview',scope).iloc[0]
    columns = st.columns([1.6,1,1,1.35])
    for col,label,value,help_text in zip(columns,
        ['商品成交额','有效订单数','唯一购买用户','平均订单商品金额'],
        [money(kpi.merchandise),number(kpi.orders),number(kpi.users),money(kpi.average_order_value)],
        ['商品price之和，不含运费；不是财务确认收入。','delivered且购买时间有效，一订单一行。','跨订单去重customer_unique_id。','商品成交额/有效订单数，BRL/单。']):
        col.metric(label,value,help=help_text)
    st.caption(f'独立口径：运费 {money(kpi.freight)} · 支付金额 {money(kpi.payment)}。三者不混同，也不代表净利润。')
    table_download(fetch('overview',scope),'overview_kpis','查看当前范围 KPI 与导出')
    if not kpi.orders:
        st.info('当前筛选没有有效购买订单。可清空筛选或调整日期、地区；全部状态分布仍按当前范围展示。')
    monthly = fetch('monthly',scope)
    with st.container(border=True):
        st.subheader('月度商品金额与有效订单')
        st.caption('橙色点标记不完整月份或局部日期窗口；不计算增长率。空月份保留真实零值。')
        fig = make_subplots(specs=[[{'secondary_y':True}]])
        fig.add_trace(go.Bar(x=monthly.month_start,y=monthly.merchandise.astype(float),name='商品成交额 · BRL',marker_color=BLUE,opacity=.78),secondary_y=False)
        fig.add_trace(go.Scatter(x=monthly.month_start,y=monthly.orders,name='有效订单 · 单',mode='lines+markers',line_color='#148A9B',marker=dict(color=['#148A9B' if x else '#D18B28' for x in monthly.is_complete])),secondary_y=True)
        amount_max=float(monthly.merchandise.max()) if len(monthly) else 0
        order_max=int(monthly.orders.max()) if len(monthly) else 0
        fig.update_yaxes(title_text='商品成交额 · BRL',range=[0,max(1,amount_max*1.12)],rangemode='tozero',secondary_y=False)
        fig.update_yaxes(title_text='有效订单 · 单',range=[0,max(1,order_max*1.12)],rangemode='tozero',tickformat=',d',secondary_y=True)
        chart(fig,'overview_monthly',380)
        table_download(monthly,'overview_monthly')
    left,right = st.columns(2)
    with left,st.container(border=True):
        st.subheader('订单状态分布')
        st.caption('同一日期与地区范围，覆盖全部订单状态；不只限于有效订单。')
        statuses = fetch('statuses',scope)
        bar(statuses,'orders','status','overview_statuses',{'orders':'订单数 · 单','status':'状态'},True)
        table_download(statuses,'overview_statuses')
    with right,st.container(border=True):
        st.subheader('客户州商品金额 · TOP 10')
        regions = fetch('regions',scope)
        bar(regions.head(10).iloc[::-1],'merchandise','state','overview_regions',{'merchandise':'商品成交额 · BRL','state':'州'},True)
        table_download(regions,'overview_regions','查看全部地区与导出')
    with st.expander('指标说明与历史观察范围'):
        context = fetch('context').iloc[0]
        st.write(f'P1有效购买范围：{context.first_purchase} 至 {context.last_purchase}。日期使用order_purchase_timestamp；界面含首尾日期，查询使用次日作为exclusive边界。')
        st.write('有效订单中的缺商品/支付记录保留并标记；金额只统计已知明细。所有图表均使用当前日期与地区筛选，状态分布另外覆盖同范围全部状态。')


render()
