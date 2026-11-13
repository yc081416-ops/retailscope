-- P3_REGIONS: one order per row; no detail-table join.
SELECT customer_state AS state,count(*) AS orders,sum(merchandise) AS merchandise,
       count(delivery_days) AS delivery_n,avg(delivery_days) AS delivery_days,
       count(is_late) AS late_n,count(*) FILTER(WHERE is_late) AS late_orders,
       avg(is_late::integer) AS late_rate,avg(review_mean) AS review_mean,
       count(review_mean) AS reviewed_orders
FROM mart.eligible_orders GROUP BY customer_state ORDER BY merchandise DESC;
