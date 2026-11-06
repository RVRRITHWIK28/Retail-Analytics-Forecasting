from pathlib import Path

from pyspark.sql import functions as F

from spark.config.spark_session import create_spark_session


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SILVER_PATH = PROJECT_ROOT / "data" / "silver" / "retail"
GOLD_PATH = PROJECT_ROOT / "data" / "gold" / "monthly_revenue"


def build_monthly_revenue(spark):
    print("=" * 70)
    print("RETAIL ANALYTICS & REVENUE FORECASTING")
    print("Gold Layer - Monthly Revenue")
    print("=" * 70)

    print(f"Silver Input : {SILVER_PATH}")
    print(f"Gold Output  : {GOLD_PATH}")

    silver_df = spark.read.parquet(str(SILVER_PATH))

    print(f"\nSilver Rows : {silver_df.count()}")

    monthly_revenue = (
        silver_df
        .groupBy("YearMonth")
        .agg(
            F.round(F.sum("Revenue"), 2).alias("TotalRevenue"),
            F.sum("Quantity").alias("TotalQuantity"),
            F.countDistinct("InvoiceNo").alias("UniqueInvoices"),
            F.countDistinct("CustomerID").alias("UniqueCustomers"),
            F.countDistinct("StockCode").alias("UniqueProducts"),
        )
        .withColumn(
            "AverageOrderValue",
            F.round(
                F.col("TotalRevenue") / F.col("UniqueInvoices"),
                2
            )
        )
        .orderBy("YearMonth")
    )

    print("\nMONTHLY REVENUE")
    print("-" * 70)

    monthly_revenue.show(20, truncate=False)

    print("\nGold Rows:", monthly_revenue.count())

    (
        monthly_revenue
        .write
        .mode("overwrite")
        .parquet(str(GOLD_PATH))
    )

    print("\nGold dataset written successfully.")
    print("Format : Parquet")
    print(f"Output : {GOLD_PATH}")

    print("=" * 70)
    print("GOLD MONTHLY REVENUE COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    spark = create_spark_session()

    try:
        build_monthly_revenue(spark)
    finally:
        spark.stop()
