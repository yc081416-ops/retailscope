from pathlib import Path

from retailscope.__main__ import main
from retailscope.contracts import SOURCES


def test_check_data_without_csv_exits_with_error(tmp_path, capsys):
    code = main(["check-data", "--source", str(tmp_path)])
    assert code == 2
    assert "缺少以下 Olist" in capsys.readouterr().err


def test_sql_schema_includes_all_source_tables():
    project_root = Path(__file__).resolve().parents[1]
    sql = (project_root / "sql" / "00_raw.sql").read_text(encoding="utf-8")
    for spec in SOURCES:
        assert f'raw."{spec.table_name}"' in sql
        for col in spec.columns:
            assert f'"{col}" TEXT' in sql
