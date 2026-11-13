"""CLI entry: python -m retailscope [check-data|init-db|load-data|db-status|db-quality]."""
import argparse
import csv
import json
from pathlib import Path
import sys

from dotenv import load_dotenv

from .audit import audit_all, audit_relations, write_json_report, DataContractError


def main(argv=None) -> int:
    load_dotenv()
    p = argparse.ArgumentParser(description="RetailScope P0 CLI")
    sub = p.add_subparsers(dest="command", required=True)
    download = sub.add_parser("download-data", help="Download official Olist CSVs using kagglehub")
    download.add_argument("--source", type=Path, default=Path("data/raw"))
    download.add_argument("--output", type=Path, default=Path("reports/download_manifest.json"))
    check = sub.add_parser("check-data", help="CSV contract and source profiling; no database required")
    check.add_argument("--source", type=Path, default=Path("data/raw"))
    check.add_argument("--output", type=Path, default=Path("reports/raw_quality.json"))
    init = sub.add_parser("init-db", help="Create 9 raw tables (requires PostgreSQL)")
    init.add_argument("--schema", type=Path, default=Path("sql/00_raw.sql"))
    loader = sub.add_parser("load-data", help="Atomic, repeatable CSV -> PostgreSQL import")
    loader.add_argument("--source", type=Path, default=Path("data/raw"))
    verify = sub.add_parser("verify-import", help="Reload raw tables twice and verify counts/content fingerprints")
    verify.add_argument("--source", type=Path, default=Path("data/raw"))
    verify.add_argument("--output", type=Path, default=Path("reports/import_verification.json"))
    sub.add_parser("db-status", help="Check PostgreSQL connectivity")
    quality = sub.add_parser("db-quality", help="Read-only relational integrity checks")
    quality.add_argument("--output", type=Path, default=Path("reports/db_quality.json"))
    args = p.parse_args(argv)
    try:
        if args.command == "download-data":
            from .download import download_data
            print(json.dumps(download_data(args.source, args.output), ensure_ascii=False, indent=2))
            return 0
        if args.command == "check-data":
            report = audit_all(args.source)
            report["relational_quality"] = audit_relations(args.source)
            write_json_report(report, args.output)
            print(json.dumps({
                "report": str(args.output),
                "rows": report["total_source_rows"],
                "by_table": {t["table"]: t["row_count"] for t in report["tables"]},
                "blocking": report["has_blocking_issues"],
            }, ensure_ascii=False, indent=2))
            return 2 if report["has_blocking_issues"] else 0
        from .database import init_db, load_raw, db_status, basic_relational_quality
        if args.command == "verify-import":
            from .verification import verify_import
            print(json.dumps(verify_import(args.source, args.output), ensure_ascii=False, indent=2))
            return 0
        if args.command == "init-db":
            init_db(args.schema)
            print("已创建 raw schema 和 9 张原始表（如果存在则保留）。")
        elif args.command == "load-data":
            print(json.dumps(load_raw(args.source), ensure_ascii=False, indent=2))
        elif args.command == "db-status":
            print(json.dumps(db_status(), ensure_ascii=False, indent=2))
        elif args.command == "db-quality":
            report = basic_relational_quality()
            write_json_report(report, args.output)
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (DataContractError, OSError, RuntimeError, ValueError, csv.Error) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
