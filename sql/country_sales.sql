SELECT
    c.country,
    ROUND(SUM(f.revenue),2) AS revenue

FROM fact_sales f

JOIN dim_country c
ON f.country_key = c.country_key

GROUP BY c.country

ORDER BY revenue DESC

LIMIT 10;