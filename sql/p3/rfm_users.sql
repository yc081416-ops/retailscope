-- P3_RFM_USERS: P1 scores/segments unchanged. Cohort month describes observed entry, not acquisition history.
SELECT r.*,c.cohort_month FROM mart.customer_rfm r
JOIN mart.customer_cohort c USING(customer_unique_id) ORDER BY customer_unique_id;
