"""Shared layout, filters, formatting and current-result exports."""
from datetime import timedelta
from decimal import Decimal
import json
import os
from pathlib import Path
from functools import wraps

import pandas as pd
import plotly.express as px
import streamlit as st

from .data import DatabaseUnavailable, Filters, ROOT, engine, fetch

BLUE = '#2457D6'
COLORS = [BLUE, '#148A9B', '#6C73C7', '#D18B28', '#5E85BA', '#789197']


def money(value):
    return 'NA' if value is None or pd.isna(value) else f'BRL {Decimal(str(value)):,.2f}'


def number(value, decimals=0, suffix=''):
    return 'NA' if value is None or pd.isna(value) else f'{value:,.{decimals}f}{suffix}'


def percent(value):
    return 'NA' if value is None or pd.isna(value) else f'{value*100:.4f}%'


def csv_bytes(frame):
    return frame.to_csv(index=False, na_rep='NA').encode('utf-8-sig')


def table_download(frame, name, title='查看结果表与导出'):
    with st.expander(title):
        st.dataframe(frame, hide_index=True, width='stretch')
        st.download_button(f'下载 CSV · {name}', csv_bytes(frame), f'{name}.csv', 'text/csv', key=f'download_{name}', on_click='ignore')


def header(kicker, title, subtitle):
    st.caption(kicker)
    st.title(title)
    st.markdown(subtitle)


def safe_page(func):
    @wraps(func)
    def wrapped():
        try:
            func()
        except DatabaseUnavailable as exc:
            st.error(str(exc))
            st.caption('页面没有使用缓存示例或模拟业务数据替代失败查询。')
            if st.button('重新连接'):
                st.cache_data.clear()
                engine.clear()
                st.rerun()
    return wrapped


def filters(prefix, category=False):
    bounds = fetch('bounds').iloc[0]
    states = fetch('states').state.tolist()
    categories = fetch('category_options').category.tolist() if category else []
    first, last = bounds.first_date, bounds.last_date
    defaults = {f'{prefix}_dates': (first,last), f'{prefix}_states': []}
    if category:
        defaults[f'{prefix}_categories'] = []
    def reset():
        for key, val in defaults.items():
            st.session_state[key] = val
    with st.container(border=True):
        cols = st.columns([2,1.3,1.8,.75] if category else [2,2,.8],vertical_alignment='bottom')
        dates = cols[0].date_input('购买日期（含首尾）', value=(first,last), min_value=first, max_value=last, key=f'{prefix}_dates')
        selected_states = cols[1].multiselect('客户州 · 留空为全部', states,placeholder='请选择（留空为全部）', key=f'{prefix}_states')
        selected_categories = cols[2].multiselect('商品类目 · 留空为全部', categories,placeholder='请选择（留空为全部）', key=f'{prefix}_categories') if category else []
        cols[-1].button('清空筛选', on_click=reset, key=f'{prefix}_reset')
    if len(dates) != 2:
        st.info('请在日期控件中选择完整的起止日期。')
        st.stop()
    scope = Filters(dates[0], dates[1]+timedelta(days=1), tuple(selected_states), tuple(selected_categories))
    st.caption(f'当前范围：{dates[0]} 至 {dates[1]} · 州：{", ".join(selected_states) or "全部"} · 类目：{", ".join(selected_categories) or "全部"}。指标默认仅 delivered，状态分布另含全部状态。')
    return scope


def chart(fig, name, height=340):
    fig.update_layout(template='plotly_white', height=height, margin=dict(l=12,r=16,t=24,b=24),
        font=dict(family='Microsoft YaHei, Arial, sans-serif',size=14,color='#263449'),
        colorway=COLORS, paper_bgcolor='white', plot_bgcolor='white',
        legend=dict(orientation='h',y=-0.22), hoverlabel=dict(font_size=14))
    fig.update_xaxes(showgrid=False,automargin=True,tickfont=dict(size=14,color='#46566C'))
    fig.update_yaxes(gridcolor='#E8EDF5',automargin=True,tickfont=dict(size=14,color='#46566C'))
    st.plotly_chart(fig, width='stretch', key=name, config={'displaylogo':False})


def bar(frame, x, y, name, labels=None, horizontal=False, height=340):
    plotted = frame.copy()
    for col in plotted.columns:
        if plotted[col].map(lambda x: isinstance(x,Decimal)).any():
            plotted[col] = plotted[col].astype(float)
    fig = px.bar(plotted,x=x,y=y,orientation='h' if horizontal else 'v',labels=labels,color_discrete_sequence=[BLUE])
    chart(fig,name,height)


def evidence_path(relative):
    isolated=os.environ.get('RETAILSCOPE_RUNTIME_MANIFEST')
    if relative=='reports/p3/analysis.json' and isolated:
        metadata=json.loads(Path(isolated).read_text(encoding='utf-8'))
        candidate=Path(metadata['analysis_path']).resolve()
        if candidate.is_relative_to(ROOT/'reports') and candidate.is_file():
            return candidate
        raise RuntimeError('隔离分析快照必须位于本项目reports目录。')
    pointer=ROOT/'reports/runtime/active.json'
    if relative=='reports/p3/analysis.json' and pointer.is_file():
        metadata=json.loads(pointer.read_text(encoding='utf-8'))
        candidate=(ROOT/metadata['analysis']).resolve()
        if candidate.is_relative_to(ROOT/'reports') and candidate.is_file():
            relative=str(candidate.relative_to(ROOT))
    return ROOT/relative


def analysis_report_path():
    if os.environ.get('RETAILSCOPE_RUNTIME_MANIFEST'):
        return evidence_path('reports/p3/analysis.json').parent.parent/'P3_BUSINESS_REPORT.md'
    pointer=ROOT/'reports/runtime/active.json'
    if pointer.is_file():
        metadata=json.loads(pointer.read_text(encoding='utf-8'))
        if metadata.get('report'):
            candidate=(ROOT/metadata['report']).resolve()
            if candidate.is_relative_to(ROOT/'reports') and candidate.is_file():
                return candidate
    return ROOT/'docs/P3_BUSINESS_REPORT.md'


def load_evidence(relative):
    path=evidence_path(relative)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding='utf-8-sig'))
