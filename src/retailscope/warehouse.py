"""Transactional P1 build and read-only evidence collection. P0 is immutable."""
from datetime import date, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from psycopg import sql

from .database import _connect

SCRIPTS = ('10_core.sql', '20_mart.sql', '30_customer.sql')
TABLES = (
    'dim_geolocation', 'dim_user', 'dim_customer', 'dim_product', 'dim_seller', 'dim_date',
    'analysis_context', 'order_wide', 'order_financials', 'order_payment_agg', 'order_review_agg',
    'order_item_fact', 'kpi_overview', 'order_status_distribution', 'monthly_kpis',
    'category_monthly', 'category_ranking', 'region_sales', 'review_distribution', 'quality_checks',
    'customer_rfm', 'rfm_segments', 'repurchase_distribution', 'repurchase_summary',
    'customer_cohort', 'cohort_sizes', 'cohort_retention',
)


def json_default(value):
    if isinstance(value, (Decimal, date, datetime)):
        return str(value)
    raise TypeError(type(value).__name__)


def save_json(value, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, default=json_default, ensure_ascii=False, indent=2), encoding='utf-8')


def query_rows(statement, params=None):
    with _connect() as conn:
        cursor = conn.execute(statement, params)
        names = [c.name for c in cursor.description]
        return [dict(zip(names, row, strict=True)) for row in cursor]


def build_warehouse(sql_dir=Path('sql')):
    with _connect() as conn:
        with conn.transaction():
            conn.execute("SET LOCAL lock_timeout='10s'")
            conn.execute("SELECT pg_advisory_xact_lock(731902)")
            for script in SCRIPTS:
                conn.execute((sql_dir / script).read_text(encoding='utf-8'))
            # Fatal source anomalies fail closed, rolling back all P1 changes.
            bad = conn.execute("""SELECT
                (SELECT count(*) FROM core.reviews WHERE score NOT BETWEEN 1 AND 5 OR score IS NULL)+
                (SELECT count(*) FROM core.payments WHERE amount<0 OR installments<0)+
                (SELECT count(*) FROM mart.order_wide WHERE customer_unique_id IS NULL)
            """).fetchone()[0]
            if bad:
                raise ValueError(f'P1 source validation failed: {bad} invalid rows')
            for table in TABLES[:12]:
                conn.execute(sql.SQL('ANALYZE mart.{}').format(sql.Identifier(table)))


def snapshot_mart():
    result = {}
    with _connect() as conn:
        for name in TABLES:
            digest = hashlib.sha256()
            count = 0
            with conn.cursor(name='p1_snapshot') as cur:
                cur.execute(sql.SQL('SELECT row_to_json(t)::text FROM mart.{} t ORDER BY row_to_json(t)::text').format(sql.Identifier(name)))
                for row in cur:
                    digest.update(row[0].encode('utf-8') + b'\n')
                    count += 1
            result[name] = {'rows': count, 'sha256': digest.hexdigest()}
    return result


def export_results(directory):
    """Publish every requested SQL result, preserving exact NUMERIC values as strings."""
    import pandas as pd

    result = {}
    for name in TABLES[6:]:
        if name in ('order_wide', 'order_financials', 'order_payment_agg', 'order_review_agg', 'order_item_fact', 'customer_rfm', 'customer_cohort'):
            continue
        rows = query_rows(sql.SQL('SELECT * FROM mart.{} t ORDER BY row_to_json(t)::text').format(sql.Identifier(name)))
        result[name] = rows
        save_json(rows, directory / f'{name}.json')
        pd.DataFrame(rows).to_csv(directory / f'{name}.csv', index=False, encoding='utf-8-sig')
    matrix = pd.DataFrame(result['cohort_retention']).pivot(index='cohort_month', columns='month_age', values='retention')
    matrix.to_csv(directory / 'cohort_matrix.csv', encoding='utf-8-sig', na_rep='NA')
    return result
