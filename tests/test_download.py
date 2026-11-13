"""Small CSV fixtures exercise failure paths, never used as project source data."""
import csv
import hashlib

import pytest

from retailscope.audit import DataContractError
from retailscope.contracts import SOURCES
from retailscope.download import download_data


def make_sources(root):
    root.mkdir()
    for spec in SOURCES:
        with (root / spec.file_name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(spec.columns)
            writer.writerow([
                "1" if col in spec.numeric_columns else
                "2018-01-01 00:00:00" if col in spec.date_columns else "fixture"
                for col in spec.columns
            ])


def test_download_and_repeat_preserve_bytes(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    make_sources(cache)
    calls = []
    monkeypatch.setattr("kagglehub.dataset_download", lambda handle: calls.append(handle) or str(cache))
    target = tmp_path / "raw"
    output = tmp_path / "manifest.json"
    first = download_data(target, output)
    second = download_data(target, tmp_path / "repeat.json")
    assert len(calls) == 1
    assert not first["download_skipped"] and second["download_skipped"]
    assert first["files"] == second["files"]
    assert len(first["files"]) == 9
    for item in first["files"]:
        assert item["sha256"] == hashlib.sha256((cache / item["file"]).read_bytes()).hexdigest()


def test_incomplete_cache_does_not_copy(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    cache.mkdir()
    monkeypatch.setattr("kagglehub.dataset_download", lambda _: str(cache))
    target = tmp_path / "raw"
    with pytest.raises(DataContractError, match="缺少文件"):
        download_data(target, tmp_path / "report.json")
    assert list(target.iterdir()) == []


def test_library_error_does_not_expose_credentials(tmp_path, monkeypatch):
    def fail(_):
        raise RuntimeError("secret-token-in-url")
    monkeypatch.setattr("kagglehub.dataset_download", fail)
    with pytest.raises(RuntimeError, match="Kaggle 下载失败") as caught:
        download_data(tmp_path / "raw", tmp_path / "report.json")
    assert "secret-token" not in str(caught.value)
