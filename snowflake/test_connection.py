import os
import snowflake.connector


conn = snowflake.connector.connect(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    password=os.environ["SNOWFLAKE_PASSWORD"],
    warehouse="COMPUTE_WH",
    database="RETAIL_ANALYTICS",
    schema="ANALYTICS",
)

try:
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            DATE,
            REVENUE,
            QUANTITY,
            ORDERS,
            CUSTOMERS,
            PRODUCTS
        FROM VW_FORECASTING_FEATURES
        ORDER BY DATE
    """)

    rows = cursor.fetchall()

    print(f"Snowflake connection successful")
    print(f"Rows retrieved: {len(rows)}")
    print()
    
    for row in rows:
        print(row)

finally:
    cursor.close()
    conn.close()
