"""P0 acceptance runner: deliberately reloads only the nine raw source tables."""
from pathlib import Path

from .audit import audit_all, audit_relations, write_json_report
from .contracts import SOURCES
from .database import _connect, basic_relational_quality, db_status, load_raw


def snapshot_raw() -> dict:
    from psycopg import sql

    result = {}
    with _connect() as conn:
        for spec in SOURCES:
            # Order-independent fingerprint includes NULLs and duplicate multiplicities.
            row = conn.execute(sql.SQL(
                "SELECT count(*), sum(('x' || substr(md5(row_to_json(t)::text), 1, 15))"
                "::bit(60)::bigint)::text FROM {}.{} t"
            ).format(sql.Identifier("raw"), sql.Identifier(spec.table_name))).fetchone()
            result[spec.table_name] = {"rows": row[0], "fingerprint": row[1]}
    return result


def verify_import(source: Path, output: Path) -> dict:
    report = {"status": "running", "database": db_status()}
    write_json_report(report, output)
    if "PostgreSQL 16." not in report["database"]["server"]:
        raise RuntimeError("P0 要求 PostgreSQL 16；未执行导入。")
    audit = audit_all(source)
    report["csv_rows"] = {r["table"]: r["row_count"] for r in audit["tables"]}
    for run in ("first", "second"):
        report[run + "_import"] = load_raw(source)
        report[run + "_snapshot"] = snapshot_raw()
        write_json_report(report, output)
    report["counts_match_csv"] = all(
        report["first_snapshot"][s.table_name]["rows"] == report["csv_rows"][s.table_name]
        == report["second_snapshot"][s.table_name]["rows"] for s in SOURCES
    )
    report["idempotent"] = report["first_snapshot"] == report["second_snapshot"]
    report["relational_quality"] = basic_relational_quality()
    report["csv_relational_quality"] = audit_relations(source)
    file_checks = report["csv_relational_quality"]["checks"]
    report["relations_match_csv"] = all(
        report["relational_quality"]["checks"].get(key) == value for key, value in file_checks.items()
    )
    report["status"] = "passed" if all(report[key] for key in (
        "counts_match_csv", "idempotent", "relations_match_csv"
    )) else "failed"
    write_json_report(report, output)
    if report["status"] != "passed":
        raise RuntimeError("真实数据导入验收失败，查看验收 JSON。")
    return report
