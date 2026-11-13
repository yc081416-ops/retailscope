"""P1 hand-checkable boundaries plus independent live CSV/PostgreSQL reconciliation."""
import os
from pathlib import Path

from dotenv import load_dotenv
import pandas as pd
import pytest

from retailscope.p1_validation import pandas_cohort, pandas_rfm, score_quintiles, validate_pandas
from retailscope.warehouse import query_rows


def sample_orders():
    return pd.DataFrame({
        'order_id': ['a', 'b', 'c', 'd'], 'customer_unique_id': ['u1', 'u1', 'u2', 'u2'],
        'purchased_at': pd.to_datetime(['2020-01-15', '2020-02-01', '2020-02-02', '2020-04-15']),
        'merchandise_cents': [1001, 2002, 3003, 4004],
    })


def test_quintile_ties_are_not_split():
    assert score_quintiles(pd.Series([1] * 10)).tolist() == [1] * 10
    assert score_quintiles(pd.Series([1] * 10), reverse=True).tolist() == [5] * 10
    assert score_quintiles(pd.Series([1, 1, 2, 2, 3])).tolist() == [1, 1, 3, 3, 5]


def test_rfm_hand_calculation_and_unknown_money():
    orders = sample_orders()
    rfm = pandas_rfm(orders).set_index('customer_unique_id')
    assert rfm.loc['u1', 'frequency'] == 2
    assert rfm.loc['u1', 'monetary_cents'] == 3003
    assert rfm.loc['u1', 'recency'] == 75
    assert rfm.loc['u2', 'recency'] == 1
    orders.loc[0, 'merchandise_cents'] = float('nan')
    missing = pandas_rfm(orders).set_index('customer_unique_id').loc['u1']
    assert pd.isna(missing.monetary_cents) and missing.segment == '数据待核对'


def test_cohort_missing_window_zero_and_monthly_dedup():
    orders = sample_orders()
    orders = pd.concat([orders, orders.iloc[[1]]], ignore_index=True)
    matrix = pandas_cohort(orders).set_index(['cohort_month', 'month_age'])
    january = pd.Timestamp('2020-01-01').date()
    assert pd.isna(matrix.loc[(january, 0), 'retention'])  # incomplete first month
    assert matrix.loc[(january, 1), 'active_users'] == 1  # two orders still one user
    assert matrix.loc[(january, 2), 'retention'] == 0     # fully observed March, no purchase
    assert pd.isna(matrix.loc[(january, 3), 'retention']) # incomplete April


@pytest.fixture(scope='module')
def live_reconciliation():
    load_dotenv()
    if not os.environ.get('DATABASE_URL'):
        pytest.skip('P1 integration requires DATABASE_URL and a built mart')
    return validate_pandas(output=Path('reports/p1/pandas_reconciliation.json'))


@pytest.mark.parametrize('name', [
    'all_order_rows_and_amounts', 'multi_payment_no_amount_inflation',
    'multi_review_no_order_inflation', 'order_financial_preaggregation',
    'payment_preaggregation', 'review_preaggregation', 'all_item_rows_and_amounts',
    'overview_money_users_delivery_review', 'all_status_distribution',
    'monthly_including_empty_and_partial', 'category_ranking', 'category_monthly',
    'region_sales', 'review_distribution_one_per_order', 'every_user_rfm_and_tied_scores',
    'rfm_segments', 'repurchase_frequency_distribution', 'repurchase_unique_customers',
    'every_cohort_cell_including_unobserved_nulls', 'cohort_new_users',
    'deduplicated_geolocation', 'geolocation_join_no_inflation',
])
def test_live_sql_against_independent_csv(name, live_reconciliation):
    assert next(c for c in live_reconciliation['checks'] if c['name'] == name)['passed']


def test_live_keys_missingness_and_unobserved_cells(live_reconciliation):
    checks = query_rows("""SELECT
        (SELECT count(*) FROM mart.order_wide)-(SELECT count(*) FROM raw.orders) AS order_delta,
        (SELECT count(*) FROM mart.order_item_fact)-(SELECT count(*) FROM raw.order_items) AS item_delta,
        (SELECT count(*) FROM mart.cohort_retention WHERE NOT is_observed AND (retention IS NOT NULL OR active_users IS NOT NULL)) AS exposed_future,
        (SELECT count(*) FROM mart.cohort_retention WHERE retention<0 OR retention>1) AS invalid_rate,
        (SELECT count(*) FROM mart.order_wide WHERE NOT has_items AND merchandise IS NOT NULL) AS invented_money,
        (SELECT count(*) FROM mart.order_wide WHERE NOT has_payment AND payment IS NOT NULL) AS invented_payment,
        (SELECT count(*) FROM mart.order_wide WHERE NOT is_eligible AND (delivery_days IS NOT NULL OR is_late IS NOT NULL)) AS invalid_delivery_scope
    """)[0]
    assert all(v == 0 for v in checks.values()), checks
