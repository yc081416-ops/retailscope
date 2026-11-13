# P0 真实数据质量基线

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
