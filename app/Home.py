"""Run: python -m streamlit run app/Home.py"""
import streamlit as st

st.set_page_config(page_title='RetailScope · 经营分析',page_icon='📊',layout='wide')
st.markdown('''<style>
.stApp {font-family: "Microsoft YaHei", "Segoe UI", sans-serif;}
.block-container {padding-top: 1.25rem; padding-bottom: 3rem; max-width: 1560px;}
h1 {font-size: 2rem !important; font-weight: 700 !important; letter-spacing: -.02em;}
h3 {font-size: 1.12rem !important;}
[data-testid="stSidebar"] {background: #EDF2FA; border-right: 1px solid #DEE6F1;}
[data-testid="stMetric"] {background: white; border: 1px solid #DFE6F0; border-radius: 10px; padding: .8rem;}
[data-testid="stMetricValue"] {font-size: clamp(1.05rem, 1.5vw, 1.5rem); color: #173E87;}
[data-testid="stMetricValue"] > div {white-space: normal; overflow: visible; text-overflow: clip;}
[data-testid="stCaptionContainer"] {opacity: 1 !important;}
[data-testid="stCaptionContainer"] p {color: #38495F !important; font-size: .95rem; line-height: 1.6;}
</style>''',unsafe_allow_html=True)
st.sidebar.markdown('## RetailScope')
st.sidebar.caption('电商经营分析与用户增长\n\nOlist · 2016–2018 历史样本')
pages = [
    st.Page('pages/overview.py',title='经营总览',icon=':material/dashboard:',default=True),
    st.Page('pages/users.py',title='用户价值分析',icon=':material/groups:',url_path='users'),
    st.Page('pages/products.py',title='商品与品类分析',icon=':material/category:',url_path='products'),
    st.Page('pages/delivery.py',title='履约与评价分析',icon=':material/local_shipping:',url_path='delivery'),
    st.Page('pages/findings.py',title='经营发现',icon=':material/insights:',url_path='findings'),
    st.Page('pages/quality.py',title='数据质量中心',icon=':material/fact_check:',url_path='quality'),
]
page = st.navigation(pages)
st.sidebar.caption('数据：PostgreSQL 16 · P1 仓库\n\n商品金额不代表收入或利润。')
if st.sidebar.button('刷新查询缓存'):
    st.cache_data.clear()
    st.rerun()
page.run()
