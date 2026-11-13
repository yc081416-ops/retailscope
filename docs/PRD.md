# RetailScope｜产品需求与技术设计 PRD v1.0

**目标与边界**

应用统计研究生求职作品。用户能上传/读取已导入的 Olist 公开数据，并完成从数据入库、质量校验、SQL 指标层、业务可视化到结论报告的完整链路。所有页面显示真实执行结果和当前筛选条件；不追求没有证据的经营增长、利润、GMV 预测等表述。

**技术与运行条件**
- Python 3.12、PostgreSQL 16（Docker Compose）、Pandas、SQLAlchemy/psycopg、Streamlit、Plotly、pytest。
- 本地命令一键起数据库、初始化 schema、ETL、建 mart、启动看板；Windows PowerShell 使用说明。
- `.env.example` 提供示例数据库连接；`.env`、原始数据、密码、缓存、导出分析中间文件须适当忽略；不得提交真实秘钥。
- 无 LLM、无登录系统、无第三方招聘爬虫、无虚构实时数据、无复杂微服务。数据集为历史数据，页面标注 2016–2018。
- GitHub 公开代码和聚合结果时尊重数据许可，不上传完整原始数据。

## 原始数据（9 张 CSV）

- olist_orders_dataset.csv（订单主表）
- olist_customers_dataset.csv（客户订单 ID、跨订单唯一用户 ID、州、城市）
- olist_order_items_dataset.csv（订单商品明细、价格、运费）
- olist_order_payments_dataset.csv（支付方式、分期和支付金额；可能一单多支付）
- olist_order_reviews_dataset.csv（评价；可能一单多评价）
- olist_products_dataset.csv（产品属性、类目）
- olist_sellers_dataset.csv（商户）
- olist_geolocation_dataset.csv（邮编前缀、坐标；一前缀多行，不可直接 JOIN 明细）
- product_category_name_translation.csv（类目葡语-英语翻译）

入口：https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

## 数据模型（必须实现）

- `raw`：9 张原始暂存表，保留原始字段，导入过程可追踪，支持重跑，不能反复追加相同批次产生重复。
- `core`：类型规范化后基础表；原始数值字符串正确处理 NULL 与无效日期；订单、客户、商品、商户关系可核验；订单明细粒度 `(order_id, order_item_id)`。
- `mart.order_item_fact`：一行一件订单商品明细，标明价格与运费。
- `mart.order_financials`：按 `order_id` 聚合商品金额、运费、支付金额（分别表示，不混同）。
- `mart.order_review_agg`：一单一行评价统计；多条评价明确采用均值或最新评价并写入方法文档。
- `mart.order_wide`：严格一行一个 `order_id`，关联订单、客户、订单级金额、评价、配送；严禁直接 JOIN 多个一对多明细表。
- `mart.monthly_kpis`、`mart.category_monthly`、`mart.customer_rfm`、`mart.cohort_retention`：结果层，也可用参数化 SQL 查询生成，但必须保留可审查 SQL。
- 经纬度用于地图时，必须先按 zip_code_prefix 聚合至唯一前缀，并记录聚合规则。第一版地区分析可仅基于州代码，地图非刚需。

## 业务模块（6 页）

1. **经营总览**：时间与州筛选；商品成交额（BRL）、订单量、下单客户数、平均订单商品金额、月趋势、州分布、客单价；完成订单和全部订单清楚分开。
2. **用户分析**：基于 `customer_unique_id` 的复购率、RFM（R/F/M）、分群分布、同期群月留存热力图；统计完整观察窗口，未观察区域显示空缺而不是 0。
3. **商品分析**：类目销售额排行、订单量、订单商品明细均价、销量/贡献、商户分布；对比时分母和口径明确。
4. **履约评价**：实际配送天数、超出承诺送达日比例、评价得分分布、按州/类目观察差异；无实际交付日期的订单不得参与交付天数统计。
5. **经营诊断**：基于可追溯阈值/规则的异常发现（例如：某月环比下降、某类目逾期率升高），显示证据、样本数、计算公式和注意事项；不声称因果关系。
6. **数据质量**：导入表行数、字段缺失率、唯一键校验、外键匹配率、金额/订单数校验、ETL 执行信息、质量告警。

## 必须具备的分析交付
- `docs/analysis_report.md`：数据集与问题定义、清洗流程、五个以上真正基于运行结果的发现、业务建议及局限性；不得预填结果。
- `docs/data_dictionary.md`：字段/单位/数据口径；`docs/quality_report.md`：真实运行检查结果。
- `README.md`：问题背景、截图（真实）、架构、目录、环境准备、数据下载、运行命令、测试、已知局限性、来源及许可。
- `tests/`：SQL 口径与 Python 复核；项目可以本地离线启动且无付费服务依赖。

## 非功能要求
- 首屏以聚合 mart 查询为主，普通开发机下交互不应每次重新全量 JOIN 百万行原始数据；Streamlit 做合理缓存和索引。
- 数值和时间单位清楚，BRL 标记；时间筛选同步所有图与 KPI；无数据时友好提示而非报错。
- 任意图表需有业务标题、单位、口径提示、可下载筛选结果表；配色清晰，文字对比达标。
- 报告和图表区分事实、相关性、推断；不能把只有样本期历史数据称为“当前销售额”。

## 建议仓库结构

```
retailscope/
├─ app/Home.py
├─ app/pages/{1_经营总览.py,2_用户分析.py,3_商品分析.py,4_履约评价.py,5_经营诊断.py,6_数据质量.py}
├─ src/etl/{load_raw.py,transform.py,run.py}
├─ src/analytics/{queries.py,metrics.py,diagnostics.py}
├─ src/db/{connection.py,init_db.py}
├─ sql/{00_schemas.sql,10_core.sql,20_marts.sql,30_kpis.sql,40_customer.sql,50_delivery.sql,60_quality.sql}
├─ tests/{test_data_grain.py,test_metrics.py,test_app_smoke.py,test_etl_idempotency.py}
├─ data/raw/                  # gitignored
├─ docs/{PRD.md,METRICS.md,ACCEPTANCE.md,data_dictionary.md,analysis_report.md,quality_report.md}
├─ scripts/
├─ docker-compose.yml
├─ requirements.txt
├─ .env.example
├─ .gitignore
└─ README.md
```

文件名和结构可经 Codex 优化，但不能省略核心分层及测试。
