# P1 数据模型与字段字典

本文件由 PostgreSQL 实际目录生成，来源为 `sql/10_core.sql`、`sql/20_mart.sql`、`sql/30_customer.sql`。

raw 保持 P0 原样；core 是带类型转换的只读视图；mart 以有主键/外键的物理维表和事实表为基础，聚合指标采用 SQL 视图。构建在单事务中刷新已知 P1 表，不删除 schema 或源文件。

用户维表粒度是 customer_unique_id；客户桥表粒度是 customer_id，订单地区由客户桥表取州。订单事实一订单一行，商品事实主键为(order_id,item_id)。支付、评价、商品金额均先分别按订单聚合，再连接订单；聚合表到订单事实的外键延迟到事务结束检查。

地理表先整行去重、排除非法坐标参与中位数、按五位邮编一行。未匹配邮编只保留源邮编，geo_zip为NULL；左连接不删订单。

分析视图逻辑键：monthly_kpis(月份)、category_monthly(月份,类目)、category_ranking(类目)、region_sales(州)、customer_rfm(唯一用户)、customer_cohort(唯一用户)、cohort_sizes(cohort月)、cohort_retention(cohort月,月龄)。视图本身不持有数据库主键，基础表约束保证粒度。

索引：order_wide购买日、唯一用户；order_item_fact商品及商户；各维表及事实表主键索引自动建立。

## core.customers（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| customer_id | text | 视图推导/可空 | 单次订单对应的客户标识，不用于跨单用户识别 |
| customer_unique_id | text | 视图推导/可空 | 跨订单唯一用户标识；用户分析主键 |
| zip_code | text | 视图推导/可空 | 规范化五位邮编前缀；文本保留前导0 |
| city | text | 视图推导/可空 | 源城市文本 |
| state | text | 视图推导/可空 | 源州代码 |


## core.geolocation（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| zip_code | text | 视图推导/可空 | 规范化五位邮编前缀；文本保留前导0 |
| lat | double precision | 视图推导/可空 | 源纬度，度 |
| lng | double precision | 视图推导/可空 | 源经度，度 |
| city | text | 视图推导/可空 | 源城市文本 |
| state | text | 视图推导/可空 | 源州代码 |


## core.order_items（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| order_id | text | 视图推导/可空 | 订单标识；订单级表主键，商品表复合主键的第一项 |
| item_id | integer | 视图推导/可空 | 订单内商品序号，与order_id组成主键 |
| product_id | text | 视图推导/可空 | 商品标识 |
| seller_id | text | 视图推导/可空 | 商户标识 |
| shipping_limit_at | timestamp without time zone | 视图推导/可空 | 商品发货截止时间 |
| price | numeric(18,2) | 视图推导/可空 | 商品明细金额，BRL |
| freight | numeric(18,2) | 视图推导/可空 | 运费之和或商品行运费，BRL |


## core.orders（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| order_id | text | 视图推导/可空 | 订单标识；订单级表主键，商品表复合主键的第一项 |
| customer_id | text | 视图推导/可空 | 单次订单对应的客户标识，不用于跨单用户识别 |
| status | text | 视图推导/可空 | 源订单状态 |
| purchased_at | timestamp without time zone | 视图推导/可空 | 购买时间，无时区源时间 |
| approved_at | timestamp without time zone | 视图推导/可空 | 付款批准时间，可缺失 |
| carrier_at | timestamp without time zone | 视图推导/可空 | 交承运商时间，可缺失 |
| delivered_at | timestamp without time zone | 视图推导/可空 | 实际送达时间，可缺失 |
| estimated_at | timestamp without time zone | 视图推导/可空 | 预计送达时间，可缺失 |


## core.payments（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| order_id | text | 视图推导/可空 | 订单标识；订单级表主键，商品表复合主键的第一项 |
| sequential | integer | 视图推导/可空 | 订单内支付序号，与订单标识共同识别支付记录 |
| payment_type | text | 视图推导/可空 | 源支付方式 |
| installments | integer | 视图推导/可空 | 支付记录的分期数 |
| amount | numeric(18,2) | 视图推导/可空 | 源支付记录金额，BRL |


## core.products（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| product_id | text | 视图推导/可空 | 商品标识 |
| category | text | 视图推导/可空 | 葡语类目；mart中缺失为__unknown__ |
| name_length | integer | 视图推导/可空 | 源商品名称长度 |
| description_length | integer | 视图推导/可空 | 源商品描述长度 |
| photos_qty | integer | 视图推导/可空 | 商品照片数 |
| weight_g | numeric | 视图推导/可空 | 商品重量，克 |
| length_cm | numeric | 视图推导/可空 | 商品长度，厘米 |
| height_cm | numeric | 视图推导/可空 | 商品高度，厘米 |
| width_cm | numeric | 视图推导/可空 | 商品宽度，厘米 |


## core.reviews（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| review_id | text | 视图推导/可空 | 源评价标识，可能跨订单重复，不能用作唯一主键 |
| order_id | text | 视图推导/可空 | 订单标识；订单级表主键，商品表复合主键的第一项 |
| score | integer | 视图推导/可空 | 评价评分1–5 |
| title | text | 视图推导/可空 | 源评价标题，空文本转NULL |
| message | text | 视图推导/可空 | 源评价正文，空文本转NULL |
| created_at | timestamp without time zone | 视图推导/可空 | 评价创建时间 |
| answered_at | timestamp without time zone | 视图推导/可空 | 评价回答时间 |


## core.sellers（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| seller_id | text | 视图推导/可空 | 商户标识 |
| zip_code | text | 视图推导/可空 | 规范化五位邮编前缀；文本保留前导0 |
| city | text | 视图推导/可空 | 源城市文本 |
| state | text | 视图推导/可空 | 源州代码 |


## mart.analysis_context（物理表）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| singleton | boolean | 是 | 单行分析上下文标识，只允许TRUE |
| first_purchase | date | 是 | 最早有效购买日 |
| last_purchase | date | 是 | 最后有效购买日 |
| rfm_reference_date | date | 是 | RFM基准日，最后有效购买日次日 |
| first_complete_month | date | 是 | 首个可完整观察的目标月首日 |
| observation_end_exclusive | date | 是 | Cohort观察终点，最后有效购买所在月首日，边界不含 |
| all_status_last_purchase | date | 是 | 全状态原订单的最后购买日，不能作为完整delivered观察终点 |

- `analysis_context_pkey`：`PRIMARY KEY (singleton)`
- `analysis_context_singleton_check`：`CHECK (singleton)`

## mart.category_monthly（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| month_start | date | 视图推导/可空 | 购买月份的首日 |
| category | text | 视图推导/可空 | 葡语类目；mart中缺失为__unknown__ |
| orders | bigint | 视图推导/可空 | 该统计范围订单数；类目内去重，跨类目不可加总 |
| items | bigint | 视图推导/可空 | 商品明细行数，不是订单数 |
| merchandise | numeric | 视图推导/可空 | 商品price之和，BRL，不含运费，不是财务确认收入 |
| freight | numeric | 视图推导/可空 | 运费之和或商品行运费，BRL |


## mart.category_ranking（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| category | text | 视图推导/可空 | 葡语类目；mart中缺失为__unknown__ |
| orders | bigint | 视图推导/可空 | 该统计范围订单数；类目内去重，跨类目不可加总 |
| items | bigint | 视图推导/可空 | 商品明细行数，不是订单数 |
| merchandise | numeric | 视图推导/可空 | 商品price之和，BRL，不含运费，不是财务确认收入 |
| freight | numeric | 视图推导/可空 | 运费之和或商品行运费，BRL |
| contribution | numeric | 视图推导/可空 | 该分组商品成交额/同口径总成交额，0–1 |
| sales_rank | bigint | 视图推导/可空 | 商品成交额降序稠密排名 |


## mart.cohort_retention（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| cohort_month | date | 视图推导/可空 | 用户数据内首次有效购买月首日 |
| month_age | integer | 视图推导/可空 | 目标月距离cohort月的整月差，0起 |
| target_month | date | 视图推导/可空 | cohort月加月龄 |
| new_users | bigint | 视图推导/可空 | 该cohort观测首购用户数 |
| cohort_left_truncated | boolean | 视图推导/可空 | cohort属于首个不完整获客月份，分母可能左截断 |
| is_observed | boolean | 视图推导/可空 | 目标月完整位于观察窗中；FALSE时人数和留存均NULL |
| active_users | bigint | 视图推导/可空 | 该cohort目标月购买用户去重人数；已观察无回购为0 |
| retention | numeric | 视图推导/可空 | active_users/new_users，0–1；不可观察为NULL |


## mart.cohort_sizes（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| cohort_month | date | 视图推导/可空 | 用户数据内首次有效购买月首日 |
| new_users | bigint | 视图推导/可空 | 该cohort观测首购用户数 |


## mart.customer_cohort（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| customer_unique_id | text | 视图推导/可空 | 跨订单唯一用户标识；用户分析主键 |
| cohort_month | date | 视图推导/可空 | 用户数据内首次有效购买月首日 |


## mart.customer_rfm（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| customer_unique_id | text | 视图推导/可空 | 跨订单唯一用户标识；用户分析主键 |
| last_purchase_date | date | 视图推导/可空 | 用户最后一次有效购买日 |
| frequency | bigint | 视图推导/可空 | 用户有效订单总数 |
| monetary | numeric | 视图推导/可空 | 用户累计商品金额，BRL；任意订单缺商品则为NULL待核对 |
| rfm_reference_date | date | 视图推导/可空 | RFM基准日，最后有效购买日次日 |
| recency | integer | 视图推导/可空 | RFM基准日减最后有效购买日，天 |
| r_score | integer | 视图推导/可空 | Recency离散五分位反向评分1–5 |
| f_score | integer | 视图推导/可空 | Frequency离散五分位评分1–5；相同次数同分 |
| m_score | integer | 视图推导/可空 | Monetary离散五分位评分1–5；缺失为NULL |
| segment | text | 视图推导/可空 | 按METRICS.md顺序互斥分配的规则分层标签 |


## mart.dim_customer（物理表）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| customer_id | text | 是 | 单次订单对应的客户标识，不用于跨单用户识别 |
| customer_unique_id | text | 是 | 跨订单唯一用户标识；用户分析主键 |
| zip_code | text | 视图推导/可空 | 规范化五位邮编前缀；文本保留前导0 |
| geo_zip | text | 视图推导/可空 | 已覆盖的标准邮编外键；未覆盖为NULL，原邮编仍保留 |
| city | text | 视图推导/可空 | 源城市文本 |
| state | text | 视图推导/可空 | 源州代码 |

- `dim_customer_customer_unique_id_fkey`：`FOREIGN KEY (customer_unique_id) REFERENCES mart.dim_user(customer_unique_id)`
- `dim_customer_geo_zip_fkey`：`FOREIGN KEY (geo_zip) REFERENCES mart.dim_geolocation(zip_code)`
- `dim_customer_pkey`：`PRIMARY KEY (customer_id)`

## mart.dim_date（物理表）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| calendar_date | date | 是 | 公历日期，日维度主键 |
| month_start | date | 是 | 购买月份的首日 |
| calendar_year | integer | 是 | 公历年 |
| calendar_month | integer | 是 | 公历月1–12 |

- `dim_date_calendar_month_check`：`CHECK (((calendar_month >= 1) AND (calendar_month <= 12)))`
- `dim_date_pkey`：`PRIMARY KEY (calendar_date)`

## mart.dim_geolocation（物理表）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| zip_code | text | 是 | 规范化五位邮编前缀；文本保留前导0 |
| latitude | double precision | 视图推导/可空 | 去重后有效坐标纬度中位数，单位度 |
| longitude | double precision | 视图推导/可空 | 去重后有效坐标经度中位数，单位度 |
| distinct_source_rows | integer | 是 | 该邮编去重后的地理记录数 |
| valid_coordinate_rows | integer | 是 | 满足全球经纬度范围的去重地理记录数 |

- `dim_geolocation_pkey`：`PRIMARY KEY (zip_code)`

## mart.dim_month（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| month_start | date | 视图推导/可空 | 购买月份的首日 |
| calendar_year | integer | 视图推导/可空 | 公历年 |
| calendar_month | integer | 视图推导/可空 | 公历月1–12 |


## mart.dim_product（物理表）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| product_id | text | 是 | 商品标识 |
| category | text | 是 | 葡语类目；mart中缺失为__unknown__ |
| category_english | text | 视图推导/可空 | 英文类目翻译，未覆盖为NULL |
| name_length | integer | 视图推导/可空 | 源商品名称长度 |
| description_length | integer | 视图推导/可空 | 源商品描述长度 |
| photos_qty | integer | 视图推导/可空 | 商品照片数 |
| weight_g | numeric | 视图推导/可空 | 商品重量，克 |
| length_cm | numeric | 视图推导/可空 | 商品长度，厘米 |
| height_cm | numeric | 视图推导/可空 | 商品高度，厘米 |
| width_cm | numeric | 视图推导/可空 | 商品宽度，厘米 |

- `dim_product_pkey`：`PRIMARY KEY (product_id)`

## mart.dim_seller（物理表）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| seller_id | text | 是 | 商户标识 |
| zip_code | text | 视图推导/可空 | 规范化五位邮编前缀；文本保留前导0 |
| geo_zip | text | 视图推导/可空 | 已覆盖的标准邮编外键；未覆盖为NULL，原邮编仍保留 |
| city | text | 视图推导/可空 | 源城市文本 |
| state | text | 视图推导/可空 | 源州代码 |

- `dim_seller_geo_zip_fkey`：`FOREIGN KEY (geo_zip) REFERENCES mart.dim_geolocation(zip_code)`
- `dim_seller_pkey`：`PRIMARY KEY (seller_id)`

## mart.dim_user（物理表）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| customer_unique_id | text | 是 | 跨订单唯一用户标识；用户分析主键 |

- `dim_user_pkey`：`PRIMARY KEY (customer_unique_id)`

## mart.eligible_orders（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| order_id | text | 视图推导/可空 | 订单标识；订单级表主键，商品表复合主键的第一项 |
| customer_id | text | 视图推导/可空 | 单次订单对应的客户标识，不用于跨单用户识别 |
| customer_unique_id | text | 视图推导/可空 | 跨订单唯一用户标识；用户分析主键 |
| status | text | 视图推导/可空 | 源订单状态 |
| purchased_at | timestamp without time zone | 视图推导/可空 | 购买时间，无时区源时间 |
| purchase_date | date | 视图推导/可空 | 购买日，关联日期维表 |
| month_start | date | 视图推导/可空 | 购买月份的首日 |
| approved_at | timestamp without time zone | 视图推导/可空 | 付款批准时间，可缺失 |
| carrier_at | timestamp without time zone | 视图推导/可空 | 交承运商时间，可缺失 |
| delivered_at | timestamp without time zone | 视图推导/可空 | 实际送达时间，可缺失 |
| estimated_at | timestamp without time zone | 视图推导/可空 | 预计送达时间，可缺失 |
| customer_state | text | 视图推导/可空 | 该订单客户州；不从跨单用户维表推断固定位置 |
| is_eligible | boolean | 视图推导/可空 | delivered且购买时间有效，为核心指标默认范围 |
| has_items | boolean | 视图推导/可空 | 是否存在商品明细；FALSE时商品金额为NULL |
| has_payment | boolean | 视图推导/可空 | 是否存在支付记录；FALSE时支付金额为NULL |
| item_count | integer | 视图推导/可空 | 该订单商品明细行数 |
| merchandise | numeric(18,2) | 视图推导/可空 | 商品price之和，BRL，不含运费，不是财务确认收入 |
| freight | numeric(18,2) | 视图推导/可空 | 运费之和或商品行运费，BRL |
| payment | numeric(18,2) | 视图推导/可空 | 支付记录金额之和，BRL |
| review_count | integer | 视图推导/可空 | 源评价行数，review_id不要求唯一 |
| review_mean | numeric | 视图推导/可空 | 每订单评价平均分，汇总时对订单等权 |
| latest_review_score | integer | 视图推导/可空 | 按回答时间、创建时间、review_id、评分排序取最新评分1–5 |
| delivery_days | numeric | 视图推导/可空 | 有效订单的实际送达减购买时间，秒/86400；异常或缺失为NULL |
| is_late | boolean | 视图推导/可空 | 实际送达日大于预计日；无效配送分母外为NULL |
| delivery_anomaly | boolean | 视图推导/可空 | 实际送达早于购买，或预计日早于购买日；只标记，不删除交易 |


## mart.kpi_overview（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| orders | bigint | 视图推导/可空 | 该统计范围订单数；类目内去重，跨类目不可加总 |
| users | bigint | 视图推导/可空 | 该统计范围唯一购买用户数；RFM/复购表为分组用户数 |
| merchandise | numeric | 视图推导/可空 | 商品price之和，BRL，不含运费，不是财务确认收入 |
| freight | numeric | 视图推导/可空 | 运费之和或商品行运费，BRL |
| payment | numeric | 视图推导/可空 | 支付记录金额之和，BRL |
| average_order_value | numeric | 视图推导/可空 | 商品成交额/有效订单数，BRL/单 |
| delivery_days | numeric | 视图推导/可空 | 有效订单的实际送达减购买时间，秒/86400；异常或缺失为NULL |
| delivery_n | bigint | 视图推导/可空 | 有效配送时长样本数 |
| late_rate | numeric | 视图推导/可空 | 逾期样本数/late_n，0–1 |
| late_n | bigint | 视图推导/可空 | 有效逾期判断样本数 |
| review_mean | numeric | 视图推导/可空 | 每订单评价平均分，汇总时对订单等权 |
| reviewed_orders | bigint | 视图推导/可空 | 有评价的有效订单数 |


## mart.monthly_kpis（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| month_start | date | 视图推导/可空 | 购买月份的首日 |
| is_complete | boolean | 视图推导/可空 | 月份处于首完整月及观察终点之间 |
| orders | bigint | 视图推导/可空 | 该统计范围订单数；类目内去重，跨类目不可加总 |
| users | bigint | 视图推导/可空 | 该统计范围唯一购买用户数；RFM/复购表为分组用户数 |
| merchandise | numeric | 视图推导/可空 | 商品price之和，BRL，不含运费，不是财务确认收入 |
| freight | numeric | 视图推导/可空 | 运费之和或商品行运费，BRL |
| payment | numeric | 视图推导/可空 | 支付记录金额之和，BRL |
| average_order_value | numeric | 视图推导/可空 | 商品成交额/有效订单数，BRL/单 |


## mart.order_financials（物理表）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| order_id | text | 是 | 订单标识；订单级表主键，商品表复合主键的第一项 |
| item_count | integer | 是 | 该订单商品明细行数 |
| merchandise | numeric(18,2) | 是 | 商品price之和，BRL，不含运费，不是财务确认收入 |
| freight | numeric(18,2) | 是 | 运费之和或商品行运费，BRL |

- `order_financials_order_id_fkey`：`FOREIGN KEY (order_id) REFERENCES mart.order_wide(order_id) DEFERRABLE INITIALLY DEFERRED`
- `order_financials_pkey`：`PRIMARY KEY (order_id)`

## mart.order_item_fact（物理表）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| order_id | text | 是 | 订单标识；订单级表主键，商品表复合主键的第一项 |
| item_id | integer | 是 | 订单内商品序号，与order_id组成主键 |
| product_id | text | 是 | 商品标识 |
| seller_id | text | 是 | 商户标识 |
| shipping_limit_at | timestamp without time zone | 视图推导/可空 | 商品发货截止时间 |
| price | numeric(18,2) | 是 | 商品明细金额，BRL |
| freight | numeric(18,2) | 是 | 运费之和或商品行运费，BRL |

- `order_item_fact_freight_check`：`CHECK ((freight >= (0)::numeric))`
- `order_item_fact_order_id_fkey`：`FOREIGN KEY (order_id) REFERENCES mart.order_wide(order_id)`
- `order_item_fact_pkey`：`PRIMARY KEY (order_id, item_id)`
- `order_item_fact_price_check`：`CHECK ((price >= (0)::numeric))`
- `order_item_fact_product_id_fkey`：`FOREIGN KEY (product_id) REFERENCES mart.dim_product(product_id)`
- `order_item_fact_seller_id_fkey`：`FOREIGN KEY (seller_id) REFERENCES mart.dim_seller(seller_id)`

## mart.order_payment_agg（物理表）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| order_id | text | 是 | 订单标识；订单级表主键，商品表复合主键的第一项 |
| payment_count | integer | 是 | 每订单支付记录数 |
| payment | numeric(18,2) | 是 | 支付记录金额之和，BRL |
| installments_max | integer | 视图推导/可空 | 订单内最大分期数，仅描述支付记录 |

- `order_payment_agg_order_id_fkey`：`FOREIGN KEY (order_id) REFERENCES mart.order_wide(order_id) DEFERRABLE INITIALLY DEFERRED`
- `order_payment_agg_pkey`：`PRIMARY KEY (order_id)`

## mart.order_review_agg（物理表）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| order_id | text | 是 | 订单标识；订单级表主键，商品表复合主键的第一项 |
| review_count | integer | 是 | 源评价行数，review_id不要求唯一 |
| review_mean | numeric | 是 | 每订单评价平均分，汇总时对订单等权 |
| latest_review_score | integer | 是 | 按回答时间、创建时间、review_id、评分排序取最新评分1–5 |

- `order_review_agg_latest_review_score_check`：`CHECK (((latest_review_score >= 1) AND (latest_review_score <= 5)))`
- `order_review_agg_order_id_fkey`：`FOREIGN KEY (order_id) REFERENCES mart.order_wide(order_id) DEFERRABLE INITIALLY DEFERRED`
- `order_review_agg_pkey`：`PRIMARY KEY (order_id)`

## mart.order_status_distribution（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| status | text | 视图推导/可空 | 源订单状态 |
| orders | bigint | 视图推导/可空 | 该统计范围订单数；类目内去重，跨类目不可加总 |
| order_share | numeric | 视图推导/可空 | 该状态订单数/全部订单数，0–1 |


## mart.order_wide（物理表）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| order_id | text | 是 | 订单标识；订单级表主键，商品表复合主键的第一项 |
| customer_id | text | 是 | 单次订单对应的客户标识，不用于跨单用户识别 |
| customer_unique_id | text | 是 | 跨订单唯一用户标识；用户分析主键 |
| status | text | 是 | 源订单状态 |
| purchased_at | timestamp without time zone | 视图推导/可空 | 购买时间，无时区源时间 |
| purchase_date | date | 视图推导/可空 | 购买日，关联日期维表 |
| month_start | date | 视图推导/可空 | 购买月份的首日 |
| approved_at | timestamp without time zone | 视图推导/可空 | 付款批准时间，可缺失 |
| carrier_at | timestamp without time zone | 视图推导/可空 | 交承运商时间，可缺失 |
| delivered_at | timestamp without time zone | 视图推导/可空 | 实际送达时间，可缺失 |
| estimated_at | timestamp without time zone | 视图推导/可空 | 预计送达时间，可缺失 |
| customer_state | text | 视图推导/可空 | 该订单客户州；不从跨单用户维表推断固定位置 |
| is_eligible | boolean | 是 | delivered且购买时间有效，为核心指标默认范围 |
| has_items | boolean | 是 | 是否存在商品明细；FALSE时商品金额为NULL |
| has_payment | boolean | 是 | 是否存在支付记录；FALSE时支付金额为NULL |
| item_count | integer | 是 | 该订单商品明细行数 |
| merchandise | numeric(18,2) | 视图推导/可空 | 商品price之和，BRL，不含运费，不是财务确认收入 |
| freight | numeric(18,2) | 视图推导/可空 | 运费之和或商品行运费，BRL |
| payment | numeric(18,2) | 视图推导/可空 | 支付记录金额之和，BRL |
| review_count | integer | 是 | 源评价行数，review_id不要求唯一 |
| review_mean | numeric | 视图推导/可空 | 每订单评价平均分，汇总时对订单等权 |
| latest_review_score | integer | 视图推导/可空 | 按回答时间、创建时间、review_id、评分排序取最新评分1–5 |
| delivery_days | numeric | 视图推导/可空 | 有效订单的实际送达减购买时间，秒/86400；异常或缺失为NULL |
| is_late | boolean | 视图推导/可空 | 实际送达日大于预计日；无效配送分母外为NULL |
| delivery_anomaly | boolean | 是 | 实际送达早于购买，或预计日早于购买日；只标记，不删除交易 |

- `order_wide_customer_id_fkey`：`FOREIGN KEY (customer_id) REFERENCES mart.dim_customer(customer_id)`
- `order_wide_customer_unique_id_fkey`：`FOREIGN KEY (customer_unique_id) REFERENCES mart.dim_user(customer_unique_id)`
- `order_wide_pkey`：`PRIMARY KEY (order_id)`
- `order_wide_purchase_date_fkey`：`FOREIGN KEY (purchase_date) REFERENCES mart.dim_date(calendar_date)`

## mart.quality_checks（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| all_orders_without_items | bigint | 视图推导/可空 | 全状态中缺商品明细的订单数 |
| eligible_without_items | bigint | 视图推导/可空 | 有效订单中缺商品明细的订单数 |
| eligible_without_payment | bigint | 视图推导/可空 | 有效订单中缺支付记录的订单数 |
| eligible_missing_delivery | bigint | 视图推导/可空 | 有效订单中缺实际送达时间的订单数 |
| eligible_delivery_anomalies | bigint | 视图推导/可空 | 有效订单中配送时间异常的订单数 |
| eligible_missing_user | bigint | 视图推导/可空 | 有效订单中缺跨单用户标识的订单数 |
| missing_purchase_timestamp | bigint | 视图推导/可空 | 全订单中缺购买时间的订单数 |


## mart.region_sales（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| state | text | 视图推导/可空 | 源州代码 |
| orders | bigint | 视图推导/可空 | 该统计范围订单数；类目内去重，跨类目不可加总 |
| users | bigint | 视图推导/可空 | 该统计范围唯一购买用户数；RFM/复购表为分组用户数 |
| merchandise | numeric | 视图推导/可空 | 商品price之和，BRL，不含运费，不是财务确认收入 |
| freight | numeric | 视图推导/可空 | 运费之和或商品行运费，BRL |
| contribution | numeric | 视图推导/可空 | 该分组商品成交额/同口径总成交额，0–1 |


## mart.repurchase_distribution（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| frequency | bigint | 视图推导/可空 | 用户有效订单总数 |
| users | bigint | 视图推导/可空 | 该统计范围唯一购买用户数；RFM/复购表为分组用户数 |
| share | numeric | 视图推导/可空 | 该分组计数占其总体计数的比例0–1 |


## mart.repurchase_summary（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| users | bigint | 视图推导/可空 | 该统计范围唯一购买用户数；RFM/复购表为分组用户数 |
| repeat_users | bigint | 视图推导/可空 | 有效订单数至少2的用户数 |
| repeat_rate | numeric | 视图推导/可空 | repeat_users/users，0–1，受观察期影响 |


## mart.review_distribution（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| score | integer | 视图推导/可空 | 评价评分1–5 |
| orders | bigint | 视图推导/可空 | 该统计范围订单数；类目内去重，跨类目不可加总 |
| share | numeric | 视图推导/可空 | 该分组计数占其总体计数的比例0–1 |


## mart.rfm_segments（视图）

| 字段 | SQL类型 | NOT NULL约束 | 业务含义 |
|---|---|---|---|
| segment | text | 视图推导/可空 | 按METRICS.md顺序互斥分配的规则分层标签 |
| users | bigint | 视图推导/可空 | 该统计范围唯一购买用户数；RFM/复购表为分组用户数 |
| user_share | numeric | 视图推导/可空 | 该层用户数/全有效购买用户数，0–1 |
| merchandise | numeric | 视图推导/可空 | 商品price之和，BRL，不含运费，不是财务确认收入 |
| contribution | numeric | 视图推导/可空 | 该分组商品成交额/同口径总成交额，0–1 |
