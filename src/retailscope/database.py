"""Database operations: raw layer only for P0. No silently fabricated CSV data."""
import os
from pathlib import Path

from .contracts import SOURCES
from .audit import audit_all, DataContractError


def _connect():
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("未安装 psycopg。请执行 pip install -e '.[dev]'。") from exc
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("缺少 DATABASE_URL。请从 .env.example 复制 .env 并设置本地数据库连接。")
    try:
        return psycopg.connect(url, connect_timeout=10)
    except Exception as exc:
        raise RuntimeError("PostgreSQL 连接失败。请先执行 docker compose up -d db，并核对 .env。") from exc


def init_db(script: Path) -> None:
    if not script.is_file():
        raise FileNotFoundError(f"SQL schema 不存在: {script}")
    with _connect() as conn:
        conn.execute(script.read_text(encoding="utf-8"))


def db_status() -> dict:
    with _connect() as conn:
        row = conn.execute("SELECT current_database(), current_user, version()").fetchone()
    return {"database": row[0], "user": row[1], "server": row[2].splitlines()[0]}


def load_raw(source: Path) -> dict:
    """Validate all sources first, then atomic TRUNCATE + streaming COPY all 9 tables."""
    audit = audit_all(source)
    if audit["has_blocking_issues"]:
        raise DataContractError("原始 CSV 有结构性/重复键/类型异常，请先处理；数据库未修改。")
    try:
        from psycopg import sql
    except ImportError as exc:
        raise RuntimeError("未安装 psycopg。请执行 pip install -e '.[dev]'。") from exc
    actual = {}
    with _connect() as conn:
        with conn.transaction():
            for spec in SOURCES:
                conn.execute(sql.SQL("TRUNCATE TABLE {}.{}").format(sql.Identifier("raw"), sql.Identifier(spec.table_name)))
            for spec in SOURCES:
                statement = sql.SQL("COPY {}.{} ({}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE, NULL '')").format(
                    sql.Identifier("raw"), sql.Identifier(spec.table_name),
                    sql.SQL(", ").join(map(sql.Identifier, spec.columns)),
                )
                with conn.cursor() as cur:
                    with cur.copy(statement) as copy:
                        with (source / spec.file_name).open("rb") as fh:
                            while chunk := fh.read(1024 * 1024):
                                copy.write(chunk)
                with conn.cursor() as cur:
                    cur.execute(sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                        sql.Identifier("raw"), sql.Identifier(spec.table_name)
                    ))
                    count = cur.fetchone()[0]
                expected = next(r["row_count"] for r in audit["tables"] if r["table"] == spec.table_name)
                if count != expected:
                    raise RuntimeError(f"{spec.table_name} 入库行数不匹配：CSV {expected}，DB {count}；已回滚。")
                actual[spec.table_name] = count
    return {"imported_rows": actual, "total_imported_rows": sum(actual.values())}


def basic_relational_quality() -> dict:
    """Read-only checks: avoid implicit claims that 'duplicates' always mean errors."""
    queries = {
        "orders_duplicate_id": "SELECT count(*) - count(DISTINCT order_id) FROM raw.orders",
        "customers_duplicate_id": "SELECT count(*) - count(DISTINCT customer_id) FROM raw.customers",
        "orders_missing_customers": "SELECT count(*) FROM raw.orders o LEFT JOIN raw.customers c ON c.customer_id=o.customer_id WHERE c.customer_id IS NULL",
        "items_missing_orders": "SELECT count(*) FROM raw.order_items i LEFT JOIN raw.orders o ON o.order_id=i.order_id WHERE o.order_id IS NULL",
        "payments_missing_orders": "SELECT count(*) FROM raw.order_payments p LEFT JOIN raw.orders o ON o.order_id=p.order_id WHERE o.order_id IS NULL",
        "reviews_missing_orders": "SELECT count(*) FROM raw.order_reviews r LEFT JOIN raw.orders o ON o.order_id=r.order_id WHERE o.order_id IS NULL",
        "items_missing_products": "SELECT count(*) FROM raw.order_items i WHERE NOT EXISTS (SELECT 1 FROM raw.products p WHERE p.product_id=i.product_id)",
        "items_missing_sellers": "SELECT count(*) FROM raw.order_items i WHERE NOT EXISTS (SELECT 1 FROM raw.sellers s WHERE s.seller_id=i.seller_id)",
        "products_missing_translation": "SELECT count(*) FROM raw.products p WHERE NULLIF(btrim(p.product_category_name),'') IS NOT NULL AND NOT EXISTS (SELECT 1 FROM raw.category_translation t WHERE t.product_category_name=p.product_category_name)",
        "customers_missing_geolocation": "SELECT count(*) FROM raw.customers c WHERE NOT EXISTS (SELECT 1 FROM raw.geolocation g WHERE g.geolocation_zip_code_prefix=c.customer_zip_code_prefix)",
        "sellers_missing_geolocation": "SELECT count(*) FROM raw.sellers s WHERE NOT EXISTS (SELECT 1 FROM raw.geolocation g WHERE g.geolocation_zip_code_prefix=s.seller_zip_code_prefix)",
        "orders_without_items": "SELECT count(*) FROM raw.orders o WHERE NOT EXISTS (SELECT 1 FROM raw.order_items i WHERE i.order_id=o.order_id)",
        "orders_without_payments": "SELECT count(*) FROM raw.orders o WHERE NOT EXISTS (SELECT 1 FROM raw.order_payments p WHERE p.order_id=o.order_id)",
        "orders_without_reviews": "SELECT count(*) FROM raw.orders o WHERE NOT EXISTS (SELECT 1 FROM raw.order_reviews r WHERE r.order_id=o.order_id)",
        "multiple_payment_orders": "SELECT count(*) FROM (SELECT order_id FROM raw.order_payments GROUP BY order_id HAVING count(*)>1) x",
        "multiple_review_orders": "SELECT count(*) FROM (SELECT order_id FROM raw.order_reviews GROUP BY order_id HAVING count(*)>1) x",
    }
    result = {}
    with _connect() as conn:
        for metric, query in queries.items():
            result[metric] = conn.execute(query).fetchone()[0]
    return {"checks": result, "notes": "多次支付/多条评价可能是真实现象，提醒 P1 先聚合后 JOIN"}
