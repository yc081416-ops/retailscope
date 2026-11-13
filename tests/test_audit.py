import csv
from pathlib import Path

import pytest

from retailscope.audit import audit_all, audit_csv, audit_relations, DataContractError, missing_files
from retailscope.contracts import SOURCES


def write_csv(path, columns, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)


def fixture_row(spec):
    vals = []
    for col in spec.columns:
        if col in spec.numeric_columns:
            vals.append("1.50")
        elif col in spec.date_columns:
            vals.append("2018-01-01 01:00:00")
        else:
            vals.append("test_value")
    return vals


@pytest.fixture
def complete_raw(tmp_path):
    for spec in SOURCES:
        write_csv(tmp_path / spec.file_name, spec.columns, [fixture_row(spec)])
    return tmp_path


def test_missing_nine_files_listed(tmp_path):
    assert len(missing_files(tmp_path)) == 9
    with pytest.raises(DataContractError, match="olist_orders_dataset.csv"):
        audit_all(tmp_path)


def test_empty_header_does_not_pass(tmp_path):
    spec = SOURCES[0]
    write_csv(tmp_path / spec.file_name, ["wrong_name"], [["x"]])
    with pytest.raises(DataContractError, match="表头不匹配"):
        audit_csv(tmp_path, spec)


def test_complete_sources_are_audited(complete_raw):
    report = audit_all(complete_raw)
    assert report["total_source_rows"] == 9
    assert len(report["tables"]) == 9
    assert not report["has_blocking_issues"]


def test_composite_key_duplicate_is_detected(complete_raw):
    spec = next(s for s in SOURCES if s.table_name == "order_items")
    row = fixture_row(spec)
    write_csv(complete_raw / spec.file_name, spec.columns, [row, row])
    report = audit_all(complete_raw)
    item_report = next(r for r in report["tables"] if r["table"] == "order_items")
    assert report["has_blocking_issues"]
    assert item_report["duplicate_unique_key_rows"] == 1


def test_invalid_numeric_and_date_are_detected(complete_raw):
    payment = next(s for s in SOURCES if s.table_name == "order_payments")
    row = fixture_row(payment)
    row[payment.columns.index("payment_value")] = "not_a_number"
    write_csv(complete_raw / payment.file_name, payment.columns, [row])
    orders = next(s for s in SOURCES if s.table_name == "orders")
    order_row = fixture_row(orders)
    order_row[orders.columns.index("order_purchase_timestamp")] = "2026-99-99"
    write_csv(complete_raw / orders.file_name, orders.columns, [order_row])
    report = audit_all(complete_raw)
    assert report["has_blocking_issues"]
    assert next(r for r in report["tables"] if r["table"] == "order_payments")["invalid_numeric_by_column"]["payment_value"] == 1
    assert next(r for r in report["tables"] if r["table"] == "orders")["invalid_date_by_column"]["order_purchase_timestamp"] == 1


def test_nonunique_reviews_are_not_assumed_to_be_unique(complete_raw):
    spec = next(s for s in SOURCES if s.table_name == "order_reviews")
    row = fixture_row(spec)
    write_csv(complete_raw / spec.file_name, spec.columns, [row, row])
    report = audit_all(complete_raw)
    reviews = next(r for r in report["tables"] if r["table"] == "order_reviews")
    assert reviews["duplicate_unique_key_rows"] is None
    assert reviews["duplicate_full_rows"] == 1
    assert not report["has_blocking_issues"]


def test_missing_key_is_counted(complete_raw):
    spec = next(s for s in SOURCES if s.table_name == "orders")
    row = fixture_row(spec)
    row[0] = ""
    write_csv(complete_raw / spec.file_name, spec.columns, [row])
    report = audit_all(complete_raw)
    result = next(r for r in report["tables"] if r["table"] == "orders")
    assert result["missing_by_column"]["order_id"] == 1
    assert result["missing_unique_key_rows"] == 1
    assert report["has_blocking_issues"]


def test_empty_data_file_is_blocked(complete_raw):
    spec = next(s for s in SOURCES if s.table_name == "orders")
    write_csv(complete_raw / spec.file_name, spec.columns, [])
    report = audit_all(complete_raw)
    assert report["has_blocking_issues"]
    assert next(r for r in report["tables"] if r["table"] == "orders")["row_count"] == 0


def test_relations_count_child_rows_without_join_expansion(complete_raw):
    spec = next(s for s in SOURCES if s.table_name == "order_items")
    row = fixture_row(spec)
    row[spec.columns.index("product_id")] = "absent_product"
    write_csv(complete_raw / spec.file_name, spec.columns, [row, row])
    report = audit_relations(complete_raw)
    assert report["checks"]["items_missing_products"] == 2
    assert report["checks"]["orders_missing_customers"] == 0
