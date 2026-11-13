-- Every object below belongs only to P1. No DROP CASCADE and no raw writes.
CREATE TABLE IF NOT EXISTS mart.dim_geolocation (
    zip_code text PRIMARY KEY, latitude double precision, longitude double precision,
    distinct_source_rows integer NOT NULL, valid_coordinate_rows integer NOT NULL
);
CREATE TABLE IF NOT EXISTS mart.dim_user (customer_unique_id text PRIMARY KEY);
CREATE TABLE IF NOT EXISTS mart.dim_customer (
    customer_id text PRIMARY KEY, customer_unique_id text NOT NULL REFERENCES mart.dim_user,
    zip_code text, geo_zip text REFERENCES mart.dim_geolocation, city text, state text
);
CREATE TABLE IF NOT EXISTS mart.dim_product (
    product_id text PRIMARY KEY, category text NOT NULL, category_english text,
    name_length integer, description_length integer, photos_qty integer,
    weight_g numeric, length_cm numeric, height_cm numeric, width_cm numeric
);
CREATE TABLE IF NOT EXISTS mart.dim_seller (
    seller_id text PRIMARY KEY, zip_code text, geo_zip text REFERENCES mart.dim_geolocation,
    city text, state text
);
CREATE TABLE IF NOT EXISTS mart.dim_date (
    calendar_date date PRIMARY KEY, month_start date NOT NULL,
    calendar_year integer NOT NULL, calendar_month integer NOT NULL CHECK(calendar_month BETWEEN 1 AND 12)
);
CREATE TABLE IF NOT EXISTS mart.analysis_context (
    singleton boolean PRIMARY KEY CHECK(singleton), first_purchase date NOT NULL,
    last_purchase date NOT NULL, rfm_reference_date date NOT NULL,
    first_complete_month date NOT NULL, observation_end_exclusive date NOT NULL,
    all_status_last_purchase date NOT NULL
);
CREATE TABLE IF NOT EXISTS mart.order_wide (
    order_id text PRIMARY KEY, customer_id text NOT NULL REFERENCES mart.dim_customer,
    customer_unique_id text NOT NULL REFERENCES mart.dim_user,
    status text NOT NULL, purchased_at timestamp, purchase_date date REFERENCES mart.dim_date,
    month_start date, approved_at timestamp, carrier_at timestamp,
    delivered_at timestamp, estimated_at timestamp, customer_state text,
    is_eligible boolean NOT NULL, has_items boolean NOT NULL, has_payment boolean NOT NULL,
    item_count integer NOT NULL, merchandise numeric(18,2), freight numeric(18,2),
    payment numeric(18,2), review_count integer NOT NULL, review_mean numeric,
    latest_review_score integer, delivery_days numeric, is_late boolean,
    delivery_anomaly boolean NOT NULL
);
CREATE TABLE IF NOT EXISTS mart.order_financials (
    order_id text PRIMARY KEY REFERENCES mart.order_wide DEFERRABLE INITIALLY DEFERRED,
    item_count integer NOT NULL, merchandise numeric(18,2) NOT NULL,
    freight numeric(18,2) NOT NULL
);
CREATE TABLE IF NOT EXISTS mart.order_payment_agg (
    order_id text PRIMARY KEY REFERENCES mart.order_wide DEFERRABLE INITIALLY DEFERRED,
    payment_count integer NOT NULL, payment numeric(18,2) NOT NULL, installments_max integer
);
CREATE TABLE IF NOT EXISTS mart.order_review_agg (
    order_id text PRIMARY KEY REFERENCES mart.order_wide DEFERRABLE INITIALLY DEFERRED,
    review_count integer NOT NULL, review_mean numeric NOT NULL,
    latest_review_score integer NOT NULL CHECK(latest_review_score BETWEEN 1 AND 5)
);
CREATE TABLE IF NOT EXISTS mart.order_item_fact (
    order_id text NOT NULL REFERENCES mart.order_wide, item_id integer NOT NULL,
    product_id text NOT NULL REFERENCES mart.dim_product,
    seller_id text NOT NULL REFERENCES mart.dim_seller,
    shipping_limit_at timestamp, price numeric(18,2) NOT NULL CHECK(price>=0),
    freight numeric(18,2) NOT NULL CHECK(freight>=0), PRIMARY KEY(order_id,item_id)
);
CREATE INDEX IF NOT EXISTS order_wide_purchase_idx ON mart.order_wide(purchase_date);
CREATE INDEX IF NOT EXISTS order_wide_user_idx ON mart.order_wide(customer_unique_id);
CREATE INDEX IF NOT EXISTS order_item_product_idx ON mart.order_item_fact(product_id);
CREATE INDEX IF NOT EXISTS order_item_seller_idx ON mart.order_item_fact(seller_id);

TRUNCATE mart.order_item_fact, mart.order_financials, mart.order_payment_agg,
         mart.order_review_agg, mart.order_wide, mart.dim_customer, mart.dim_user,
         mart.dim_product, mart.dim_seller, mart.dim_geolocation, mart.dim_date, mart.analysis_context;

INSERT INTO mart.dim_geolocation
SELECT zip_code,
       percentile_cont(0.5) WITHIN GROUP(ORDER BY lat) FILTER(WHERE lat BETWEEN -90 AND 90 AND lng BETWEEN -180 AND 180),
       percentile_cont(0.5) WITHIN GROUP(ORDER BY lng) FILTER(WHERE lat BETWEEN -90 AND 90 AND lng BETWEEN -180 AND 180),
       count(*),count(*) FILTER(WHERE lat BETWEEN -90 AND 90 AND lng BETWEEN -180 AND 180)
FROM core.geolocation GROUP BY zip_code;
INSERT INTO mart.dim_user SELECT DISTINCT customer_unique_id FROM core.customers;
INSERT INTO mart.dim_customer
SELECT c.customer_id,c.customer_unique_id,c.zip_code,g.zip_code,c.city,c.state
FROM core.customers c LEFT JOIN mart.dim_geolocation g USING(zip_code);
INSERT INTO mart.dim_seller
SELECT s.seller_id,s.zip_code,g.zip_code,s.city,s.state
FROM core.sellers s LEFT JOIN mart.dim_geolocation g USING(zip_code);
INSERT INTO mart.dim_product
SELECT p.product_id,coalesce(p.category,'__unknown__'),t.product_category_name_english,
       p.name_length,p.description_length,p.photos_qty,p.weight_g,p.length_cm,p.height_cm,p.width_cm
FROM core.products p LEFT JOIN raw.category_translation t ON t.product_category_name=p.category;
INSERT INTO mart.dim_date
SELECT d::date,date_trunc('month',d)::date,extract(year FROM d)::integer,extract(month FROM d)::integer
FROM generate_series((SELECT min(purchased_at)::date FROM core.orders),
                     (SELECT max(purchased_at)::date FROM core.orders),interval '1 day') d;
INSERT INTO mart.analysis_context
SELECT true,min(purchased_at)::date,max(purchased_at)::date,max(purchased_at)::date+1,
       CASE WHEN min(purchased_at)::date=date_trunc('month',min(purchased_at))::date
            THEN min(purchased_at)::date ELSE (date_trunc('month',min(purchased_at))+interval '1 month')::date END,
       date_trunc('month',max(purchased_at))::date,
       (SELECT max(purchased_at)::date FROM core.orders)
FROM core.orders WHERE status='delivered' AND purchased_at IS NOT NULL;

-- These three independent aggregations are each one row per order BEFORE joining.
INSERT INTO mart.order_financials
SELECT order_id,count(*),sum(price),sum(freight) FROM core.order_items GROUP BY order_id;
INSERT INTO mart.order_payment_agg
SELECT order_id,count(*),sum(amount),max(installments) FROM core.payments GROUP BY order_id;
INSERT INTO mart.order_review_agg
WITH ranked AS (
    SELECT *,row_number() OVER(PARTITION BY order_id ORDER BY answered_at DESC NULLS LAST,
        created_at DESC NULLS LAST,review_id DESC,score DESC) AS rn FROM core.reviews
)
SELECT order_id,count(*),avg(score),max(score) FILTER(WHERE rn=1) FROM ranked GROUP BY order_id;

INSERT INTO mart.order_wide
SELECT o.order_id,o.customer_id,c.customer_unique_id,o.status,o.purchased_at,o.purchased_at::date,
       date_trunc('month',o.purchased_at)::date,o.approved_at,o.carrier_at,o.delivered_at,o.estimated_at,c.state,
       o.status='delivered' AND o.purchased_at IS NOT NULL,
       f.order_id IS NOT NULL,p.order_id IS NOT NULL,coalesce(f.item_count,0),f.merchandise,f.freight,p.payment,
       coalesce(r.review_count,0),r.review_mean,r.latest_review_score,
       CASE WHEN o.status='delivered' AND o.delivered_at>=o.purchased_at
            THEN extract(epoch FROM o.delivered_at-o.purchased_at)/86400 END,
       CASE WHEN o.status='delivered' AND o.delivered_at>=o.purchased_at AND o.estimated_at>=o.purchased_at::date
            THEN o.delivered_at::date>o.estimated_at::date END,
       coalesce(o.delivered_at<o.purchased_at OR o.estimated_at<o.purchased_at::date,false)
FROM core.orders o JOIN mart.dim_customer c USING(customer_id)
LEFT JOIN mart.order_financials f USING(order_id)
LEFT JOIN mart.order_payment_agg p USING(order_id)
LEFT JOIN mart.order_review_agg r USING(order_id);
INSERT INTO mart.order_item_fact SELECT * FROM core.order_items;

CREATE OR REPLACE VIEW mart.dim_month AS
SELECT DISTINCT month_start,calendar_year,calendar_month FROM mart.dim_date;
CREATE OR REPLACE VIEW mart.eligible_orders AS SELECT * FROM mart.order_wide WHERE is_eligible;
CREATE OR REPLACE VIEW mart.kpi_overview AS
SELECT count(*) AS orders,count(DISTINCT customer_unique_id) AS users,
       coalesce(sum(merchandise),0) AS merchandise,coalesce(sum(freight),0) AS freight,
       coalesce(sum(payment),0) AS payment,sum(merchandise)/NULLIF(count(*),0) AS average_order_value,
       avg(delivery_days) AS delivery_days,count(delivery_days) AS delivery_n,
       avg(is_late::integer) AS late_rate,count(is_late) AS late_n,
       avg(review_mean) AS review_mean,count(review_mean) AS reviewed_orders
FROM mart.eligible_orders;
CREATE OR REPLACE VIEW mart.order_status_distribution AS
SELECT status,count(*) AS orders,count(*)::numeric/sum(count(*)) OVER() AS order_share
FROM mart.order_wide GROUP BY status;
CREATE OR REPLACE VIEW mart.monthly_kpis AS
SELECT m.month_start,m.month_start>=c.first_complete_month AND m.month_start<c.observation_end_exclusive AS is_complete,
       count(o.order_id) AS orders,count(DISTINCT o.customer_unique_id) AS users,
       coalesce(sum(o.merchandise),0) AS merchandise,coalesce(sum(o.freight),0) AS freight,
       coalesce(sum(o.payment),0) AS payment,sum(o.merchandise)/NULLIF(count(o.order_id),0) AS average_order_value
FROM mart.dim_month m CROSS JOIN mart.analysis_context c
LEFT JOIN mart.eligible_orders o ON o.month_start=m.month_start
WHERE m.month_start BETWEEN date_trunc('month',c.first_purchase)::date AND date_trunc('month',c.last_purchase)::date
GROUP BY m.month_start,c.first_complete_month,c.observation_end_exclusive;
CREATE OR REPLACE VIEW mart.category_monthly AS
SELECT o.month_start,p.category,count(DISTINCT i.order_id) AS orders,count(*) AS items,
       sum(i.price) AS merchandise,sum(i.freight) AS freight
FROM mart.order_item_fact i JOIN mart.eligible_orders o USING(order_id)
JOIN mart.dim_product p USING(product_id) GROUP BY o.month_start,p.category;
CREATE OR REPLACE VIEW mart.category_ranking AS
SELECT p.category,count(DISTINCT i.order_id) AS orders,count(*) AS items,sum(i.price) AS merchandise,
       sum(i.freight) AS freight,sum(i.price)/NULLIF(sum(sum(i.price)) OVER(),0) AS contribution,
       dense_rank() OVER(ORDER BY sum(i.price) DESC) AS sales_rank
FROM mart.order_item_fact i JOIN mart.eligible_orders o USING(order_id)
JOIN mart.dim_product p USING(product_id) GROUP BY p.category;
CREATE OR REPLACE VIEW mart.region_sales AS
SELECT customer_state AS state,count(*) AS orders,count(DISTINCT customer_unique_id) AS users,
       coalesce(sum(merchandise),0) AS merchandise,coalesce(sum(freight),0) AS freight,
       sum(merchandise)/NULLIF(sum(sum(merchandise)) OVER(),0) AS contribution
FROM mart.eligible_orders GROUP BY customer_state;
CREATE OR REPLACE VIEW mart.review_distribution AS
SELECT latest_review_score AS score,count(*) AS orders,count(*)::numeric/sum(count(*)) OVER() AS share
FROM mart.eligible_orders WHERE latest_review_score IS NOT NULL GROUP BY latest_review_score;
CREATE OR REPLACE VIEW mart.quality_checks AS
SELECT count(*) FILTER(WHERE NOT has_items) AS all_orders_without_items,
       count(*) FILTER(WHERE is_eligible AND NOT has_items) AS eligible_without_items,
       count(*) FILTER(WHERE is_eligible AND NOT has_payment) AS eligible_without_payment,
       count(*) FILTER(WHERE is_eligible AND delivered_at IS NULL) AS eligible_missing_delivery,
       count(*) FILTER(WHERE is_eligible AND delivery_anomaly) AS eligible_delivery_anomalies,
       count(*) FILTER(WHERE is_eligible AND customer_unique_id IS NULL) AS eligible_missing_user,
       count(*) FILTER(WHERE purchased_at IS NULL) AS missing_purchase_timestamp
FROM mart.order_wide;
