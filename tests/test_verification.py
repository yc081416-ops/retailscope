from pathlib import Path

import pytest

from retailscope import verification
from retailscope.contracts import SOURCES


@pytest.mark.parametrize("changed", [False, True])
def test_verification_detects_changed_content(tmp_path, monkeypatch, changed):
    monkeypatch.setattr(verification, "db_status", lambda: {"server": "PostgreSQL 16.0"})
    monkeypatch.setattr(verification, "audit_all", lambda _: {
        "tables": [{"table": s.table_name, "row_count": 1} for s in SOURCES]
    })
    calls = []
    monkeypatch.setattr(verification, "load_raw", lambda _: calls.append(1) or {"total_imported_rows": 9})
    first = {s.table_name: {"rows": 1, "fingerprint": "a"} for s in SOURCES}
    second = {s.table_name: {"rows": 1, "fingerprint": "b" if changed else "a"} for s in SOURCES}
    snapshots = iter([first, second])
    monkeypatch.setattr(verification, "snapshot_raw", lambda: next(snapshots))
    monkeypatch.setattr(verification, "basic_relational_quality", lambda: {"checks": {"missing": 0}})
    monkeypatch.setattr(verification, "audit_relations", lambda _: {"checks": {"missing": 0}})
    if changed:
        with pytest.raises(RuntimeError, match="验收失败"):
            verification.verify_import(Path("unused"), tmp_path / "report.json")
    else:
        result = verification.verify_import(Path("unused"), tmp_path / "report.json")
        assert result["status"] == "passed" and result["relations_match_csv"]
    assert len(calls) == 2


def test_rejects_wrong_server_before_loading(tmp_path, monkeypatch):
    monkeypatch.setattr(verification, "db_status", lambda: {"server": "PostgreSQL 15.0"})
    with pytest.raises(RuntimeError, match="PostgreSQL 16"):
        verification.verify_import(Path("unused"), tmp_path / "report.json")
