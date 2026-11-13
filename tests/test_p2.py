"""P2 live SQL, independent filter checks and Streamlit rendering tests."""
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO
import json
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import text
from streamlit.testing.v1 import AppTest

from retailscope.bi.components import csv_bytes
from retailscope.bi.data import DatabaseUnavailable, Filters, engine, execute, fetch
from retailscope.warehouse import query_rows

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def full_scope():
    bounds = execute('bounds').iloc[0]
    return Filters(bounds.first_date,bounds.last_date+timedelta(days=1))


def test_p2_default_query_matches_every_p1_kpi(full_scope):
    expected = json.loads((ROOT/'reports/p1/kpi_overview.json').read_text())[0]
    actual = execute('overview',full_scope).iloc[0]
    for field,value in expected.items():
        assert actual[field] == (Decimal(value) if isinstance(value,str) else value)
    assert execute('repurchase').iloc[0].repeat_rate == Decimal(json.loads((ROOT/'reports/p1/repurchase_summary.json').read_text())[0]['repeat_rate'])


@pytest.mark.parametrize('view,name,keys',[
    ('rfm_segments','rfm',['segment']), ('repurchase_distribution','frequency',['frequency']),
    ('cohort_retention','cohort',['cohort_month','month_age']), ('cohort_sizes','new_users',['cohort_month']),
])
def test_fixed_user_results_equal_p1(view,name,keys):
    actual = execute(name)
    expected = pd.DataFrame(query_rows(f'SELECT * FROM mart.{view}'))
    pd.testing.assert_frame_equal(actual.sort_values(keys).reset_index(drop=True),expected.sort_values(keys).reset_index(drop=True),check_dtype=False)
    if name == 'cohort':
        future = actual[~actual.is_observed]
        assert future.retention.isna().all() and len(future)>0
        assert actual[actual.is_observed].retention.notna().all()


@pytest.mark.parametrize('states,categories',[(('SP',),()),((),('beleza_saude',)),(('RJ','MG'),('cama_mesa_banho','beleza_saude'))])
def test_date_state_category_filters_against_separate_sql(states,categories):
    scope = Filters(date(2018,1,1),date(2018,2,1),states,categories)
    actual_items = execute('product_kpis',scope).iloc[0]
    # Separate direct SQL oracle joins only item->order and item->unique product.
    expected = query_rows("""SELECT count(DISTINCT o.order_id) AS orders,count(*) AS items,
        coalesce(sum(i.price),0) AS merchandise,coalesce(sum(i.freight),0) AS freight
        FROM mart.order_item_fact i JOIN mart.order_wide o USING(order_id)
        JOIN mart.dim_product p USING(product_id)
        WHERE o.is_eligible AND o.purchased_at>=%s AND o.purchased_at<%s
          AND (%s OR o.customer_state=ANY(%s)) AND (%s OR p.category=ANY(%s))""",
        (scope.start,scope.end,not states,list(states),not categories,list(categories)))[0]
    assert all(actual_items[k] == v for k,v in expected.items())
    by_category = execute('categories',scope)
    by_month = execute('category_monthly',scope)
    assert sum(by_category.merchandise) == sum(by_month.merchandise) == expected['merchandise']
    orders = execute('overview',scope).iloc[0]
    assert orders.orders == expected['orders']  # order-level category membership uses EXISTS.
    assert execute('reviews',scope).orders.sum() <= orders.orders
    assert execute('delivery_histogram',scope).orders.sum() == orders.delivery_n
    assert execute('delivery_regions',scope).orders.sum() == orders.orders


def test_overview_filtered_charts_reconcile_and_partial_month(full_scope):
    scope = Filters(date(2018,1,15),date(2018,3,1),('SP',))
    kpi,monthly,regions = [execute(n,scope) for n in ('overview','monthly','regions')]
    assert sum(monthly.merchandise) == sum(regions.merchandise) == kpi.iloc[0].merchandise
    assert int(monthly.orders.sum()) == int(regions.orders.sum()) == int(kpi.iloc[0].orders)
    assert not bool(monthly.iloc[0].is_complete) and bool(monthly.iloc[1].is_complete)
    assert fetch('overview',scope).iloc[0].orders != fetch('overview',full_scope).iloc[0].orders


def test_empty_scope_does_not_invent_values():
    scope = Filters(date(2018,10,17),date(2018,10,18))
    kpi = execute('overview',scope).iloc[0]
    assert kpi.orders == 0 and kpi.merchandise == 0 and kpi.average_order_value is None
    assert execute('categories',scope).empty
    assert execute('delivery_histogram',scope).empty


def test_query_allowlist_and_bound_injection(full_scope):
    with pytest.raises(ValueError,match='不支持'):
        execute('SELECT password FROM users')
    bad = Filters(full_scope.start,full_scope.end,categories=("x'); DROP SCHEMA mart CASCADE;--",))
    assert execute('product_kpis',bad).iloc[0]['items'] == 0
    with engine().connect() as conn:
        assert conn.execute(text('SHOW transaction_read_only')).scalar() == 'on'
    with pytest.raises(ValueError):
        Filters(date(2018,2,1),date(2018,1,1))


def test_export_preserves_scope_cents_and_na(full_scope):
    scope = Filters(date(2018,1,1),date(2018,2,1),('SP',),('beleza_saude',))
    actual = execute('categories',scope)
    exported = pd.read_csv(BytesIO(csv_bytes(actual)),dtype={'merchandise':str})
    assert exported.orders.sum() == actual.orders.sum()
    assert sum(exported.merchandise.map(Decimal)) == sum(actual.merchandise)
    cohort = execute('cohort')
    raw = csv_bytes(cohort).decode('utf-8-sig')
    assert 'NA' in raw
    reloaded = pd.read_csv(BytesIO(csv_bytes(cohort)))
    assert reloaded.retention.isna().sum() == cohort.retention.isna().sum()


@pytest.mark.parametrize('page,min_charts',[
    ('overview',3),('users',5),('products',5),('delivery',4),('findings',0),('quality',0)
])
def test_each_streamlit_page_opens_with_real_results(page,min_charts):
    at = AppTest.from_file(str(ROOT/'app/Home.py'),default_timeout=45).run()
    if page != 'overview':
        at.switch_page(f'pages/{page}.py').run(timeout=45)
    assert not at.exception and not at.error
    assert len(at.get('plotly_chart')) >= min_charts
    if page == 'overview':
        assert [m.value for m in at.metric] == ['BRL 13,221,498.11','96,478','93,358','BRL 137.04']
    if page == 'delivery':
        assert [m.value for m in at.metric][:3] == ['12.56 天','6.7731%','4.16']
    if page == 'users':
        assert at.metric[2].value == '3.0003%'
        assert '全样本' in at.info[0].value
        heatmap = next(json.loads(p.proto.spec) for p in at.get('plotly_chart') if json.loads(p.proto.spec)['data'][0]['type']=='heatmap')
        assert heatmap['layout']['yaxis']['type']=='category'
        assert sum(v is None for row in heatmap['data'][0]['z'] for v in row)==298
    if page == 'findings':
        assert any('beleza_saude' in m.value for m in at.markdown)
    if page == 'quality':
        assert at.metric[1].value == '1,550,922'


def test_ui_filter_reset_empty_and_page_isolation():
    at = AppTest.from_file(str(ROOT/'app/Home.py'),default_timeout=45).run()
    at.multiselect(key='overview_states').set_value(['SP']).run()
    assert at.metric[0].value == 'BRL 5,067,633.16'
    at.switch_page('pages/users.py').run()
    assert at.metric[0].value == '93,358'  # fixed P1 global sample
    at.switch_page('pages/overview.py').run()
    at.date_input(key='overview_dates').set_value((date(2018,10,17),date(2018,10,17))).run()
    assert at.metric[1].value == '0' and at.info
    at.button(key='overview_reset').click().run()
    assert at.metric[1].value == '96,478'
    at.date_input(key='overview_dates').set_value((date(2018,1,1),)).run()
    assert at.info and not at.exception


def test_connection_error_is_readable_and_contains_no_secret(monkeypatch):
    import retailscope.bi.data as data
    def unavailable(*args,**kwargs):
        raise DatabaseUnavailable('数据暂时无法读取。请确认数据库运行正常且 P1 数据仓库已构建，然后点击“重新连接”。')
    monkeypatch.setattr(data,'fetch',unavailable)
    at = AppTest.from_file(str(ROOT/'app/Home.py'),default_timeout=20).run()
    assert not at.exception and at.error
    assert '数据库' in at.error[0].value
    assert 'postgresql://' not in at.error[0].value and 'password' not in at.error[0].value
