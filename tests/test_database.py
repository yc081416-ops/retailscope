"""Live read-only check, explicitly skipped until the P0 database is available."""
import os

from dotenv import load_dotenv
import pytest

from retailscope.database import db_status


def test_postgresql_16_connection():
    load_dotenv()
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("未配置 DATABASE_URL；尚未验证真实 PostgreSQL 连接")
    assert "PostgreSQL 16." in db_status()["server"]
