"""Download official Olist files; preserve existing source files and record hashes."""
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import shutil

from .audit import DataContractError, audit_all, missing_files, write_json_report
from .contracts import SOURCES

DATASET = "olistbr/brazilian-ecommerce"


def download_data(destination: Path, output: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    missing = missing_files(destination)
    cache = None
    if missing:
        import kagglehub

        try:
            cache = Path(kagglehub.dataset_download(DATASET))
        except Exception as exc:
            # Library errors can contain signed URLs or credentials; keep them off stdout.
            raise RuntimeError(
                f"Kaggle 下载失败 ({type(exc).__name__})。请检查网络、Kaggle 服务和认证；"
                "不要将令牌发送到聊天或提交到仓库。"
            ) from None
        unavailable = [name for name in missing if not (cache / name).is_file()]
        if unavailable:
            raise DataContractError("Kaggle 下载缺少文件：" + ", ".join(unavailable))
        audit_all(cache)  # Verify all headers before copying anything.
        for name in missing:
            with (cache / name).open("rb") as source, (destination / name).open("xb") as target:
                shutil.copyfileobj(source, target)
    audit = audit_all(destination)
    if audit["has_blocking_issues"]:
        raise DataContractError("下载后的 CSV 审计未通过，请运行 check-data 查看详情。")
    report = {
        "dataset": DATASET,
        "source_url": "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "download_skipped": not missing,
        "downloaded_files": missing,
        "cache_version": cache.name if cache else None,
        "files": [],
    }
    for spec, quality in zip(SOURCES, audit["tables"], strict=True):
        path = destination / spec.file_name
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        report["files"].append({
            "file": spec.file_name, "bytes": path.stat().st_size,
            "sha256": digest, "rows": quality["row_count"],
        })
    write_json_report(report, output)
    return report
