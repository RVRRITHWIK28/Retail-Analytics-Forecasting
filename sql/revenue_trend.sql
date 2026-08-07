SELECT
    d.year,
    d.month,
    SUM(f.revenue) AS revenue
FROM fact_sales f
JOIN dim_date d
ON f.date_key=d.date_key
GROUP BY d.year,d.month
ORDER BY d.year,d.month;