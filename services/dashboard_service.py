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
        FROM fact_sales;
        """

    else:

        query = f"""
        SELECT
            COALESCE(SUM(f.revenue),0) AS revenue,
            COUNT(DISTINCT f.invoice_no) AS orders,
            COUNT(DISTINCT f.customer_key) AS customers
        FROM fact_sales f
        JOIN dim_country c
        ON f.country_key = c.country_key
        WHERE c.country = '{country}';
        """

    df = pd.read_sql(query, engine)

    country_count = pd.read_sql(
        "SELECT COUNT(*) AS countries FROM dim_country;",
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
    FROM dim_country
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
            SUM(f.revenue) AS revenue
        FROM fact_sales f
        JOIN dim_date d
            ON f.date_key = d.date_key
        JOIN dim_country c
            ON f.country_key = c.country_key
        WHERE c.country = '{country}'
        GROUP BY d.year, d.month
        ORDER BY d.year, d.month;
        """

    return pd.read_sql(query, engine)