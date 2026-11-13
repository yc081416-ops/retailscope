# RetailScope P1 验收报告

生成时间：2026-11-13T11:43:37+08:00。**P1 技术验收通过，等待用户验收。**

由真实执行证据生成；金额单位 BRL；比率为观察期描述，不作因果推断。

## 范围与 P0 核查

数据库：PostgreSQL 16.16 on x86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit；Python 3.12.10，延用 P0 本地虚拟环境和免费开源依赖。
raw 与 P0 验收指纹一致=True；P0 报告、质量报告、原始 CSV、原有测试及根 reports 文件哈希不变=True。完整哈希见 `reports/p1/run.json`。
九张 raw 表仍合计1,550,922行。未运行 P0 重新导入或报告生成脚本，不覆盖 P0 成果。未开发 P2 前端或 P3/P4。

## 实际数据层行数

| mart对象 | 实际行数 | 第二次构建哈希 |
|---|---|---|
| dim_geolocation | 19015 | 01e7643b19c9daa7… |
| dim_user | 96096 | 9818802c7800f9f5… |
| dim_customer | 99441 | dd23ff94143ecb37… |
| dim_product | 32951 | 99617ceae37ecb5a… |
| dim_seller | 3095 | 27236e4227a2bcda… |
| dim_date | 774 | 08a860944d430f7b… |
| analysis_context | 1 | 6839e2496ce27534… |
| order_wide | 99441 | 0898ff7572b776af… |
| order_financials | 98666 | f7bd3ee4a2348ebb… |
| order_payment_agg | 99440 | 1d0dc329169ffd38… |
| order_review_agg | 98673 | 891ab1a039b44017… |
| order_item_fact | 112650 | db918c1263980907… |
| kpi_overview | 1 | 90ad159d0b54a061… |
| order_status_distribution | 8 | 667a46d0d7b13d0a… |
| monthly_kpis | 24 | f2955723ff88e5f6… |
| category_monthly | 1273 | 9c1d471a752d7d97… |
| category_ranking | 74 | 953a6b53f0ac4180… |
| region_sales | 27 | 0d82357e8dd8cb73… |
| review_distribution | 5 | 7e4bead96eaca27f… |
| quality_checks | 1 | 0846bf70eeb9c040… |
| customer_rfm | 93358 | 4154a1406f4e91f5… |
| rfm_segments | 6 | c3edb7d3155efc45… |
| repurchase_distribution | 9 | a49ad54ecc6f2983… |
| repurchase_summary | 1 | d0f04ad9aa72c9cc… |
| customer_cohort | 93358 | 221bc8728c5ec73d… |
| cohort_sizes | 23 | 4cb29f0d47753564… |
| cohort_retention | 552 | 5dd4e75f525fe814… |

完整SHA-256见两份 `mart_snapshot_*.json`，27个对象全部行数及内容一致。core包含8个带类型源视图；第9份类目翻译直接读取raw.category_translation，无额外复制原始数据。

## 真实经营指标

有效购买期：2016-09-15 至 2018-08-29（含），以购买时间归属。全状态数据最后购买日为 2018-10-17，不据此延长完整有效购买观察窗。

| 指标 | 真实SQL结果 |
|---|---|
| 有效订单数 | 96478 |
| 唯一购买用户数 | 93358 |
| 商品成交额 | 13,221,498.11 |
| 运费 | 2,198,275.64 |
| 支付金额（独立口径） | 15,422,461.77 |
| 平均订单商品金额 | 137.04 |
| 复购用户数 | 2801 |
| 观察期复购率 | 3.0003% |
| 平均配送天数 | 12.56 |
| 配送样本数 | 96470 |
| 逾期率（日期口径） | 6.7731% |
| 逾期样本数 | 96470 |
| 订单等权评价均分 | 4.16 |
| 有评价订单数 | 95832 |

金额精确到分；客单价/配送天数/评价均分在文档展示四舍五入，JSON保留数据库原精度。商品金额不是财务确认收入或利润；支付金额另列。

## RFM 与 Cohort

RFM基准日 **2018-08-30**；用户数 93358。离散分位点：R=[93, 178, 269, 383]；F=[1, 1, 1, 1]；M=['39.90', '69.90', '109.90', '179.90'] BRL。
F评分实际分布：[{'f_score': 1, 'users': 90557}, {'f_score': 5, 'users': 2801}]。大量相同频次导致评分档可能为空，未按用户ID强拆相同值。
分层规则见METRICS.md；本数据“数据待核对”层为0人，所以分层视图仅输出6个非空层。

| 分层 | 用户数 | 用户占比 | 商品金额BRL | 金额贡献 |
|---|---|---|---|---|
| 其他用户 | 18723 | 20.0551% | 2,509,606.57 | 18.9813% |
| 核心价值 | 941 | 1.0079% | 307,543.11 | 2.3261% |
| 沉睡用户 | 22782 | 24.4028% | 1,280,039.44 | 9.6815% |
| 活跃复购 | 273 | 0.2924% | 20,275.05 | 0.1533% |
| 近期用户 | 36345 | 38.9308% | 5,101,677.71 | 38.5862% |
| 高价值待唤回 | 14294 | 15.3110% | 4,002,356.23 | 30.2716% |

Cohort完整目标月区间：[2016-10-01, 2018-08-01)。末尾2018-08及更远月份均为NULL，首个不完整目标月2016-09同样不可算。首cohort标记左截断。
23个cohort，552个cohort/月龄单元，其中可观察254个，不可观察298个。
长表：`reports/p1/cohort_retention.csv`；矩阵：`reports/p1/cohort_matrix.csv`，NA表示不可观察，0仅表示已完整观察且当月没有回购用户。新增用户及整体复购分布分别见cohort_sizes和repurchase_distribution。

## 关联膨胀与独立对账

订单商品/支付/评价先分别按订单聚合，三个订单级表主键均为order_id；order_wide订单主键与order_item_fact复合主键、维表外键由数据库执行约束。
地理表去重后每邮编一行；缺覆盖左连接保留订单，不对百万地理原始行做交易汇总。

| 独立Pandas校验 | 比较行数 | 结果 |
|---|---|---|
| all_order_rows_and_amounts | 99441 | 通过 |
| multi_payment_no_amount_inflation | 2961 | 通过 |
| multi_review_no_order_inflation | 547 | 通过 |
| order_financial_preaggregation | 98666 | 通过 |
| payment_preaggregation | 99440 | 通过 |
| review_preaggregation | 98673 | 通过 |
| all_item_rows_and_amounts | 112650 | 通过 |
| overview_money_users_delivery_review | 1 | 通过 |
| all_status_distribution | 8 | 通过 |
| monthly_including_empty_and_partial | 24 | 通过 |
| category_ranking | 74 | 通过 |
| category_monthly | 1273 | 通过 |
| region_sales | 27 | 通过 |
| review_distribution_one_per_order | 5 | 通过 |
| every_user_rfm_and_tied_scores | 93358 | 通过 |
| rfm_segments | 6 | 通过 |
| repurchase_frequency_distribution | 9 | 通过 |
| repurchase_unique_customers | 1 | 通过 |
| every_cohort_cell_including_unobserved_nulls | 552 | 通过 |
| cohort_new_users | 23 | 通过 |
| deduplicated_geolocation | 19015 | 通过 |
| geolocation_join_no_inflation | 99441 | 通过 |

Pandas直接读取真实CSV，金额先转换为整数分后逐行精确比较；均值/比率/坐标容差1e-10。核验覆盖每订单、每商品行、每用户RFM、每cohort单元及全部所需汇总。

## 缺失与异常处理

| 质量项 | 真实SQL计数 |
|---|---|
| all_orders_without_items | 775 |
| eligible_without_items | 0 |
| eligible_without_payment | 1 |
| eligible_missing_delivery | 8 |
| eligible_delivery_anomalies | 0 |
| eligible_missing_user | 0 |
| missing_purchase_timestamp | 0 |

无商品订单保留状态及NULL金额；有效订单实测无缺商品。1笔有效订单缺支付，保留商品金额，支付额不补零。8笔有效订单缺实际送达时间，交易保留，配送/逾期分母排除。取消等非delivered状态仅进入全状态分布。
P0的类目翻译和邮编缺失未被删除：商品类目缺失归入__unknown__，英文缺失保留葡语类目；地理缺失保留邮编并置地理外键NULL。非法评分/负金额等将使构建失败回滚，不静默清洗。

## 重跑与测试证据

完整流程两次构建及初轮测试用时 131.194 秒（本机实测，不是性能承诺）。重跑内容一致=True。
最新Pytest：**44通过，0失败，0错误，0跳过**，含P0原有18项及P1新增26项。最终日志无warnings。

```powershell
.\.venv\Scripts\python.exe scripts/probe_p1.py
.\.venv\Scripts\python.exe scripts/run_p1.py
.\.venv\Scripts\python.exe -m pytest -q -rA --junitxml=reports/p1/pytest.xml
.\.venv\Scripts\python.exe scripts/write_p1_report.py
```

证据：`reports/p1/run.log`、`run.json`、`mart_snapshot_1.json`、`mart_snapshot_2.json`、`pandas_reconciliation.json`、`pytest.log`、`pytest.xml`、各SQL指标JSON/CSV。依赖兼容警告修复前日志保留为pytest_initial.log。

## 修改文件与复现

- 更新：`docs/METRICS.md`、`README.md`。
- 新增SQL：`sql/10_core.sql`、`sql/20_mart.sql`、`sql/30_customer.sql`。
- 新增模块：`src/retailscope/warehouse.py`、`src/retailscope/p1_validation.py`。
- 新增入口：`scripts/probe_p1.py`、`scripts/build_warehouse.py`、`scripts/run_p1.py`、`scripts/write_p1_report.py`。
- 新增测试：`tests/test_p1.py`。
- 新增文档：本报告、`P1_DATA_MODEL.md`、`P1_ANALYSIS_FINDINGS.md`。
- 运行结果全部位于被gitignore排除的reports/p1；未提交CSV、凭证或原始用户级数据。

日常仅构建：python scripts/build_warehouse.py。完整验收：python scripts/run_p1.py，然后python scripts/write_p1_report.py；SQL脚本需在同一事务中按10→20→30执行。失败回滚P1数据，raw不被修改。

## 局限与待验收

P1无未解决运行阻塞。观察期首尾不完整，用户获客前历史不可见，各用户复购观察时长不一；部分完整日历月份样本很少，不能推断市场总量。源数据没有成本/完整退款/曝光，不能计算利润、ROI或转化率。
RFM是规则分层、Cohort是购买活跃留存，都未证明营销干预效果。无效新源格式会失败，P0数据契约需先修复；未实现增量CDC。
**已完成P1并停止开发，等待用户验收；不自动进入P2–P4。**
