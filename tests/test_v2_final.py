"""Final semantic regression: P3 order-mean and latest-score definitions must stay distinct."""
from retailscope.bi.components import evidence_path
import json
from pathlib import Path
from sqlalchemy import text
import pytest

from api.queries import database


def test_f05_uses_order_review_mean_and_latest_score_only_for_low_rating():
    result=json.loads(evidence_path('reports/p3/analysis.json').read_text(encoding='utf-8'))['association']
    with database().connect() as conn:
        rows=conn.execute(text("""SELECT is_late,count(*) AS n,avg(review_mean) AS order_mean,
            avg(latest_review_score) AS latest_mean,
            avg((latest_review_score<=2)::integer) AS low_rate
            FROM mart.eligible_orders WHERE is_late IS NOT NULL AND review_mean IS NOT NULL
            AND latest_review_score IS NOT NULL AND customer_unique_id IS NOT NULL
            GROUP BY is_late ORDER BY is_late""")).mappings().all()
    for source,group in zip(rows,result['groups']):
        assert group['n']==source['n']
        assert group['mean_score']==pytest.approx(float(source['order_mean']),abs=1e-12)
        assert abs(group['mean_score']-float(source['latest_mean']))>1e-5
        assert group['low_rate']==pytest.approx(float(source['low_rate']),abs=1e-12)
