"""Streaming, reproducible validation before any destructive DB operation."""
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import csv
import json
import hashlib

from .contracts import SOURCES, SourceSpec


class DataContractError(ValueError):
    """Data is missing or does not match the declared input schema."""


def missing_files(root: Path) -> list[str]:
    return [s.file_name for s in SOURCES if not (root / s.file_name).is_file()]


def audit_csv(root: Path, spec: SourceSpec) -> dict:
    path = root / spec.file_name
    if not path.is_file():
        raise DataContractError(f"缺少文件：{path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, strict=True)
        if tuple(reader.fieldnames or ()) != spec.columns:
            raise DataContractError(
                f"{spec.file_name} 表头不匹配。期望 {list(spec.columns)}，"
                f"实际 {reader.fieldnames}"
            )
        row_count = 0
        missing = Counter()
        invalid_numeric = Counter()
        invalid_date = Counter()
        key_seen: set[tuple[str, ...]] = set()
        duplicate_key_count = 0
        missing_unique_key_rows = 0
        malformed_rows = 0
        row_seen = set()
        duplicate_rows = 0
        for row in reader:
            row_count += 1
            if None in row or any(v is None for v in row.values()):
                malformed_rows += 1
                continue
            digest = hashlib.sha256(json.dumps(list(row.values()), ensure_ascii=False).encode("utf-8")).digest()
            if digest in row_seen:
                duplicate_rows += 1
            row_seen.add(digest)
            for col, value in row.items():
                if value is None or not value.strip():
                    missing[col] += 1
            if spec.unique_key:
                key = tuple(row.get(col, "") or "" for col in spec.unique_key)
                if any(not v.strip() for v in key):
                    missing_unique_key_rows += 1
                elif key in key_seen:
                    duplicate_key_count += 1
                else:
                    key_seen.add(key)
            for col in spec.numeric_columns:
                raw = row.get(col, "") or ""
                if raw.strip():
                    try:
                        if not Decimal(raw.strip()).is_finite():
                            raise InvalidOperation
                    except (InvalidOperation, ValueError):
                        invalid_numeric[col] += 1
            for col in spec.date_columns:
                raw = row.get(col, "") or ""
                if raw.strip():
                    try:
                        datetime.fromisoformat(raw.strip())
                    except ValueError:
                        invalid_date[col] += 1
    return {
        "source_file": spec.file_name,
        "table": spec.table_name,
        "row_count": row_count,
        "duplicate_full_rows": duplicate_rows,
        "duplicate_unique_key_rows": duplicate_key_count if spec.unique_key else None,
        "missing_unique_key_rows": missing_unique_key_rows if spec.unique_key else None,
        "malformed_rows": malformed_rows,
        "missing_by_column": dict(sorted(missing.items())),
        "invalid_numeric_by_column": dict(sorted(invalid_numeric.items())),
        "invalid_date_by_column": dict(sorted(invalid_date.items())),
    }


def audit_all(root: Path) -> dict:
    missing = missing_files(root)
    if missing:
        raise DataContractError("缺少以下 Olist 原始文件：\n" + "\n".join(f"  - {name}" for name in missing))
    reports = [audit_csv(root, spec) for spec in SOURCES]
    return {
        "source": "Olist Brazilian E-Commerce Public Dataset",
        "source_url": "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce",
        "license": "CC BY-NC-SA 4.0",
        "scope": "raw CSV structural audit (no claim about relational integrity before DB loading)",
        "tables": reports,
        "total_source_rows": sum(r["row_count"] for r in reports),
        "has_blocking_issues": any(
            r["row_count"] == 0 or r["malformed_rows"] > 0
            or (r["missing_unique_key_rows"] or 0) > 0
            or (r["duplicate_unique_key_rows"] or 0) > 0
            or any(r["invalid_numeric_by_column"].values())
            or any(r["invalid_date_by_column"].values())
            for r in reports
        ),
    }


def audit_relations(root: Path) -> dict:
    """Independent file-side checks; no many-to-many joins or source cleaning."""
    import pandas as pd

    fields = {
        "orders": ["order_id", "customer_id"],
        "customers": ["customer_id", "customer_unique_id", "customer_zip_code_prefix"],
        "order_items": ["order_id", "product_id", "seller_id"],
        "order_payments": ["order_id"], "order_reviews": ["order_id", "review_id"],
        "products": ["product_id", "product_category_name"],
        "sellers": ["seller_id", "seller_zip_code_prefix"],
        "geolocation": ["geolocation_zip_code_prefix"],
        "category_translation": ["product_category_name"],
    }
    frames = {
        s.table_name: pd.read_csv(root / s.file_name, usecols=fields[s.table_name],
                                  dtype=str, keep_default_na=False)
        for s in SOURCES
    }
    checks = {}
    relations = [
        ("orders_missing_customers", "orders", "customer_id", "customers", "customer_id"),
        ("items_missing_orders", "order_items", "order_id", "orders", "order_id"),
        ("payments_missing_orders", "order_payments", "order_id", "orders", "order_id"),
        ("reviews_missing_orders", "order_reviews", "order_id", "orders", "order_id"),
        ("items_missing_products", "order_items", "product_id", "products", "product_id"),
        ("items_missing_sellers", "order_items", "seller_id", "sellers", "seller_id"),
        ("products_missing_translation", "products", "product_category_name", "category_translation", "product_category_name"),
        ("customers_missing_geolocation", "customers", "customer_zip_code_prefix", "geolocation", "geolocation_zip_code_prefix"),
        ("sellers_missing_geolocation", "sellers", "seller_zip_code_prefix", "geolocation", "geolocation_zip_code_prefix"),
        ("orders_without_items", "orders", "order_id", "order_items", "order_id"),
        ("orders_without_payments", "orders", "order_id", "order_payments", "order_id"),
        ("orders_without_reviews", "orders", "order_id", "order_reviews", "order_id"),
    ]
    for name, child, key, parent, parent_key in relations:
        values = frames[child][key]
        absent = ~values.isin(frames[parent][parent_key])
        if name == "products_missing_translation":
            absent &= values.str.strip().ne("")
        checks[name] = int(absent.sum())
    for table, name in (("order_payments", "multiple_payment_orders"), ("order_reviews", "multiple_review_orders")):
        checks[name] = int((frames[table]["order_id"].value_counts() > 1).sum())
    return {
        "checks": checks,
        "nonunique_reference_fields": {
            "review_id_duplicate_rows": int(frames["order_reviews"]["review_id"].duplicated().sum()),
            "geolocation_zip_duplicate_rows": int(frames["geolocation"]["geolocation_zip_code_prefix"].duplicated().sum()),
            "customer_unique_id_duplicate_rows": int(frames["customers"]["customer_unique_id"].duplicated().sum()),
        },
        "notes": "CSV 独立检查；缺少翻译/邮编覆盖属于源数据告警，不清洗 raw。重复唯一用户标识、评价 ID 和邮编不作为非法主键。",
    }


def write_json_report(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
