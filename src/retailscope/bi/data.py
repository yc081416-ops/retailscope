"""Allowlisted, parameterized SQLAlchemy queries with bounded read-only connections."""
from dataclasses import dataclass
from datetime import date
import logging
import os
from pathlib import Path
import time

from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import String, bindparam, create_engine, text
from sqlalchemy.engine import make_url
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
LOGGER = logging.getLogger('retailscope.bi')
if not LOGGER.handlers:
    (ROOT / 'reports/p2').mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(ROOT / 'reports/p2/queries.log', encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)


class DatabaseUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class Filters:
    start: date
    end: date  # Exclusive.
    states: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.start, date) or not isinstance(self.end, date) or self.start >= self.end:
            raise ValueError('请选择有效日期范围，起始日期不能晚于结束日期。')
        if len(self.states) > 27 or len(self.categories) > 100:
            raise ValueError('筛选项过多。')

    def params(self):
        return dict(start=self.start, end=self.end, states=list(self.states), categories=list(self.categories),
                    all_states=not self.states, all_categories=not self.categories)


@st.cache_resource(show_spinner=False)
def engine():
    load_dotenv(ROOT / '.env')
    try:
        url = make_url(os.environ['DATABASE_URL']).set(drivername='postgresql+psycopg')
        return create_engine(url, pool_pre_ping=True, pool_size=3, max_overflow=2,
            connect_args={'connect_timeout': 5, 'options': '-c default_transaction_read_only=on -c statement_timeout=20000'}, hide_parameters=True)
    except Exception as exc:
        LOGGER.error('connection_configuration_failed type=%s', type(exc).__name__)
        raise DatabaseUnavailable('数据库配置不可用。请检查本地 .env，并确认 PostgreSQL 服务已启动。') from None


SCOPE = """WITH scoped_orders AS (
    SELECT o.* FROM mart.order_wide o
    WHERE o.purchased_at>=:start AND o.purchased_at<:end
      AND (:all_states OR o.customer_state IN :states)
      AND (:all_categories OR EXISTS (
          SELECT 1 FROM mart.order_item_fact i JOIN mart.dim_product p USING(product_id)
          WHERE i.order_id=o.order_id AND p.category IN :categories))
), eligible AS (SELECT * FROM scoped_orders WHERE is_eligible), scoped_items AS (
    SELECT i.*,p.category,o.month_start,o.customer_state
    FROM mart.order_item_fact i JOIN eligible o USING(order_id)
    JOIN mart.dim_product p USING(product_id)
    WHERE (:all_categories OR p.category IN :categories)
)
"""

FILTERED = {
    'overview': """SELECT count(*) AS orders,count(DISTINCT customer_unique_id) AS users,
        coalesce(sum(merchandise),0) AS merchandise,coalesce(sum(freight),0) AS freight,
        coalesce(sum(payment),0) AS payment,sum(merchandise)/NULLIF(count(*),0) AS average_order_value,
        avg(delivery_days) AS delivery_days,count(delivery_days) AS delivery_n,
        avg(is_late::integer) AS late_rate,count(is_late) AS late_n,
        avg(review_mean) AS review_mean,count(review_mean) AS reviewed_orders FROM eligible""",
    'monthly': """SELECT m::date AS month_start,count(o.order_id) AS orders,
        count(DISTINCT o.customer_unique_id) AS users,coalesce(sum(o.merchandise),0) AS merchandise,
        m>=c.first_complete_month AND m<c.observation_end_exclusive
          AND :start<=m AND :end>=m+interval '1 month' AS is_complete
        FROM mart.analysis_context c CROSS JOIN LATERAL generate_series(
          greatest(date_trunc('month',:start::date),date_trunc('month',c.first_purchase)),
          least(date_trunc('month',:end::date-1),date_trunc('month',c.last_purchase)),interval '1 month') m
        LEFT JOIN eligible o ON o.month_start=m::date
        GROUP BY m,c.first_complete_month,c.observation_end_exclusive ORDER BY m""",
    'statuses': 'SELECT status,count(*) AS orders FROM scoped_orders GROUP BY status ORDER BY orders DESC',
    'regions': """SELECT customer_state AS state,count(*) AS orders,coalesce(sum(merchandise),0) AS merchandise,
        sum(merchandise)/NULLIF(sum(sum(merchandise)) OVER(),0) AS contribution FROM eligible GROUP BY 1 ORDER BY merchandise DESC""",
    'categories': """SELECT category,count(DISTINCT order_id) AS orders,count(*) AS items,
        sum(price) AS merchandise,sum(freight) AS freight,
        sum(price)/NULLIF(sum(sum(price)) OVER(),0) AS contribution
        FROM scoped_items GROUP BY category ORDER BY merchandise DESC,category""",
    'product_kpis': """SELECT count(DISTINCT order_id) AS orders,count(*) AS items,
        coalesce(sum(price),0) AS merchandise,coalesce(sum(freight),0) AS freight FROM scoped_items""",
    'category_monthly': """SELECT month_start,category,sum(price) AS merchandise,count(*) AS items,
        count(DISTINCT order_id) AS orders FROM scoped_items GROUP BY 1,2 ORDER BY 1,2""",
    'delivery_histogram': """SELECT floor(delivery_days/5)*5 AS day_start,count(*) AS orders
        FROM eligible WHERE delivery_days IS NOT NULL GROUP BY 1 ORDER BY 1""",
    'reviews': """SELECT latest_review_score AS score,count(*) AS orders FROM eligible
        WHERE latest_review_score IS NOT NULL GROUP BY 1 ORDER BY 1""",
    'delivery_regions': """SELECT customer_state AS state,count(*) AS orders,avg(delivery_days) AS delivery_days,
        count(delivery_days) AS delivery_n,avg(is_late::integer) AS late_rate,count(is_late) AS late_n
        FROM eligible GROUP BY 1 ORDER BY delivery_days DESC NULLS LAST""",
    'late_reviews': """SELECT CASE WHEN is_late THEN '逾期' ELSE '未逾期' END AS delivery_group,
        count(*) AS orders,avg(review_mean) AS review_mean,
        avg((latest_review_score<=2)::integer) AS low_score_rate
        FROM eligible WHERE is_late IS NOT NULL AND review_mean IS NOT NULL GROUP BY is_late ORDER BY is_late""",
}
# Cast syntax is kept separate from SQLAlchemy bind tokens.
FILTERED['monthly'] = FILTERED['monthly'].replace(':start::date', 'CAST(:start AS date)').replace(':end::date', 'CAST(:end AS date)')

FIXED = {
    'context': 'SELECT * FROM mart.analysis_context',
    'bounds': 'SELECT min(calendar_date) AS first_date,max(calendar_date) AS last_date FROM mart.dim_date',
    'states': 'SELECT DISTINCT customer_state AS state FROM mart.order_wide ORDER BY 1',
    'category_options': 'SELECT DISTINCT category FROM mart.dim_product ORDER BY 1',
    'rfm': 'SELECT * FROM mart.rfm_segments ORDER BY users DESC',
    'frequency': 'SELECT * FROM mart.repurchase_distribution ORDER BY frequency',
    'repurchase': 'SELECT * FROM mart.repurchase_summary',
    'cohort': 'SELECT * FROM mart.cohort_retention ORDER BY cohort_month,month_age',
    'new_users': 'SELECT * FROM mart.cohort_sizes ORDER BY cohort_month',
    'quality': 'SELECT * FROM mart.quality_checks',
}


def execute(name, filters=None):
    start = time.perf_counter()
    if name in FILTERED:
        if filters is None:
            raise ValueError('该查询需要统一筛选范围。')
        statement = text(SCOPE + FILTERED[name]).bindparams(bindparam('states', expanding=True, type_=String()), bindparam('categories', expanding=True, type_=String()))
        params = filters.params()
    elif name in FIXED and filters is None:
        statement, params = text(FIXED[name]), {}
    else:
        raise ValueError('不支持的指标查询。')
    try:
        with engine().connect() as conn:
            result = pd.read_sql_query(statement, conn, params=params, coerce_float=False)
        LOGGER.info('query=%s rows=%d seconds=%.3f', name, len(result), time.perf_counter()-start)
        return result
    except DatabaseUnavailable:
        raise
    except Exception as exc:
        LOGGER.error('query=%s failed type=%s', name, type(exc).__name__)
        raise DatabaseUnavailable('数据暂时无法读取。请确认数据库运行正常且 P1 数据仓库已构建，然后点击“重新连接”。') from None


@st.cache_data(ttl=120, max_entries=128, show_spinner=False)
def fetch(name, filters=None):
    return execute(name, filters)


@st.cache_data(ttl=120, show_spinner=False)
def raw_counts():
    from retailscope.contracts import SOURCES
    statement = ' UNION ALL '.join(f"SELECT '{s.table_name}' AS table_name,count(*) AS rows FROM raw.{s.table_name}" for s in SOURCES)
    try:
        with engine().connect() as conn:
            return pd.read_sql_query(text(statement), conn)
    except Exception as exc:
        LOGGER.error('raw_counts_failed type=%s', type(exc).__name__)
        raise DatabaseUnavailable('无法读取原始表计数，请检查数据库连接。') from None
