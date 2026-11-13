-- P3_ASSOCIATION: all eligible orders, including missing values for denominator accounting.
SELECT order_id,customer_unique_id,customer_state,is_late,review_mean,latest_review_score
FROM mart.eligible_orders ORDER BY order_id;
