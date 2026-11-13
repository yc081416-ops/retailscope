import plotly.express as px
import streamlit as st

from retailscope.bi.components import bar, chart, filters, header, number, percent, safe_page, table_download
from retailscope.bi.data import fetch


@safe_page
def render():
    header('DELIVERY & EXPERIENCE / 04','履约与评价分析','观察配送时长、逾期表现与评价的描述性关联。')
    scope = filters('delivery',category=True)
    st.caption('类目筛选表示“有效订单包含任一选中类目”；订单只计一次。评价和配送采用订单级口径，所有组件使用该订单范围。')
    kpi = fetch('overview',scope).iloc[0]
    for col,label,val in zip(st.columns(4),['平均配送天数','逾期率','订单等权评价均分','有效订单数'],
        [number(kpi.delivery_days,2,' 天'),percent(kpi.late_rate),number(kpi.review_mean,2),number(kpi.orders)]):
        col.metric(label,val)
    st.caption(f'配送样本 {number(kpi.delivery_n)} 单 · 逾期判断样本 {number(kpi.late_n)} 单 · 有评价 {number(kpi.reviewed_orders)} 单。缺失/异常日期不进入配送分母，同日送达不算逾期。')
    table_download(fetch('overview',scope),'delivery_kpis')
    if not kpi.orders:
        st.info('当前筛选没有有效订单，请调整日期、地区或类目。')
        return
    left,right = st.columns(2)
    with left,st.container(border=True):
        st.subheader('配送时长分布 · 每 5 天一组')
        histogram = fetch('delivery_histogram',scope).copy()
        histogram['day_range'] = histogram.day_start.map(lambda d:f'[{int(d)}, {int(d)+5})')
        bar(histogram,'day_range','orders','delivery_histogram',{'day_range':'实际配送时长 · 天','orders':'订单数 · 单'})
        table_download(histogram,'delivery_histogram')
    with right,st.container(border=True):
        st.subheader('订单最新评价得分分布')
        reviews = fetch('reviews',scope)
        bar(reviews,'score','orders','delivery_reviews',{'score':'每订单最新评分','orders':'有效订单数 · 单'})
        st.caption('均分先在订单内平均，再对订单等权；此分布每订单取最新评分，口径不同但均无多评价加权。')
        table_download(reviews,'review_distribution')
    with st.container(border=True):
        st.subheader('不同客户州的配送表现')
        regions = fetch('delivery_regions',scope).copy()
        regions['delivery_days'] = regions.delivery_days.astype(float)
        bar(regions,'state','delivery_days','delivery_regions',{'state':'客户州','delivery_days':'平均配送时长 · 天'})
        table_download(regions,'delivery_by_state','州级配送均值、逾期率及样本数')
    with st.container(border=True):
        st.subheader('逾期与评价 · 描述性关联')
        association = fetch('late_reviews',scope).copy()
        association['review_mean'] = association.review_mean.astype(float)
        bar(association,'delivery_group','review_mean','delivery_association',{'delivery_group':'配送分组','review_mean':'订单等权评价均分'})
        st.info('这是在有效配送且有评价订单中的分组比较。样本选择、地区、商品和用户差异均可能影响结果，不能据此断言配送延迟导致差评。低评分指最新评分≤2。')
        table_download(association,'late_review_association','查看分组样本数、均分和低评分率')


render()
