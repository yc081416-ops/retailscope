# RetailScope P0 验收报告

生成时间：2026-11-13T11:19:24+08:00。
阶段状态：**P0 技术检查通过，等待用户验收**。未进入 P1–P4。

## 实际运行环境

- Windows：Windows-11-10.0.26200-SP0；Python 3.12.10（64 位）。
- 工程根目录：`D:\Projects\RetailScope`；使用本项目 `.venv`。初始工程无 `.git`，未创建仓库或执行提交。
- 已通过 winget 用户级安装 Python 3.12.10；已实际安装项目及 dev 依赖。
- 硬件虚拟化已开启；物理内存约 16 GB，安装前 D 盘可用空间约 109 GB。
- 微软官方 WSL 安装：WSL 3.0.5.0，Linux 内核 6.18.58.1-1。
- Docker 官方安装包 Authenticode 签名 Valid，签名者 Docker Inc；安装日志显示 Installation succeeded。
- Docker CLI 29.9.3；Compose v5.7.0。安装后的初次引擎检查失败，重启前存在 RebootPending。
- 重启后 WSL 状态正常（默认版本 2），RebootPending 已消失；Docker Engine 29.9.3 已实际连接。证据见 `reports/wsl_status_after_reboot.txt`、`reports/docker_engine.log`。
- PostgreSQL：PostgreSQL 16.16 on x86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit。

依赖实际版本：

- `pandas==2.3.3`
- `sqlalchemy==2.1.8`
- `psycopg==3.3.9`
- `streamlit==1.67.0`
- `plotly==6.9.0`
- `pytest==9.2.0`
- `kagglehub==1.0.3`

## 数据来源与下载

官方来源：[Olist / Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)，CC BY-NC-SA 4.0。
使用 `kagglehub.dataset_download('olistbr/brazilian-ecommerce')`，缓存版本 2。无需登录；九个原始 CSV 已复制到 `data/raw/`。
每个文件的字节数、SHA-256 与 CSV 解析行数见 `reports/download_manifest.json`；行数不包含表头，正确解析评价中的换行和引号。
重复下载：跳过=True；九文件内容哈希一致=True。
原始 CSV、报告、安装包、`.env`、虚拟环境已由 `.gitignore` 排除；无凭证打印或公开提交。

## 九表真实记录数与数据库对账

| CSV | raw 表 | CSV 行数 | 首次导入 | 再次导入 |
|---|---|---:|---:|---:|
| olist_customers_dataset.csv | raw.customers | 99,441 | 99441 | 99441 |
| olist_geolocation_dataset.csv | raw.geolocation | 1,000,163 | 1000163 | 1000163 |
| olist_order_items_dataset.csv | raw.order_items | 112,650 | 112650 | 112650 |
| olist_order_payments_dataset.csv | raw.order_payments | 103,886 | 103886 | 103886 |
| olist_order_reviews_dataset.csv | raw.order_reviews | 99,224 | 99224 | 99224 |
| olist_orders_dataset.csv | raw.orders | 99,441 | 99441 | 99441 |
| olist_products_dataset.csv | raw.products | 32,951 | 32951 | 32951 |
| olist_sellers_dataset.csv | raw.sellers | 3,095 | 3095 | 3095 |
| product_category_name_translation.csv | raw.category_translation | 71 | 71 | 71 |

CSV 合计：**1,550,922 条**。

raw 层保留 TEXT 原值及原始重复；空 CSV 字段由 PostgreSQL COPY 的 NULL 规则导入，不在 P0 执行类型清洗。

## 缺失值、重复与格式检查

缺失口径：空字符串或仅空白字段；重复行数为首次出现之后的额外行数。空日期与无效日期分别处理。

| raw 表 | 整行重复 | 声明唯一键重复 | 缺失字段及数量 |
|---|---:|---:|---|
| customers | 0 | 0 | 无 |
| geolocation | 261831 | 不声明唯一 | 无 |
| order_items | 0 | 0 | 无 |
| order_payments | 0 | 0 | 无 |
| order_reviews | 0 | 不声明唯一 | review_comment_message: 58274; review_comment_title: 87658 |
| orders | 0 | 0 | order_approved_at: 160; order_delivered_carrier_date: 1783; order_delivered_customer_date: 2965 |
| products | 0 | 0 | product_category_name: 610; product_description_lenght: 610; product_height_cm: 2; product_length_cm: 2; product_name_lenght: 610; product_photos_qty: 610; product_weight_g: 2; product_width_cm: 2 |
| sellers | 0 | 0 | 无 |
| category_translation | 0 | 0 | 无 |

结构/关键字段/类型阻塞问题：False。九表表头严格匹配，日期和数值格式审计详见 `reports/raw_quality.json`。
地理表重复按原样保留；reviews.review_id、customer_unique_id、邮编前缀不被误设为主键。

## 关联异常

Pandas 从真实 CSV 独立计算，并与 PostgreSQL SQL 实测对账；缺少翻译及邮编覆盖属于源数据告警。

| 检查 | CSV 实测 | PostgreSQL 实测 |
|---|---:|---:|
| orders_missing_customers | 0 | 0 |
| items_missing_orders | 0 | 0 |
| payments_missing_orders | 0 | 0 |
| reviews_missing_orders | 0 | 0 |
| items_missing_products | 0 | 0 |
| items_missing_sellers | 0 | 0 |
| products_missing_translation | 13 | 13 |
| customers_missing_geolocation | 278 | 278 |
| sellers_missing_geolocation | 7 | 7 |
| orders_without_items | 775 | 775 |
| orders_without_payments | 1 | 1 |
| orders_without_reviews | 768 | 768 |
| multiple_payment_orders | 2961 | 2961 |
| multiple_review_orders | 547 | 547 |

- review_id_duplicate_rows: 814（非错误主键检查）。

- geolocation_zip_duplicate_rows: 981148（非错误主键检查）。

- customer_unique_id_duplicate_rows: 3345（非错误主键检查）。

## 数据库与重复导入验收

- 验收状态：passed。
- CSV/数据库行数一致：True。
- 两次导入行数及包含重复次数的内容指纹一致：True。
- Pandas/SQL 关联检查一致：True。
- `verify-import` 会真实执行两次原始表事务式 TRUNCATE + COPY；只替换本项目九张 raw 表。失败时回滚。未使用其他数据库替代 PostgreSQL 16。

## Pytest

实际结果：18 通过、0 失败、0 错误、0 跳过。详情：`reports/pytest.log`、`reports/pytest.xml`。

原有测试基线：10 passed in 0.30s。新增下载重跑、缺文件、凭证错误隐藏、CSV 关联与导入验收逻辑测试。数据库测试未配置连接时明确 skip，配置后不可用则失败。测试微型 fixture 仅写入 pytest 临时目录，从未用于真实入库。

## 实际执行命令与证据

```powershell
winget install --id Python.Python.3.12 --exact --scope user --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m retailscope download-data
.\.venv\Scripts\python.exe -m retailscope download-data --output reports/download_repeat_manifest.json
.\.venv\Scripts\python.exe -m retailscope check-data
.\.venv\Scripts\python.exe -m pytest -q -rA --junitxml=reports/pytest.xml
wsl --install --no-distribution --web-download  # UAC 授权执行
wsl --version
wsl --status
docker --version
docker compose version
docker info --format '{{.ServerVersion}}'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_p0.ps1
# 续跑入口依次实际执行下列数据库命令，执行结果见对应日志：
docker compose up -d --wait db
docker compose ps
.\.venv\Scripts\python.exe -m retailscope db-status
.\.venv\Scripts\python.exe -m retailscope init-db
.\.venv\Scripts\python.exe -m retailscope verify-import
.\.venv\Scripts\python.exe -m retailscope db-quality
```

下载、依赖、审计、测试日志及冻结的实际依赖列表保存在 `reports/`。完整数据库续跑入口为 `scripts/run_p0.ps1`；尚未执行的命令不会当作成功结果。

## 修改文件

- `pyproject.toml`：加入 kagglehub。
- `.gitignore`：排除 editable 安装生成的 egg-info。
- `src/retailscope/download.py`：官方下载、完整性校验、跳过已有数据、哈希清单。
- `src/retailscope/audit.py`：整行重复与独立 CSV 关联检查。
- `src/retailscope/database.py`：补齐产品、商户、翻译和邮编关联检查。
- `src/retailscope/verification.py`：两次真实导入、逐表行数/内容指纹、CSV/SQL 对账。
- `src/retailscope/__main__.py`：下载/验收 CLI 和格式错误处理。
- `tests/test_audit.py`、`tests/test_download.py`、`tests/test_database.py`、`tests/test_verification.py`：P0 测试。
- `scripts/check_windows_features.ps1`、`scripts/run_p0.ps1`、`scripts/write_p0_report.py`：环境检查、续跑与报告。
- `README.md`、`docs/P0_ACCEPTANCE_REPORT.md`、`docs/quality_report.md`、`docs/P0_RESUME.md`：运行说明和真实结果。

## 安装阶段的历史失败与处理

- 依赖安装尚在进行时首次执行下载出现 No module named retailscope；等待安装完成并重新安装后，下载和重跑均成功。
- 重启前 `docker compose up -d db` 退出码 1，Docker Desktop Linux Engine `_ping` 返回 HTTP 500；用户重启后引擎已恢复。
- 重启前 `db-status` 退出码 2（缺少 DATABASE_URL）；续跑程序在引擎可用后才生成本地随机密码 `.env`。未打印密码。
- 重启前续跑程序在 Docker info 处停止，退出码 1；仅停止长时间无响应的单个探针，未操作数据卷。历史日志 `reports/p0_run.log`，本次日志 `reports/p0_after_reboot.log`。

- 重启后的首次续跑被 Windows PowerShell 对 Docker stderr 进度输出的错误判定打断。已修复 Invoke-Checked：保留输出，依据实际进程退出码判断成功或失败；随后重新完整运行。

## 尚未解决的问题与 P1 准入

**已具备进入 P1 的技术条件，等待用户验收。** P0 无未解决的运行阻塞。源数据中的缺失、地理整行重复、13 条商品类目翻译缺失、邮编覆盖不足及明细缺失保留为质量告警；P1 需明确处理规则。本次未进入 P1–P4。
不自动重启，不删除现有工程、关闭安全防护或开发后续阶段。
