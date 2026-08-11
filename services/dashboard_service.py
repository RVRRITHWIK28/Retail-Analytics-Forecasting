from pathlib import Path
import pandas as pd
from sqlalchemy import text

from database.connection import engine

BASE_DIR = Path(__file__).resolve().parent.parent


# -------------------------------
# KPI CARDS
# -------------------------------

def get_kpis(country="All"):
    if country == "All":
        query = text("""
        SELECT
            COALESCE(SUM(revenue), 0) AS revenue,
            COUNT(DISTINCT invoice_no) AS orders,
            COUNT(DISTINCT customer_key) AS customers
        FROM public.fact_sales;
        """)
        df = pd.read_sql(query, engine)
    else:
        query = text("""
        SELECT
            COALESCE(SUM(f.revenue), 0) AS revenue,
            COUNT(DISTINCT f.invoice_no) AS orders,
            COUNT(DISTINCT f.customer_key) AS customers
        FROM public.fact_sales f
        JOIN public.dim_country c ON f.country_key = c.country_key
        WHERE c.country = :country;
        """)
        df = pd.read_sql(query, engine, params={"country": country})

    country_count_query = text("SELECT COUNT(*) AS countries FROM public.dim_country;")
    country_count = pd.read_sql(country_count_query, engine).iloc[0]["countries"]

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
    query = text("""
    SELECT country
    FROM public.dim_country
    ORDER BY country;
    """)
    df = pd.read_sql(query, engine)
    return df["country"].tolist()


def revenue_trend(country="All"):
    if country == "All":
        sql_path = BASE_DIR / "sql" / "revenue_trend.sql"
        with open(sql_path, encoding="utf-8") as f:
            query = text(f.read())
        return pd.read_sql(query, engine)
    else:
        query = text("""
        SELECT
            d.year,
            d.month,
            ROUND(SUM(f.revenue)::numeric, 2) AS revenue
        FROM public.fact_sales f
        JOIN public.dim_date d ON f.date_key = d.date_key
        JOIN public.dim_country c ON f.country_key = c.country_key
        WHERE c.country = :country
        GROUP BY d.year, d.month
        ORDER BY d.year, d.month;
        """)
        return pd.read_sql(query, engine, params={"country": country})


def top_products(country="All"):
    if country == "All":
        sql_path = BASE_DIR / "sql" / "top_products.sql"
        with open(sql_path, encoding="utf-8") as f:
            query = text(f.read())
        return pd.read_sql(query, engine)
    else:
        query = text("""
        SELECT
            p.description,
            ROUND(SUM(f.revenue)::numeric, 2) AS revenue
        FROM public.fact_sales f
        JOIN public.dim_product p ON f.product_key = p.product_key
        JOIN public.dim_country c ON f.country_key = c.country_key
        WHERE c.country = :country
        GROUP BY p.description
        ORDER BY revenue DESC
        LIMIT 10;
        """)
        return pd.read_sql(query, engine, params={"country": country})


def country_sales(country="All"):
    if country == "All":
        sql_path = BASE_DIR / "sql" / "country_sales.sql"
        with open(sql_path, encoding="utf-8") as f:
            query = text(f.read())
        return pd.read_sql(query, engine)
    else:
        query = text("""
        SELECT
            c.country,
            ROUND(SUM(f.revenue)::numeric, 2) AS revenue
        FROM public.fact_sales f
        JOIN public.dim_country c ON f.country_key = c.country_key
        WHERE c.country = :country
        GROUP BY c.country
        ORDER BY revenue DESC;
        """)
        return pd.read_sql(query, engine, params={"country": country})


def monthly_sales(country="All"):
    if country == "All":
        sql_path = BASE_DIR / "sql" / "monthly_sales.sql"
        with open(sql_path, encoding="utf-8") as f:
            query = text(f.read())
        return pd.read_sql(query, engine)
    else:
        query = text("""
        SELECT
            d.year,
            d.month,
            ROUND(SUM(f.revenue)::numeric, 2) AS revenue
        FROM public.fact_sales f
        JOIN public.dim_date d ON f.date_key = d.date_key
        JOIN public.dim_country c ON f.country_key = c.country_key
        WHERE c.country = :country
        GROUP BY d.year, d.month
        ORDER BY d.year, d.month;
        """)
        return pd.read_sql(query, engine, params={"country": country})


def business_insights(country="All"):
    if country == "All":
        query = text("""
        SELECT
            ROUND(SUM(revenue)::numeric, 2) AS revenue,
            ROUND(AVG(revenue)::numeric, 2) AS avg_order,
            ROUND(MAX(revenue)::numeric, 2) AS max_sale
        FROM public.fact_sales;
        """)
        return pd.read_sql(query, engine)
    else:
        query = text("""
        SELECT
            ROUND(SUM(f.revenue)::numeric, 2) AS revenue,
            ROUND(AVG(f.revenue)::numeric, 2) AS avg_order,
            ROUND(MAX(f.revenue)::numeric, 2) AS max_sale
        FROM public.fact_sales f
        JOIN public.dim_country c ON f.country_key = c.country_key
        WHERE c.country = :country;
        """)
        return pd.read_sql(query, engine, params={"country": country})


def get_years():
    query = text("""
    SELECT DISTINCT year
    FROM public.dim_date
    ORDER BY year;
    """)
    df = pd.read_sql(query, engine)
    return df["year"].tolist()


def world_revenue():
    query = text("""
    SELECT
        c.country,
        ROUND(SUM(f.revenue)::numeric, 2) AS revenue
    FROM public.fact_sales f
    JOIN public.dim_country c ON f.country_key = c.country_key
    GROUP BY c.country;
    """)
    return pd.read_sql(query, engine)