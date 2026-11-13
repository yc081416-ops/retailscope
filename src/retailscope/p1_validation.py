"""Independent CSV/Pandas oracle. Money uses integer cents, never binary floats."""
from bisect import bisect_left
from decimal import Decimal
from datetime import timedelta
import math
from pathlib import Path

import pandas as pd

from .contracts import SOURCES
from .warehouse import query_rows, save_json


def cents(value):
    return None if value is None or pd.isna(value) else int(Decimal(str(value)) * 100)


def score_quintiles(values, reverse=False):
    ordered = sorted(v for v in values if pd.notna(v))
    if not ordered:
        return pd.Series([None] * len(values), index=values.index)
    bounds = [ordered[math.ceil(len(ordered) * p / 5) - 1] for p in range(1, 5)]
    def score(v):
        if pd.isna(v):
            return None
        result = bisect_left(bounds, v) + 1
        return 6 - result if reverse else result
    return values.map(score)


def segment_user(row):
    r, f, m = row['r_score'], row['f_score'], row['m_score']
    if pd.isna(m):
        return '数据待核对'
    if r >= 4 and f >= 4 and m >= 4:
        return '核心价值'
    if r >= 4 and f >= 4:
        return '活跃复购'
    if r >= 4:
        return '近期用户'
    if r <= 2 and m >= 4:
        return '高价值待唤回'
    return '沉睡用户' if r <= 2 else '其他用户'


def pandas_rfm(orders):
    reference = pd.Timestamp(orders['purchased_at'].max().date() + timedelta(days=1))
    result = orders.groupby('customer_unique_id').agg(
        last_purchase_date=('purchased_at', 'max'), frequency=('order_id', 'size'),
        monetary_cents=('merchandise_cents', lambda x: x.sum(min_count=len(x))),
    ).reset_index()
    result['last_purchase_date'] = result.last_purchase_date.dt.normalize()
    result['recency'] = (reference - result.last_purchase_date).dt.days
    result['rfm_reference_date'] = reference
    for column, label, reverse in [('recency', 'r_score', True), ('frequency', 'f_score', False), ('monetary_cents', 'm_score', False)]:
        result[label] = score_quintiles(result[column], reverse)
    result['segment'] = result.apply(segment_user, axis=1)
    return result


def pandas_cohort(orders):
    activity = orders[['customer_unique_id', 'purchased_at']].copy()
    activity['month'] = activity.purchased_at.dt.to_period('M')
    activity = activity[['customer_unique_id', 'month']].drop_duplicates()
    first = activity.groupby('customer_unique_id')['month'].min().rename('cohort_month')
    sizes = first.value_counts().sort_index()
    counts = activity.join(first, on='customer_unique_id').groupby(['cohort_month', 'month']).size()
    first_date, last_date = orders.purchased_at.min().normalize(), orders.purchased_at.max().normalize()
    first_full = first_date.to_period('M') + int(first_date.day != 1)
    end = last_date.to_period('M')
    max_age = end.ordinal - first_date.to_period('M').ordinal
    rows = []
    for cohort, size in sizes.items():
        for age in range(max_age + 1):
            target = cohort + age
            observed = first_full <= target < end
            active = int(counts.get((cohort, target), 0)) if observed else None
            rows.append({
                'cohort_month': cohort.start_time.date(), 'month_age': age,
                'target_month': target.start_time.date(), 'new_users': int(size),
                'cohort_left_truncated': cohort < first_full, 'is_observed': observed,
                'active_users': active, 'retention': active / size if observed else None,
            })
    return pd.DataFrame(rows)


def validate_pandas(source=Path('data/raw'), output=Path('reports/p1/pandas_reconciliation.json')):
    frames = {s.table_name: pd.read_csv(source / s.file_name, dtype=str, keep_default_na=False) for s in SOURCES}
    checks = []

    def compare(name, expected, actual, keys, columns):
        expected, actual = expected.copy(), actual.copy()
        for frame in (expected, actual):
            for column in columns:
                if column.endswith('_cents'):
                    frame[column] = frame[column].astype('Int64')
                elif column in ('is_late', 'is_eligible', 'has_items', 'has_payment', 'delivery_anomaly', 'is_observed', 'cohort_left_truncated', 'is_complete'):
                    frame[column] = frame[column].astype('boolean')
                elif column == 'latest_review_score':
                    frame[column] = frame[column].astype('Int64')
                elif column.endswith('_date') or column in ('month_start', 'cohort_month', 'target_month', 'rfm_reference_date'):
                    frame[column] = pd.to_datetime(frame[column]).astype('datetime64[ns]')
                elif column in ('delivery_days', 'review_mean', 'late_rate', 'retention', 'contribution', 'average_order_value', 'share', 'user_share', 'order_share'):
                    frame[column] = pd.to_numeric(frame[column]).astype(float)
        expected = expected[columns].sort_values(keys).reset_index(drop=True)
        actual = actual[columns].sort_values(keys).reset_index(drop=True)
        try:
            money_columns = [c for c in columns if c.endswith('_cents')]
            if money_columns:
                pd.testing.assert_frame_equal(expected[money_columns], actual[money_columns], check_dtype=False, check_exact=True)
            pd.testing.assert_frame_equal(expected, actual, check_dtype=False, check_exact=False, rtol=1e-10, atol=1e-10)
        except AssertionError:
            checks.append({'name': name, 'passed': False, 'expected_rows': len(expected), 'actual_rows': len(actual)})
            save_json({'passed': False, 'checks': checks}, output)
            raise
        checks.append({'name': name, 'passed': True, 'rows': len(expected)})

    def sql_frame(view):
        frame = pd.DataFrame(query_rows(f'SELECT * FROM mart.{view}'))
        for col in ('merchandise', 'monetary', 'freight', 'payment'):
            if col in frame:
                frame[col + '_cents'] = frame[col].map(cents).astype('Int64')
        return frame

    customers = frames['customers'].rename(columns={'customer_state': 'customer_state'})
    orders = frames['orders'].rename(columns={
        'order_status': 'status', 'order_purchase_timestamp': 'purchased_at',
        'order_delivered_customer_date': 'delivered_at', 'order_estimated_delivery_date': 'estimated_at',
    })
    for col in ('purchased_at', 'delivered_at', 'estimated_at'):
        orders[col] = pd.to_datetime(orders[col], format='%Y-%m-%d %H:%M:%S')
    items = frames['order_items'].copy()
    items['merchandise_cents'] = items.price.map(cents)
    items['freight_cents'] = items.freight_value.map(cents)
    financials = items.groupby('order_id').agg(
        merchandise_cents=('merchandise_cents', 'sum'), freight_cents=('freight_cents', 'sum'), item_count=('order_id', 'size'),
    ).reset_index()
    payments = frames['order_payments'].copy()
    payments['payment_cents'] = payments.payment_value.map(cents)
    payment_agg = payments.groupby('order_id').agg(payment_cents=('payment_cents', 'sum'), payment_count=('order_id', 'size')).reset_index()
    reviews = frames['order_reviews'].copy()
    reviews['score'] = reviews.review_score.astype(int)
    review_agg = reviews.groupby('order_id').agg(review_count=('order_id', 'size'), review_mean=('score', 'mean')).reset_index()
    latest = reviews.sort_values(['review_answer_timestamp', 'review_creation_date', 'review_id', 'score']).drop_duplicates('order_id', keep='last')
    review_agg = review_agg.merge(latest[['order_id', 'score']].rename(columns={'score': 'latest_review_score'}), validate='one_to_one')
    all_orders = orders.merge(customers[['customer_id', 'customer_unique_id', 'customer_state']], on='customer_id', validate='one_to_one')
    for agg in (financials, payment_agg, review_agg):
        all_orders = all_orders.merge(agg, on='order_id', how='left', validate='one_to_one')
    all_orders['has_items'] = all_orders.item_count.notna()
    all_orders['has_payment'] = all_orders.payment_count.notna()
    all_orders['is_eligible'] = all_orders.status.eq('delivered') & all_orders.purchased_at.notna()
    all_orders['item_count'] = all_orders.item_count.fillna(0).astype(int)
    all_orders['review_count'] = all_orders.review_count.fillna(0).astype(int)
    all_orders['purchase_date'] = all_orders.purchased_at.dt.normalize()
    all_orders['month_start'] = all_orders.purchased_at.dt.to_period('M').dt.to_timestamp()
    all_orders['delivery_days'] = (all_orders.delivered_at - all_orders.purchased_at).dt.total_seconds() / 86400
    all_orders.loc[~all_orders.is_eligible | all_orders.delivery_days.lt(0), 'delivery_days'] = float('nan')
    valid_late = all_orders.delivery_days.notna() & all_orders.estimated_at.ge(all_orders.purchased_at.dt.normalize())
    all_orders['is_late'] = pd.Series(pd.NA, index=all_orders.index, dtype='boolean')
    all_orders.loc[valid_late, 'is_late'] = all_orders.loc[valid_late, 'delivered_at'].dt.normalize().gt(all_orders.loc[valid_late, 'estimated_at'].dt.normalize())
    all_orders['delivery_anomaly'] = all_orders.delivered_at.lt(all_orders.purchased_at) | all_orders.estimated_at.lt(all_orders.purchased_at.dt.normalize())
    actual_orders = sql_frame('order_wide')
    columns = ['order_id', 'customer_id', 'customer_unique_id', 'status', 'purchase_date', 'month_start', 'customer_state', 'is_eligible', 'has_items', 'has_payment', 'item_count', 'merchandise_cents', 'freight_cents', 'payment_cents', 'review_count', 'review_mean', 'latest_review_score', 'delivery_days', 'is_late', 'delivery_anomaly']
    compare('all_order_rows_and_amounts', all_orders, actual_orders, ['order_id'], columns)
    for label, counts in [('multi_payment_no_amount_inflation', payments.order_id.value_counts()), ('multi_review_no_order_inflation', reviews.order_id.value_counts())]:
        ids = counts[counts > 1].index
        compare(label, all_orders[all_orders.order_id.isin(ids)], actual_orders[actual_orders.order_id.isin(ids)], ['order_id'], ['order_id', 'merchandise_cents', 'freight_cents', 'payment_cents'])
    compare('order_financial_preaggregation', financials, sql_frame('order_financials'), ['order_id'], ['order_id', 'item_count', 'merchandise_cents', 'freight_cents'])
    compare('payment_preaggregation', payment_agg, sql_frame('order_payment_agg'), ['order_id'], ['order_id', 'payment_count', 'payment_cents'])
    compare('review_preaggregation', review_agg, sql_frame('order_review_agg'), ['order_id'], ['order_id', 'review_count', 'review_mean', 'latest_review_score'])
    item_actual = pd.DataFrame(query_rows('SELECT order_id,item_id,product_id,seller_id,price,freight FROM mart.order_item_fact'))
    item_actual['merchandise_cents'] = item_actual.price.map(cents)
    item_actual['freight_cents'] = item_actual.freight.map(cents)
    items['item_id'] = items.order_item_id.astype(int)
    compare('all_item_rows_and_amounts', items, item_actual, ['order_id', 'item_id'], ['order_id', 'item_id', 'product_id', 'seller_id', 'merchandise_cents', 'freight_cents'])

    eligible = all_orders[all_orders.is_eligible].copy()
    overview = pd.DataFrame([{
        'orders': len(eligible), 'users': eligible.customer_unique_id.nunique(),
        'merchandise_cents': eligible.merchandise_cents.sum(), 'freight_cents': eligible.freight_cents.sum(),
        'payment_cents': eligible.payment_cents.sum(), 'average_order_value': eligible.merchandise_cents.sum()/100/len(eligible),
        'delivery_days': eligible.delivery_days.mean(), 'delivery_n': eligible.delivery_days.count(),
        'late_rate': eligible.is_late.mean(), 'late_n': eligible.is_late.count(),
        'review_mean': eligible.review_mean.mean(), 'reviewed_orders': eligible.review_mean.count(),
    }])
    compare('overview_money_users_delivery_review', overview, sql_frame('kpi_overview'), ['orders'], list(overview.columns))
    status = all_orders.groupby('status').size().rename('orders').reset_index()
    status['order_share'] = status.orders / status.orders.sum()
    compare('all_status_distribution', status, sql_frame('order_status_distribution'), ['status'], list(status.columns))
    monthly = eligible.groupby('month_start').agg(orders=('order_id', 'size'), users=('customer_unique_id', 'nunique'), merchandise_cents=('merchandise_cents', 'sum'), freight_cents=('freight_cents', 'sum'), payment_cents=('payment_cents', 'sum'))
    monthly = monthly.reindex(pd.date_range(eligible.month_start.min(), eligible.month_start.max(), freq='MS'), fill_value=0).rename_axis('month_start').reset_index()
    first_date = eligible.purchased_at.min().normalize()
    first_full = first_date if first_date.day == 1 else first_date.to_period('M').start_time + pd.offsets.MonthBegin()
    end = eligible.month_start.max()
    monthly['is_complete'] = monthly.month_start.ge(first_full) & monthly.month_start.lt(end)
    monthly['average_order_value'] = monthly.merchandise_cents.div(100).div(monthly.orders.replace(0, float('nan')))
    compare('monthly_including_empty_and_partial', monthly, sql_frame('monthly_kpis'), ['month_start'], list(monthly.columns))
    product = frames['products'][['product_id', 'product_category_name']].copy()
    product['category'] = product.product_category_name.replace('', '__unknown__')
    eligible_items = items.merge(eligible[['order_id', 'month_start']], on='order_id', validate='many_to_one').merge(product[['product_id', 'category']], validate='many_to_one')
    for view, keys in [('category_ranking', ['category']), ('category_monthly', ['month_start', 'category'])]:
        groups = eligible_items.groupby(keys).agg(orders=('order_id', 'nunique'), items=('order_id', 'size'), merchandise_cents=('merchandise_cents', 'sum'), freight_cents=('freight_cents', 'sum')).reset_index()
        if view == 'category_ranking':
            groups['contribution'] = groups.merchandise_cents / groups.merchandise_cents.sum()
            groups['sales_rank'] = groups.merchandise_cents.rank(method='dense', ascending=False).astype(int)
        compare(view, groups, sql_frame(view), keys, list(groups.columns))
    region = eligible.groupby('customer_state').agg(orders=('order_id', 'size'), users=('customer_unique_id', 'nunique'), merchandise_cents=('merchandise_cents', 'sum'), freight_cents=('freight_cents', 'sum')).reset_index().rename(columns={'customer_state': 'state'})
    region['contribution'] = region.merchandise_cents / region.merchandise_cents.sum()
    compare('region_sales', region, sql_frame('region_sales'), ['state'], list(region.columns))
    scores = eligible.groupby('latest_review_score').size().rename('orders').reset_index().rename(columns={'latest_review_score': 'score'})
    scores['share'] = scores.orders / scores.orders.sum()
    compare('review_distribution_one_per_order', scores, sql_frame('review_distribution'), ['score'], list(scores.columns))

    rfm = pandas_rfm(eligible)
    compare('every_user_rfm_and_tied_scores', rfm, sql_frame('customer_rfm'), ['customer_unique_id'], list(rfm.columns))
    segments = rfm.groupby('segment').agg(users=('customer_unique_id', 'size'), merchandise_cents=('monetary_cents', 'sum')).reset_index()
    segments['user_share'] = segments.users / len(rfm)
    segments['contribution'] = segments.merchandise_cents / segments.merchandise_cents.sum()
    compare('rfm_segments', segments, sql_frame('rfm_segments'), ['segment'], list(segments.columns))
    distribution = rfm.groupby('frequency').size().rename('users').reset_index()
    distribution['share'] = distribution.users / len(rfm)
    compare('repurchase_frequency_distribution', distribution, sql_frame('repurchase_distribution'), ['frequency'], list(distribution.columns))
    summary = pd.DataFrame([{'users': len(rfm), 'repeat_users': int(rfm.frequency.ge(2).sum()), 'repeat_rate': rfm.frequency.ge(2).mean()}])
    # Normalize numeric conversion through the common exact/ratio comparison helper.
    summary['repeat_rate'] = summary.repeat_rate.astype(float)
    actual_summary = sql_frame('repurchase_summary')
    actual_summary['repeat_rate'] = actual_summary.repeat_rate.astype(float)
    compare('repurchase_unique_customers', summary, actual_summary, ['users'], list(summary.columns))
    cohort = pandas_cohort(eligible)
    compare('every_cohort_cell_including_unobserved_nulls', cohort, sql_frame('cohort_retention'), ['cohort_month', 'month_age'], list(cohort.columns))
    cohort_sizes = cohort[cohort.month_age.eq(0)][['cohort_month', 'new_users']]
    compare('cohort_new_users', cohort_sizes, sql_frame('cohort_sizes'), ['cohort_month'], list(cohort_sizes.columns))

    geo = frames['geolocation'].rename(columns={'geolocation_zip_code_prefix': 'zip_code', 'geolocation_lat': 'latitude', 'geolocation_lng': 'longitude'})
    geo['zip_code'] = geo.zip_code.str.zfill(5)
    geo[['latitude', 'longitude']] = geo[['latitude', 'longitude']].astype(float)
    geo = geo.drop_duplicates()
    valid = geo.latitude.between(-90, 90) & geo.longitude.between(-180, 180)
    coordinates = geo[valid].groupby('zip_code')[['latitude', 'longitude']].median()
    geographic = geo.groupby('zip_code').size().rename('distinct_source_rows').to_frame().join(coordinates)
    geographic['valid_coordinate_rows'] = geo[valid].groupby('zip_code').size().reindex(geographic.index, fill_value=0)
    geographic = geographic.reset_index()
    actual_geo = sql_frame('dim_geolocation')
    compare('deduplicated_geolocation', geographic, actual_geo, ['zip_code'], list(geographic.columns))
    expanded = actual_orders.merge(sql_frame('dim_customer')[['customer_id', 'geo_zip']], on='customer_id', validate='many_to_one').merge(actual_geo[['zip_code']], left_on='geo_zip', right_on='zip_code', how='left', validate='many_to_one')
    compare('geolocation_join_no_inflation', actual_orders, expanded, ['order_id'], ['order_id', 'merchandise_cents'])
    report = {'passed': True, 'money_comparison': 'exact integer cents; floating averages/coordinates tolerance 1e-10', 'checks': checks}
    save_json(report, output)
    return report
