CREATE OR REPLACE VIEW mart.customer_rfm AS
WITH totals AS (
    SELECT customer_unique_id,max(purchased_at)::date AS last_purchase_date,
           count(*) AS frequency,CASE WHEN bool_and(has_items) THEN sum(merchandise) END AS monetary
    FROM mart.eligible_orders GROUP BY customer_unique_id
), rfm_values AS (
    SELECT t.*,c.rfm_reference_date,c.rfm_reference_date-t.last_purchase_date AS recency
    FROM totals t CROSS JOIN mart.analysis_context c
), bounds AS (
    SELECT percentile_disc(ARRAY[0.2,0.4,0.6,0.8]) WITHIN GROUP(ORDER BY recency) AS r,
           percentile_disc(ARRAY[0.2,0.4,0.6,0.8]) WITHIN GROUP(ORDER BY frequency) AS f,
           percentile_disc(ARRAY[0.2,0.4,0.6,0.8]) WITHIN GROUP(ORDER BY monetary) AS m
    FROM rfm_values
), scored AS (
    SELECT v.*,
       CASE WHEN recency<=r[1] THEN 5 WHEN recency<=r[2] THEN 4 WHEN recency<=r[3] THEN 3 WHEN recency<=r[4] THEN 2 ELSE 1 END AS r_score,
       CASE WHEN frequency<=f[1] THEN 1 WHEN frequency<=f[2] THEN 2 WHEN frequency<=f[3] THEN 3 WHEN frequency<=f[4] THEN 4 ELSE 5 END AS f_score,
       CASE WHEN monetary IS NULL THEN NULL WHEN monetary<=m[1] THEN 1 WHEN monetary<=m[2] THEN 2 WHEN monetary<=m[3] THEN 3 WHEN monetary<=m[4] THEN 4 ELSE 5 END AS m_score
    FROM rfm_values v CROSS JOIN bounds
)
SELECT *,CASE WHEN monetary IS NULL THEN '数据待核对'
    WHEN r_score>=4 AND f_score>=4 AND m_score>=4 THEN '核心价值'
    WHEN r_score>=4 AND f_score>=4 THEN '活跃复购'
    WHEN r_score>=4 THEN '近期用户'
    WHEN r_score<=2 AND m_score>=4 THEN '高价值待唤回'
    WHEN r_score<=2 THEN '沉睡用户' ELSE '其他用户' END AS segment FROM scored;
CREATE OR REPLACE VIEW mart.rfm_segments AS
SELECT segment,count(*) AS users,count(*)::numeric/sum(count(*)) OVER() AS user_share,
       sum(monetary) AS merchandise,sum(monetary)/NULLIF(sum(sum(monetary)) OVER(),0) AS contribution
FROM mart.customer_rfm GROUP BY segment;
CREATE OR REPLACE VIEW mart.repurchase_distribution AS
SELECT frequency,count(*) AS users,count(*)::numeric/sum(count(*)) OVER() AS share
FROM mart.customer_rfm GROUP BY frequency;
CREATE OR REPLACE VIEW mart.repurchase_summary AS
SELECT count(*) AS users,count(*) FILTER(WHERE frequency>=2) AS repeat_users,
       count(*) FILTER(WHERE frequency>=2)::numeric/NULLIF(count(*),0) AS repeat_rate
FROM mart.customer_rfm;
CREATE OR REPLACE VIEW mart.customer_cohort AS
SELECT customer_unique_id,min(month_start) AS cohort_month
FROM mart.eligible_orders GROUP BY customer_unique_id;
CREATE OR REPLACE VIEW mart.cohort_sizes AS
SELECT cohort_month,count(*) AS new_users FROM mart.customer_cohort GROUP BY cohort_month;
CREATE OR REPLACE VIEW mart.cohort_retention AS
WITH activity AS (
    SELECT DISTINCT customer_unique_id,month_start FROM mart.eligible_orders
), counts AS (
    SELECT c.cohort_month,a.month_start,count(*) AS active_users
    FROM mart.customer_cohort c JOIN activity a USING(customer_unique_id) GROUP BY 1,2
), grid AS (
    SELECT s.*,n AS month_age,(s.cohort_month+make_interval(months=>n))::date AS target_month,
           s.cohort_month<c.first_complete_month AS cohort_left_truncated,
           c.first_complete_month,c.observation_end_exclusive
    FROM mart.cohort_sizes s CROSS JOIN mart.analysis_context c
    CROSS JOIN LATERAL generate_series(0,
        (extract(year FROM age(date_trunc('month',c.last_purchase),date_trunc('month',c.first_purchase)))*12+
         extract(month FROM age(date_trunc('month',c.last_purchase),date_trunc('month',c.first_purchase))))::integer) n
)
SELECT g.cohort_month,g.month_age,g.target_month,g.new_users,g.cohort_left_truncated,
       g.target_month>=g.first_complete_month AND g.target_month<g.observation_end_exclusive AS is_observed,
       CASE WHEN g.target_month>=g.first_complete_month AND g.target_month<g.observation_end_exclusive
            THEN coalesce(a.active_users,0) END AS active_users,
       CASE WHEN g.target_month>=g.first_complete_month AND g.target_month<g.observation_end_exclusive
            THEN coalesce(a.active_users,0)::numeric/g.new_users END AS retention
FROM grid g LEFT JOIN counts a ON a.cohort_month=g.cohort_month AND a.month_start=g.target_month;
