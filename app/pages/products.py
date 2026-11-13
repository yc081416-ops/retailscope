import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from retailscope.bi.components import BLUE, bar, chart, filters, header, money, number, safe_page, table_download
from retailscope.bi.data import fetch


@safe_page
def render():
    header('PRODUCT & CATEGORY / 03','商品与品类分析','从选中商品明细观察品类贡献、集中度与月度结构。')
    scope = filters('products',category=True)
    st.caption('类目筛选仅统计选中类目的商品行；金额、运费、件数、去重订单数和图表全部采用相同商品范围。')
    kpi = fetch('product_kpis',scope).iloc[0]
    for col,label,val in zip(st.columns([1.6,1,1,1.5]),['商品成交额','商品件数','覆盖有效订单','商品运费'],[money(kpi.merchandise),number(kpi['items']),number(kpi.orders),money(kpi.freight)]):
        col.metric(label,val)
    table_download(fetch('product_kpis',scope),'product_kpis')
    if not kpi['items']:
        st.info('当前日期、地区与类目组合没有有效商品明细。请调整或清空筛选。')
        return
    categories = fetch('categories',scope).copy()
    st.warning('同一订单可能跨多个类目。各类目去重订单数不可直接相加作为总订单数；商品件数与金额可在不重叠类目间相加。',icon=':material/info:')
    left,right = st.columns(2)
    with left,st.container(border=True):
        st.subheader('TOP 10 品类 · 商品成交额')
        bar(categories.head(10).iloc[::-1],'merchandise','category','products_top10',{'merchandise':'商品成交额 · BRL','category':'葡语类目'},True,440)
    with right,st.container(border=True):
        st.subheader('TOP 10 品类 · 成交额贡献')
        values = categories.head(10).iloc[::-1].copy()
        values['贡献占比'] = values.contribution.astype(float)
        fig = px.bar(values,x='贡献占比',y='category',orientation='h',labels={'category':'葡语类目'},color_discrete_sequence=['#148A9B'])
        fig.update_xaxes(tickformat='.1%')
        chart(fig,'products_share',440)
    table_download(categories,'category_ranking','全部类目排行与当前范围导出')
    with st.container(border=True):
        st.subheader('帕累托累计贡献')
        pareto = categories.copy()
        pareto['rank'] = range(1,len(pareto)+1)
        pareto['cumulative'] = pareto.contribution.astype(float).cumsum()
        fig = make_subplots(specs=[[{'secondary_y':True}]])
        fig.add_trace(go.Bar(x=pareto['rank'],y=pareto.merchandise.astype(float),name='商品成交额 · BRL',marker_color=BLUE),secondary_y=False)
        fig.add_trace(go.Scatter(x=pareto['rank'],y=pareto.cumulative,name='累计贡献',line_color='#148A9B'),secondary_y=True)
        fig.update_xaxes(title='品类按商品金额降序排名')
        fig.update_yaxes(title_text='商品成交额 · BRL',secondary_y=False)
        fig.update_yaxes(title_text='累计贡献',tickformat='.0%',range=[0,1.05],secondary_y=True)
        chart(fig,'products_pareto')
        table_download(pareto,'category_pareto')
    with st.container(border=True):
        st.subheader('TOP 10 品类月度趋势')
        monthly = fetch('category_monthly',scope)
        shown = monthly[monthly.category.isin(categories.head(10).category)].copy()
        shown['merchandise'] = shown.merchandise.astype(float)
        fig = px.line(shown,x='month_start',y='merchandise',color='category',labels={'month_start':'购买月份','merchandise':'商品成交额 · BRL','category':'类目'})
        chart(fig,'products_monthly',430)
        st.caption('首尾月及局部日期窗口可能不完整，不据此计算增长率。未出现的类目/月在本表不代表完整观测。')
        table_download(monthly,'category_monthly','全部选中类目的月度结果与导出')
    with st.container(border=True):
        st.subheader('TOP 10 品类 · 件数与订单数')
        counts = categories.head(10).melt(id_vars='category',value_vars=['items','orders'],var_name='measure',value_name='count')
        counts['measure'] = counts.measure.map({'items':'商品件数','orders':'类目内去重订单数'})
        fig = px.bar(counts,x='category',y='count',color='measure',barmode='group',labels={'category':'葡语类目','count':'件 / 单','measure':'指标'})
        chart(fig,'products_counts',380)


render()
