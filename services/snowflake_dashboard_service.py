"""
Snowflake Dashboard Service
============================

Data access layer for the Retail Analytics & Revenue Forecasting
Platform 2.0 Streamlit dashboard.

Snowflake structure:

RETAIL_ANALYTICS
├── ANALYTICS
│   ├── FACT_SALES
│   ├── DIM_COUNTRY
│   ├── VW_MONTHLY_REVENUE
│   ├── VW_PRODUCT_PERFORMANCE
│   ├── VW_COUNTRY_PERFORMANCE
│   ├── VW_CUSTOMER_METRICS
│   └── VW_FORECASTING_FEATURES
│
└── FORECASTING
    ├── MODEL_COMPARISON
    └── REVENUE_FORECAST
"""

import os

import pandas as pd
import snowflake.connector


# ============================================================
# CONNECTION
# ============================================================

def get_connection():
    """Create and return a Snowflake connection."""

    return snowflake.connector.connect(
        account=os.getenv(
            "SNOWFLAKE_ACCOUNT",
            "DP39031.ap-southeast-7.aws",
        ),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "RETAIL_ANALYTICS"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "ANALYTICS"),
        role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
    )


# ============================================================
# COUNTRIES
# ============================================================

def get_countries():
    """Return all available countries."""

    conn = get_connection()

    try:
        query = """
            SELECT COUNTRY_NAME
            FROM ANALYTICS.VW_COUNTRY_PERFORMANCE
            ORDER BY COUNTRY_NAME
        """

        df = pd.read_sql(query, conn)

        return df["COUNTRY_NAME"].tolist()

    finally:
        conn.close()


# ============================================================
# KPIs
# ============================================================

def get_kpis(country="All"):
    """
    Return:

        revenue,
        orders,
        customers,
        country_count

    For All:
        FACT_SALES is used so DISTINCT orders/customers
        are calculated across the entire dataset.

    For a specific country:
        VW_COUNTRY_PERFORMANCE is used.
    """

    conn = get_connection()

    try:

        # ----------------------------------------------------
        # ALL COUNTRIES
        # ----------------------------------------------------

        if country == "All":

            query = """
                SELECT
                    COALESCE(SUM(REVENUE), 0) AS REVENUE,
                    COUNT(DISTINCT INVOICE_NO) AS ORDERS,
                    COUNT(DISTINCT CUSTOMER_KEY) AS CUSTOMERS
                FROM ANALYTICS.FACT_SALES
            """

            df = pd.read_sql(query, conn)

            country_count = pd.read_sql(
                """
                SELECT COUNT(*) AS COUNTRY_COUNT
                FROM ANALYTICS.DIM_COUNTRY
                """,
                conn,
            )

        # ----------------------------------------------------
        # SPECIFIC COUNTRY
        # ----------------------------------------------------

        else:

            query = """
                SELECT
                    COALESCE(TOTAL_REVENUE, 0) AS REVENUE,
                    COALESCE(TOTAL_ORDERS, 0) AS ORDERS,
                    COALESCE(UNIQUE_CUSTOMERS, 0) AS CUSTOMERS
                FROM ANALYTICS.VW_COUNTRY_PERFORMANCE
                WHERE COUNTRY_NAME = %s
            """

            df = pd.read_sql(
                query,
                conn,
                params=[country],
            )

            country_count = pd.DataFrame(
                [{"COUNTRY_COUNT": 1}]
            )

        if df.empty:
            return 0, 0, 0, 0

        revenue = float(df.iloc[0]["REVENUE"])
        orders = int(df.iloc[0]["ORDERS"])
        customers = int(df.iloc[0]["CUSTOMERS"])
        countries = int(country_count.iloc[0]["COUNTRY_COUNT"])

        return revenue, orders, customers, countries

    finally:
        conn.close()


# ============================================================
# REVENUE TREND
# ============================================================

def revenue_trend(country="All"):
    """
    Return monthly revenue trend using the column names
    expected by the Streamlit dashboard.
    """

    conn = get_connection()

    try:

        if country == "All":

            query = """
                SELECT
                    YEAR,
                    MONTH_NUMBER,
                    MONTH_NAME,
                    TOTAL_REVENUE,
                    TOTAL_QUANTITY,
                    TOTAL_ORDERS,
                    UNIQUE_CUSTOMERS,
                    UNIQUE_PRODUCTS
                FROM ANALYTICS.VW_MONTHLY_REVENUE
                ORDER BY YEAR, MONTH_NUMBER
            """

            df = pd.read_sql(query, conn)

        else:

            query = """
                SELECT
                    YEAR(TRANSACTION_DATE) AS YEAR,
                    MONTH(TRANSACTION_DATE) AS MONTH_NUMBER,
                    TO_CHAR(
                        DATE_TRUNC('MONTH', TRANSACTION_DATE),
                        'Mon'
                    ) AS MONTH_NAME,
                    SUM(REVENUE) AS TOTAL_REVENUE,
                    SUM(QUANTITY) AS TOTAL_QUANTITY,
                    COUNT(DISTINCT INVOICE_NO) AS TOTAL_ORDERS,
                    COUNT(DISTINCT CUSTOMER_KEY) AS UNIQUE_CUSTOMERS,
                    COUNT(DISTINCT PRODUCT_KEY) AS UNIQUE_PRODUCTS
                FROM ANALYTICS.FACT_SALES
                WHERE COUNTRY = %s
                GROUP BY
                    YEAR(TRANSACTION_DATE),
                    MONTH(TRANSACTION_DATE),
                    DATE_TRUNC('MONTH', TRANSACTION_DATE)
                ORDER BY
                    YEAR(TRANSACTION_DATE),
                    MONTH(TRANSACTION_DATE)
            """

            df = pd.read_sql(
                query,
                conn,
                params=[country],
            )

        # Convert Snowflake column names to the names
        # expected by the existing Streamlit dashboard.
        df = df.rename(
            columns={
                "YEAR": "year",
                "MONTH_NUMBER": "month",
                "MONTH_NAME": "month_name",
                "TOTAL_REVENUE": "revenue",
                "TOTAL_QUANTITY": "quantity",
                "TOTAL_ORDERS": "orders",
                "UNIQUE_CUSTOMERS": "customers",
                "UNIQUE_PRODUCTS": "products",
            }
        )

        return df

    finally:
        conn.close()


# ============================================================
# TOP PRODUCTS
# ============================================================

def top_products(country="All", limit=10):
    """
    Return top products by revenue.

    The returned DataFrame uses the lowercase column names
    expected by the existing Streamlit dashboard:
        stock_code
        description
        revenue
        quantity
        orders
    """

    conn = get_connection()

    try:

        if country == "All":

            query = """
                SELECT
                    STOCK_CODE,
                    DESCRIPTION,
                    TOTAL_REVENUE,
                    TOTAL_QUANTITY,
                    TOTAL_ORDERS
                FROM ANALYTICS.VW_PRODUCT_PERFORMANCE
                ORDER BY TOTAL_REVENUE DESC
                LIMIT %s
            """

            df = pd.read_sql(
                query,
                conn,
                params=[limit],
            )

        else:

            query = """
                SELECT
                    STOCK_CODE,
                    DESCRIPTION,
                    SUM(REVENUE) AS TOTAL_REVENUE,
                    SUM(QUANTITY) AS TOTAL_QUANTITY,
                    COUNT(DISTINCT INVOICE_NO) AS TOTAL_ORDERS
                FROM ANALYTICS.FACT_SALES
                WHERE COUNTRY = %s
                GROUP BY
                    STOCK_CODE,
                    DESCRIPTION
                ORDER BY TOTAL_REVENUE DESC
                LIMIT %s
            """

            df = pd.read_sql(
                query,
                conn,
                params=[country, limit],
            )

        df = df.rename(
            columns={
                "STOCK_CODE": "stock_code",
                "DESCRIPTION": "description",
                "TOTAL_REVENUE": "revenue",
                "TOTAL_QUANTITY": "quantity",
                "TOTAL_ORDERS": "orders",
            }
        )

        return df

    finally:
        conn.close()


# ============================================================
# COUNTRY SALES
# ============================================================

def country_sales(country="All", limit=15):
    """
    Return country-level revenue performance.

    Returns lowercase column names expected by the
    existing Streamlit dashboard.
    """

    conn = get_connection()

    try:

        if country == "All":

            query = """
                SELECT
                    COUNTRY_NAME,
                    TOTAL_REVENUE,
                    TOTAL_QUANTITY,
                    TOTAL_ORDERS,
                    UNIQUE_CUSTOMERS,
                    UNIQUE_PRODUCTS
                FROM ANALYTICS.VW_COUNTRY_PERFORMANCE
                ORDER BY TOTAL_REVENUE DESC
                LIMIT %s
            """

            df = pd.read_sql(
                query,
                conn,
                params=[limit],
            )

        else:

            query = """
                SELECT
                    COUNTRY_NAME,
                    TOTAL_REVENUE,
                    TOTAL_QUANTITY,
                    TOTAL_ORDERS,
                    UNIQUE_CUSTOMERS,
                    UNIQUE_PRODUCTS
                FROM ANALYTICS.VW_COUNTRY_PERFORMANCE
                WHERE COUNTRY_NAME = %s
            """

            df = pd.read_sql(
                query,
                conn,
                params=[country],
            )

        df = df.rename(
            columns={
                "COUNTRY_NAME": "country",
                "TOTAL_REVENUE": "revenue",
                "TOTAL_QUANTITY": "quantity",
                "TOTAL_ORDERS": "orders",
                "UNIQUE_CUSTOMERS": "customers",
                "UNIQUE_PRODUCTS": "products",
            }
        )

        return df

    finally:
        conn.close()


# ============================================================
# MONTHLY SALES
# ============================================================

def monthly_sales(country="All"):
    """Return monthly sales data."""

    conn = get_connection()

    try:

        # ----------------------------------------------------
        # ALL COUNTRIES
        # ----------------------------------------------------

        if country == "All":

            query = """
                SELECT
                    YEAR,
                    MONTH_NUMBER,
                    MONTH_NAME,
                    TOTAL_REVENUE,
                    TOTAL_QUANTITY,
                    TOTAL_ORDERS,
                    UNIQUE_CUSTOMERS,
                    UNIQUE_PRODUCTS
                FROM ANALYTICS.VW_MONTHLY_REVENUE
                ORDER BY YEAR, MONTH_NUMBER
            """

            df = pd.read_sql(query, conn)

            df.rename(columns={
                "YEAR": "year",
                "MONTH_NUMBER": "month",
                "MONTH_NAME": "month_name",
                "TOTAL_REVENUE": "revenue",
                "TOTAL_QUANTITY": "quantity",
                "TOTAL_ORDERS": "orders",
                "UNIQUE_CUSTOMERS": "customers",
                "UNIQUE_PRODUCTS": "products"
            }, inplace=True)

            return df

        # ----------------------------------------------------
        # SPECIFIC COUNTRY
        # ----------------------------------------------------

        query = """
            SELECT
                YEAR(TRANSACTION_DATE) AS YEAR,
                MONTH(TRANSACTION_DATE) AS MONTH_NUMBER,
                TO_CHAR(
                    DATE_TRUNC('MONTH', TRANSACTION_DATE),
                    'Mon'
                ) AS MONTH_NAME,
                SUM(REVENUE) AS TOTAL_REVENUE,
                SUM(QUANTITY) AS TOTAL_QUANTITY,
                COUNT(DISTINCT INVOICE_NO) AS TOTAL_ORDERS,
                COUNT(DISTINCT CUSTOMER_KEY) AS UNIQUE_CUSTOMERS,
                COUNT(DISTINCT PRODUCT_KEY) AS UNIQUE_PRODUCTS
            FROM ANALYTICS.FACT_SALES
            WHERE COUNTRY = %s
            GROUP BY
                YEAR(TRANSACTION_DATE),
                MONTH(TRANSACTION_DATE),
                DATE_TRUNC('MONTH', TRANSACTION_DATE)
            ORDER BY
                YEAR(TRANSACTION_DATE),
                MONTH(TRANSACTION_DATE)
        """

        return pd.read_sql(
            query,
            conn,
            params=[country],
        )

    finally:
        conn.close()


# ============================================================
# BUSINESS INSIGHTS
# ============================================================

def business_insights(country="All"):
    """Return business insight metrics for the selected country."""

    conn = get_connection()

    try:
        if country == "All":

            query = """
                SELECT
                    SUM(REVENUE) AS REVENUE,
                    AVG(REVENUE) AS AVG_ORDER,
                    MAX(REVENUE) AS MAX_SALE
                FROM ANALYTICS.FACT_SALES
            """

            df = pd.read_sql(query, conn)

        else:

            query = """
                SELECT
                    SUM(REVENUE) AS REVENUE,
                    AVG(REVENUE) AS AVG_ORDER,
                    MAX(REVENUE) AS MAX_SALE
                FROM ANALYTICS.FACT_SALES
                WHERE COUNTRY_NAME = %s
            """

            df = pd.read_sql(
                query,
                conn,
                params=(country,)
            )

        # Snowflake/pandas may return uppercase column names
        df.rename(columns={
            "REVENUE": "revenue",
            "AVG_ORDER": "avg_order",
            "MAX_SALE": "max_sale"
        }, inplace=True)

        return df

    finally:
        conn.close()


# ============================================================
# WORLD REVENUE
# ============================================================

def world_revenue():
    """Return country-level revenue for the world map."""

    conn = get_connection()

    try:
        query = """
            SELECT
                COUNTRY_NAME,
                TOTAL_REVENUE
            FROM ANALYTICS.VW_COUNTRY_PERFORMANCE
            ORDER BY TOTAL_REVENUE DESC
        """

        df = pd.read_sql(query, conn)

        df.rename(columns={
            "COUNTRY_NAME": "country",
            "TOTAL_REVENUE": "revenue"
        }, inplace=True)

        return df

    finally:
        conn.close()


# ============================================================
# MODEL COMPARISON
# ============================================================

def get_model_comparison():
    """
    Return only the latest evaluation for each forecasting model.

    Table:
        RETAIL_ANALYTICS.FORECASTING.MODEL_COMPARISON
    """

    conn = get_connection()

    try:

        query = """
            SELECT
                MODEL_NAME,
                MAE,
                RMSE,
                MAPE,
                EVALUATION_DATE
            FROM FORECASTING.MODEL_COMPARISON
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY MODEL_NAME
                ORDER BY EVALUATION_DATE DESC
            ) = 1
            ORDER BY MODEL_NAME
        """

        return pd.read_sql(query, conn)

    finally:
        conn.close()


# ============================================================
# FUTURE FORECASTS
# ============================================================

def get_future_forecasts():
    """
    Return the latest complete future forecast set.

    The forecasting pipeline inserts each forecast row separately,
    so CREATED_AT differs slightly between rows. We therefore
    identify the latest forecast run using the latest set of
    forecast dates and models.
    """

    conn = get_connection()

    try:

        query = """
            WITH ranked_forecasts AS (
                SELECT
                    FORECAST_DATE,
                    MODEL_NAME,
                    FORECAST_REVENUE,
                    CREATED_AT,
                    MAX(CREATED_AT) OVER () AS LATEST_CREATED_AT
                FROM FORECASTING.REVENUE_FORECAST
            ),

            latest_run AS (
                SELECT
                    MAX(CREATED_AT) AS RUN_END
                FROM ranked_forecasts
                WHERE CREATED_AT >= DATEADD(
                    SECOND,
                    -30,
                    LATEST_CREATED_AT
                )
            )

            SELECT
                FORECAST_DATE,
                MODEL_NAME,
                FORECAST_REVENUE,
                CREATED_AT
            FROM ranked_forecasts
            WHERE CREATED_AT >= DATEADD(
                SECOND,
                -30,
                LATEST_CREATED_AT
            )
            ORDER BY
                FORECAST_DATE,
                MODEL_NAME
        """

        return pd.read_sql(query, conn)

    finally:
        conn.close()