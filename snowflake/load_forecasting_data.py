import os
import snowflake.connector
import pandas as pd


def load_forecasting_data():
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse="COMPUTE_WH",
        database="RETAIL_ANALYTICS",
        schema="ANALYTICS",
    )

    try:
        query = """
            SELECT
                DATE,
                REVENUE,
                QUANTITY,
                ORDERS,
                CUSTOMERS,
                PRODUCTS
            FROM VW_FORECASTING_FEATURES
            ORDER BY DATE
        """

        df = pd.read_sql(query, conn)

        df["DATE"] = pd.to_datetime(df["DATE"])
        df["REVENUE"] = pd.to_numeric(df["REVENUE"])
        df["QUANTITY"] = pd.to_numeric(df["QUANTITY"])
        df["ORDERS"] = pd.to_numeric(df["ORDERS"])
        df["CUSTOMERS"] = pd.to_numeric(df["CUSTOMERS"])
        df["PRODUCTS"] = pd.to_numeric(df["PRODUCTS"])

        return df

    finally:
        conn.close()


if __name__ == "__main__":
    df = load_forecasting_data()

    print("Snowflake → Pandas successful")
    print(f"Rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print()
    print(df.to_string(index=False))
