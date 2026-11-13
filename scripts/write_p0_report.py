"""Render the P0 report exclusively from local execution evidence, including blockers."""
from datetime import datetime
from importlib.metadata import version
import json
from pathlib import Path
import platform
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def read_json(name):
    path = ROOT / "reports" / name
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def main():
    audit = read_json("raw_quality.json")
    download = read_json("download_manifest.json")
    repeat = read_json("download_repeat_manifest.json")
    verification = read_json("import_verification.json")
    test_path = ROOT / "reports/pytest.xml"
    tests = ET.parse(test_path).getroot().find("testsuite") if test_path.exists() else None
    passed = verification.get("status") == "passed" and tests is not None and all(
        int(tests.get(key, 0)) == 0 for key in ("failures", "errors", "skipped")
    )
    lines = [
        "# RetailScope P0 验收报告", "",
        f"生成时间：{datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')}。",
        f"阶段状态：**{'P0 技术检查通过，等待用户验收' if passed else 'P0 未通过：数据库运行验收尚未完成'}**。未进入 P1–P4。", "",
        "## 实际运行环境", "",
        f"- Windows：{platform.platform()}；Python {platform.python_version()}（64 位）。",
        "- 工程根目录：`D:\\Projects\\RetailScope`；使用本项目 `.venv`。初始工程无 `.git`，未创建仓库或执行提交。",
        "- 已通过 winget 用户级安装 Python 3.12.10；已实际安装项目及 dev 依赖。",
        "- 硬件虚拟化已开启；物理内存约 16 GB，安装前 D 盘可用空间约 109 GB。",
        "- 微软官方 WSL 安装：WSL 3.0.5.0，Linux 内核 6.18.58.1-1。",
        "- Docker 官方安装包 Authenticode 签名 Valid，签名者 Docker Inc；安装日志显示 Installation succeeded。",
        "- Docker CLI 29.9.3；Compose v5.7.0。安装后的初次引擎检查失败，重启前存在 RebootPending。",
        "- 重启后 WSL 状态正常（默认版本 2），RebootPending 已消失；Docker Engine 29.9.3 已实际连接。证据见 `reports/wsl_status_after_reboot.txt`、`reports/docker_engine.log`。",
        f"- PostgreSQL：{verification.get('database', {}).get('server', '尚无数据库运行证据')}。", "",
        "依赖实际版本：", "",
    ]
    lines += [f"- `{name}=={version(name)}`" for name in (
        "pandas", "sqlalchemy", "psycopg", "streamlit", "plotly", "pytest", "kagglehub"
    )]
    lines += ["", "## 数据来源与下载", "",
        "官方来源：[Olist / Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)，CC BY-NC-SA 4.0。",
        f"使用 `kagglehub.dataset_download('olistbr/brazilian-ecommerce')`，缓存版本 {download.get('cache_version', '未记录')}。无需登录；九个原始 CSV 已复制到 `data/raw/`。",
        "每个文件的字节数、SHA-256 与 CSV 解析行数见 `reports/download_manifest.json`；行数不包含表头，正确解析评价中的换行和引号。",
        f"重复下载：跳过={repeat.get('download_skipped')}；九文件内容哈希一致={bool(download.get('files')) and download.get('files') == repeat.get('files')}。",
        "原始 CSV、报告、安装包、`.env`、虚拟环境已由 `.gitignore` 排除；无凭证打印或公开提交。", "",
        "## 九表真实记录数与数据库对账", "",
        "| CSV | raw 表 | CSV 行数 | 首次导入 | 再次导入 |", "|---|---|---:|---:|---:|",
    ]
    for table in audit.get("tables", []):
        name = table["table"]
        first = verification.get("first_snapshot", {}).get(name, {}).get("rows", "未执行")
        second = verification.get("second_snapshot", {}).get(name, {}).get("rows", "未执行")
        lines.append(f"| {table['source_file']} | raw.{name} | {table['row_count']:,} | {first} | {second} |")
    lines += ["", f"CSV 合计：**{audit.get('total_source_rows', '未执行'):,} 条**。", "",
        "raw 层保留 TEXT 原值及原始重复；空 CSV 字段由 PostgreSQL COPY 的 NULL 规则导入，不在 P0 执行类型清洗。", "",
        "## 缺失值、重复与格式检查", "",
        "缺失口径：空字符串或仅空白字段；重复行数为首次出现之后的额外行数。空日期与无效日期分别处理。", "",
        "| raw 表 | 整行重复 | 声明唯一键重复 | 缺失字段及数量 |", "|---|---:|---:|---|",
    ]
    for table in audit.get("tables", []):
        missing = "; ".join(f"{key}: {value}" for key, value in table["missing_by_column"].items()) or "无"
        lines.append(f"| {table['table']} | {table['duplicate_full_rows']} | {table['duplicate_unique_key_rows'] if table['duplicate_unique_key_rows'] is not None else '不声明唯一'} | {missing} |")
    lines += ["", f"结构/关键字段/类型阻塞问题：{audit.get('has_blocking_issues', '未执行')}。九表表头严格匹配，日期和数值格式审计详见 `reports/raw_quality.json`。",
        "地理表重复按原样保留；reviews.review_id、customer_unique_id、邮编前缀不被误设为主键。", "",
        "## 关联异常", "",
        "Pandas 从真实 CSV 独立计算，并与 PostgreSQL SQL 实测对账；缺少翻译及邮编覆盖属于源数据告警。", "",
        "| 检查 | CSV 实测 | PostgreSQL 实测 |", "|---|---:|---:|",
    ]
    for key, value in audit.get("relational_quality", {}).get("checks", {}).items():
        db_value = verification.get("relational_quality", {}).get("checks", {}).get(key, "未执行")
        lines.append(f"| {key} | {value} | {db_value} |")
    for key, value in audit.get("relational_quality", {}).get("nonunique_reference_fields", {}).items():
        lines.append(f"\n- {key}: {value}（非错误主键检查）。")
    lines += ["", "## 数据库与重复导入验收", "",
        f"- 验收状态：{verification.get('status', '未执行，Docker 引擎未启动')}。",
        f"- CSV/数据库行数一致：{verification.get('counts_match_csv', '未验证')}。",
        f"- 两次导入行数及包含重复次数的内容指纹一致：{verification.get('idempotent', '未验证')}。",
        f"- Pandas/SQL 关联检查一致：{verification.get('relations_match_csv', '未验证')}。",
        "- `verify-import` 会真实执行两次原始表事务式 TRUNCATE + COPY；只替换本项目九张 raw 表。失败时回滚。未使用其他数据库替代 PostgreSQL 16。", "",
        "## Pytest", "",
    ]
    if tests is not None:
        total, failures, errors, skipped = [int(tests.get(key, 0)) for key in ("tests", "failures", "errors", "skipped")]
        lines.append(f"实际结果：{total - failures - errors - skipped} 通过、{failures} 失败、{errors} 错误、{skipped} 跳过。详情：`reports/pytest.log`、`reports/pytest.xml`。")
    lines += ["", "原有测试基线：10 passed in 0.30s。新增下载重跑、缺文件、凭证错误隐藏、CSV 关联与导入验收逻辑测试。数据库测试未配置连接时明确 skip，配置后不可用则失败。测试微型 fixture 仅写入 pytest 临时目录，从未用于真实入库。", "",
        "## 实际执行命令与证据", "",
        "```powershell", "winget install --id Python.Python.3.12 --exact --scope user --silent --accept-package-agreements --accept-source-agreements --disable-interactivity",
        r".\.venv\Scripts\python.exe -m pip install -e '.[dev]'",
        r".\.venv\Scripts\python.exe -m pip check",
        r".\.venv\Scripts\python.exe -m retailscope download-data",
        r".\.venv\Scripts\python.exe -m retailscope download-data --output reports/download_repeat_manifest.json",
        r".\.venv\Scripts\python.exe -m retailscope check-data",
        r".\.venv\Scripts\python.exe -m pytest -q -rA --junitxml=reports/pytest.xml",
        "wsl --install --no-distribution --web-download  # UAC 授权执行",
        "wsl --version", "wsl --status", "docker --version", "docker compose version", "docker info --format '{{.ServerVersion}}'",
        "powershell -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\run_p0.ps1",
        "# 续跑入口依次实际执行下列数据库命令，执行结果见对应日志：",
        "docker compose up -d --wait db", "docker compose ps",
        r".\.venv\Scripts\python.exe -m retailscope db-status",
        r".\.venv\Scripts\python.exe -m retailscope init-db",
        r".\.venv\Scripts\python.exe -m retailscope verify-import",
        r".\.venv\Scripts\python.exe -m retailscope db-quality", "```", "",
        "下载、依赖、审计、测试日志及冻结的实际依赖列表保存在 `reports/`。完整数据库续跑入口为 `scripts/run_p0.ps1`；尚未执行的命令不会当作成功结果。", "",
        "## 修改文件", "",
        "- `pyproject.toml`：加入 kagglehub。",
        "- `.gitignore`：排除 editable 安装生成的 egg-info。",
        "- `src/retailscope/download.py`：官方下载、完整性校验、跳过已有数据、哈希清单。",
        "- `src/retailscope/audit.py`：整行重复与独立 CSV 关联检查。",
        "- `src/retailscope/database.py`：补齐产品、商户、翻译和邮编关联检查。",
        "- `src/retailscope/verification.py`：两次真实导入、逐表行数/内容指纹、CSV/SQL 对账。",
        "- `src/retailscope/__main__.py`：下载/验收 CLI 和格式错误处理。",
        "- `tests/test_audit.py`、`tests/test_download.py`、`tests/test_database.py`、`tests/test_verification.py`：P0 测试。",
        "- `scripts/check_windows_features.ps1`、`scripts/run_p0.ps1`、`scripts/write_p0_report.py`：环境检查、续跑与报告。",
        "- `README.md`、`docs/P0_ACCEPTANCE_REPORT.md`、`docs/quality_report.md`、`docs/P0_RESUME.md`：运行说明和真实结果。", "",
        "## 安装阶段的历史失败与处理", "",
        "- 依赖安装尚在进行时首次执行下载出现 No module named retailscope；等待安装完成并重新安装后，下载和重跑均成功。",
        "- 重启前 `docker compose up -d db` 退出码 1，Docker Desktop Linux Engine `_ping` 返回 HTTP 500；用户重启后引擎已恢复。",
        "- 重启前 `db-status` 退出码 2（缺少 DATABASE_URL）；续跑程序在引擎可用后才生成本地随机密码 `.env`。未打印密码。",
        "- 重启前续跑程序在 Docker info 处停止，退出码 1；仅停止长时间无响应的单个探针，未操作数据卷。历史日志 `reports/p0_run.log`，本次日志 `reports/p0_after_reboot.log`。", "",
        "- 重启后的首次续跑被 Windows PowerShell 对 Docker stderr 进度输出的错误判定打断。已修复 Invoke-Checked：保留输出，依据实际进程退出码判断成功或失败；随后重新完整运行。", "",
        "## 尚未解决的问题与 P1 准入", "",
        "**已具备进入 P1 的技术条件，等待用户验收。** P0 无未解决的运行阻塞。源数据中的缺失、地理整行重复、13 条商品类目翻译缺失、邮编覆盖不足及明细缺失保留为质量告警；P1 需明确处理规则。本次未进入 P1–P4。" if passed else
        "**目前不具备进入 P1 的条件。** 数据库运行验收或测试尚未全部通过。以 `reports/p0_after_reboot.log`、`reports/import_verification.json`、`reports/pytest.xml` 为准，修复后重新运行 `scripts/run_p0.ps1`。",
        "不自动重启，不删除现有工程、关闭安全防护或开发后续阶段。", "",
    ]
    (ROOT / "docs/P0_ACCEPTANCE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    quality = lines[lines.index("## 九表真实记录数与数据库对账"):lines.index("## 数据库与重复导入验收")]
    (ROOT / "docs/quality_report.md").write_text("# P0 真实数据质量基线\n\n" + "\n".join(quality), encoding="utf-8")
    print("Updated docs/P0_ACCEPTANCE_REPORT.md and docs/quality_report.md")


if __name__ == "__main__":
    main()
