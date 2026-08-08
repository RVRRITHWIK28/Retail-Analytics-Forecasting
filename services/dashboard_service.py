from pathlib import Path

import pandas as pd

from database.connection import engine

BASE_DIR = Path(__file__).resolve().parent.parent


# -------------------------------
# KPI CARDS
# -------------------------------

def get_kpis(country="All"):

    if country == "All":

        query = """
        SELECT
            COALESCE(SUM(revenue),0) AS revenue,
            COUNT(DISTINCT invoice_no) AS orders,
            COUNT(DISTINCT customer_key) AS customers
        FROM public.fact_sales;
        """

    else:

        query = f"""
        SELECT
            COALESCE(SUM(f.revenue),0) AS revenue,
            COUNT(DISTINCT f.invoice_no) AS orders,
            COUNT(DISTINCT f.customer_key) AS customers
        FROM public.fact_sales f
        JOIN public.dim_country c
        ON f.country_key = c.country_key
        WHERE c.country = '{country}';
        """

    df = pd.read_sql(query, engine)

    country_count = pd.read_sql(
        "SELECT COUNT(*) AS countries FROM public.dim_country;",
        engine
    ).iloc[0]["countries"]

    return (
        float(df.iloc[0]["revenue"]),
        int(df.iloc[0]["orders"]),
        int(df.iloc[0]["customers"]),
        int(country_count),
    )


# -------------------------------
# COUNTRY DROPDOWN
# -------------------------------

def get_countries():

    query = """
    SELECT country
    FROM public.dim_country
    ORDER BY country;
    """

    df = pd.read_sql(query, engine)

    return df["country"].tolist()

def revenue_trend(country="All"):

    if country == "All":

        sql_path = BASE_DIR / "sql" / "revenue_trend.sql"

        with open(sql_path, encoding="utf-8") as f:
            query = f.read()

    else:

        query = f"""
        SELECT
            d.year,
            d.month,
            ROUND(SUM(f.revenue), 2) AS revenue
        FROM public.fact_sales f
        JOIN public.dim_date d
            ON f.date_key = d.date_key
        GROUP BY
            d.year,
            d.month
        ORDER BY
            d.year,
            d.month;
        """

    return pd.read_sql(query, engine)

def top_products(country="All"):

    if country == "All":

        sql_path = BASE_DIR / "sql" / "top_products.sql"

        with open(sql_path, encoding="utf-8") as f:
            query = f.read()

    else:

        query = f"""
        SELECT
            p.description,
            ROUND(SUM(f.revenue),2) AS revenue
        FROM public.fact_sales f
        JOIN public.dim_product p
            ON f.product_key = p.product_key
        JOIN public.dim_country c
            ON f.country_key = c.country_key
        WHERE c.country = '{country}'
        GROUP BY p.description
        ORDER BY revenue DESC
        LIMIT 10;
        """

    return pd.read_sql(query, engine)

def country_sales(country="All"):

    if country == "All":

        sql_path = BASE_DIR / "sql" / "country_sales.sql"

        with open(sql_path, encoding="utf-8") as f:
            query = f.read()

    else:

        query = f"""
        SELECT
            c.country,
            ROUND(SUM(f.revenue),2) AS revenue
        FROM public.fact_sales f
        JOIN public.dim_country c
            ON f.country_key = c.country_key
        WHERE c.country = '{country}'
        GROUP BY c.country
        ORDER BY revenue DESC;
        """

    return pd.read_sql(query, engine)

def monthly_sales(country="All"):

    if country == "All":

        sql_path = BASE_DIR / "sql" / "monthly_sales.sql"

        with open(sql_path, encoding="utf-8") as f:
            query = f.read()

    else:

        query = f"""
        SELECT
    d.year,
    d.month,
    ROUND(SUM(f.revenue), 2) AS revenue
FROM public.fact_sales f
JOIN public.dim_date d
    ON f.date_key = d.date_key
GROUP BY
    d.year,
    d.month
ORDER BY
    d.year,
    d.month;
        """

    return pd.read_sql(query, engine)

def business_insights(country="All"):

    if country == "All":

        query = """
        SELECT
            ROUND(SUM(revenue),2) AS revenue,
            ROUND(AVG(revenue),2) AS avg_order,
            ROUND(MAX(revenue),2) AS max_sale
        FROM public.fact_sales;
        """

    else:

        query = f"""
        SELECT
            ROUND(SUM(f.revenue),2) AS revenue,
            ROUND(AVG(f.revenue),2) AS avg_order,
            ROUND(MAX(f.revenue),2) AS max_sale
        FROM public.fact_sales f
        JOIN public.dim_country c
            ON f.country_key = c.country_key
        WHERE c.country = '{country}';
        """

    return pd.read_sql(query, engine)

def get_years():

    query = """
    SELECT DISTINCT year
    FROM public.dim_date
    ORDER BY year;
    """

    df = pd.read_sql(query, engine)

    return df["year"].tolist()

def world_revenue():

    query = """
    SELECT
        c.country,
        ROUND(SUM(f.revenue),2) AS revenue
    FROM public.fact_sales f
    JOIN public.dim_country c
        ON f.country_key = c.country_key
    GROUP BY c.country;
    """

    return pd.read_sql(query, engine)
