SELECT
    p.description,
    ROUND(SUM(f.revenue),2) AS revenue

FROM fact_sales f

JOIN dim_product p
ON f.product_key = p.product_key

GROUP BY p.description

ORDER BY revenue DESC

LIMIT 10;