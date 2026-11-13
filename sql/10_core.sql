-- Typed source views. Failed casts abort the warehouse transaction; raw stays untouched.
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS mart;
CREATE OR REPLACE VIEW core.customers AS
SELECT customer_id, customer_unique_id, lpad(customer_zip_code_prefix,5,'0') AS zip_code,
       customer_city AS city, customer_state AS state FROM raw.customers;
CREATE OR REPLACE VIEW core.products AS
SELECT product_id, NULLIF(btrim(product_category_name),'') AS category,
       NULLIF(product_name_lenght,'')::integer AS name_length,
       NULLIF(product_description_lenght,'')::integer AS description_length,
       NULLIF(product_photos_qty,'')::integer AS photos_qty,
       NULLIF(product_weight_g,'')::numeric AS weight_g,
       NULLIF(product_length_cm,'')::numeric AS length_cm,
       NULLIF(product_height_cm,'')::numeric AS height_cm,
       NULLIF(product_width_cm,'')::numeric AS width_cm FROM raw.products;
CREATE OR REPLACE VIEW core.sellers AS
SELECT seller_id, lpad(seller_zip_code_prefix,5,'0') AS zip_code,
       seller_city AS city, seller_state AS state FROM raw.sellers;
CREATE OR REPLACE VIEW core.orders AS
SELECT order_id, customer_id, order_status AS status,
       NULLIF(order_purchase_timestamp,'')::timestamp AS purchased_at,
       NULLIF(order_approved_at,'')::timestamp AS approved_at,
       NULLIF(order_delivered_carrier_date,'')::timestamp AS carrier_at,
       NULLIF(order_delivered_customer_date,'')::timestamp AS delivered_at,
       NULLIF(order_estimated_delivery_date,'')::timestamp AS estimated_at FROM raw.orders;
CREATE OR REPLACE VIEW core.order_items AS
SELECT order_id, order_item_id::integer AS item_id, product_id, seller_id,
       NULLIF(shipping_limit_date,'')::timestamp AS shipping_limit_at,
       price::numeric(18,2) AS price, freight_value::numeric(18,2) AS freight
FROM raw.order_items;
CREATE OR REPLACE VIEW core.payments AS
SELECT order_id, payment_sequential::integer AS sequential, payment_type,
       payment_installments::integer AS installments, payment_value::numeric(18,2) AS amount
FROM raw.order_payments;
CREATE OR REPLACE VIEW core.reviews AS
SELECT review_id, order_id, review_score::integer AS score,
       NULLIF(review_comment_title,'') AS title, NULLIF(review_comment_message,'') AS message,
       NULLIF(review_creation_date,'')::timestamp AS created_at,
       NULLIF(review_answer_timestamp,'')::timestamp AS answered_at FROM raw.order_reviews;
CREATE OR REPLACE VIEW core.geolocation AS
SELECT DISTINCT lpad(geolocation_zip_code_prefix,5,'0') AS zip_code,
       geolocation_lat::double precision AS lat, geolocation_lng::double precision AS lng,
       geolocation_city AS city, geolocation_state AS state FROM raw.geolocation;
