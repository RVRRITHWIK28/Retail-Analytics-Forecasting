import pandas as pd
from database.connection import engine

def get_kpis():

    revenue = pd.read_sql(
        "SELECT SUM(revenue) revenue FROM fact_sales",
        engine
    ).iloc[0,0]

    orders = pd.read_sql(
        "SELECT COUNT(DISTINCT invoice_no) orders FROM fact_sales",
        engine
    ).iloc[0,0]

    customers = pd.read_sql(
        "SELECT COUNT(DISTINCT customer_key) customers FROM fact_sales",
        engine
    ).iloc[0,0]

    countries = pd.read_sql(
        "SELECT COUNT(*) countries FROM dim_country",
        engine
    ).iloc[0,0]

    return revenue, orders, customers, countries

def revenue_trend():
    query = """
    SELECT
        d.year,
        d.month,
        SUM(f.revenue) revenue
    FROM fact_sales f
    JOIN dim_date d
      ON f.date_key=d.date_key
    GROUP BY d.year,d.month
    ORDER BY d.year,d.month;
    """

    return pd.read_sql(query, engine)