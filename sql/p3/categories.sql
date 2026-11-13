-- P3_CATEGORIES: item amounts already reconcile to P1; category order counts overlap.
SELECT * FROM mart.category_ranking ORDER BY sales_rank,category;
