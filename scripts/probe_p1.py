"""Read-only P0 recheck and P1 boundary inspection; never rewrites P0 evidence."""
import json
from pathlib import Path
from dotenv import load_dotenv
from retailscope.audit import write_json_report
from retailscope.database import _connect, db_status
from retailscope.verification import snapshot_raw

load_dotenv()
baseline = json.loads(Path('reports/import_verification.json').read_text())
snapshot = snapshot_raw()
assert snapshot == baseline['second_snapshot'], 'raw changed since P0 acceptance'
queries = {
    'purchase_bounds': "SELECT min(order_purchase_timestamp), max(order_purchase_timestamp), max(order_purchase_timestamp) FILTER (WHERE order_status='delivered') FROM raw.orders",
    'status': 'SELECT order_status,count(*) FROM raw.orders GROUP BY 1 ORDER BY 1',
    'delivered_missing': "SELECT count(*) FILTER (WHERE i.order_id IS NULL),count(*) FILTER (WHERE p.order_id IS NULL),count(*) FILTER (WHERE NULLIF(order_delivered_customer_date,'')::timestamp < order_purchase_timestamp::timestamp) FROM raw.orders o LEFT JOIN (SELECT DISTINCT order_id FROM raw.order_items) i USING(order_id) LEFT JOIN (SELECT DISTINCT order_id FROM raw.order_payments) p USING(order_id) WHERE order_status='delivered'",
    'invalid_values': "SELECT count(*) FILTER(WHERE price::numeric<0 OR freight_value::numeric<0) FROM raw.order_items",
}
with _connect() as conn:
    results = {key: conn.execute(sql).fetchall() for key, sql in queries.items()}
report = {'database': db_status(), 'raw_unchanged_since_p0': True, 'raw': snapshot, 'probes': results}
write_json_report(report, Path('reports/p1/p0_recheck.json'))
print(json.dumps(report, ensure_ascii=False, indent=2))
