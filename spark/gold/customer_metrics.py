from pathlib import Path

from pyspark.sql import functions as F

from spark.config.spark_session import create_spark_session


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SILVER_PATH = PROJECT_ROOT / "data" / "silver" / "retail"
GOLD_PATH = PROJECT_ROOT / "data" / "gold" / "customer_metrics"


def build_customer_metrics(spark):
    print("=" * 70)
    print("RETAIL ANALYTICS & REVENUE FORECASTING")
    print("Gold Layer - Customer Metrics")
    print("=" * 70)

    print(f"Silver Input : {SILVER_PATH}")
    print(f"Gold Output  : {GOLD_PATH}")

    silver_df = spark.read.parquet(str(SILVER_PATH))

    print(f"\nSilver Rows : {silver_df.count()}")

    customer_metrics = (
        silver_df
        .filter(F.col("CustomerID").isNotNull())
        .groupBy("CustomerID")
        .agg(
            F.round(F.sum("Revenue"), 2).alias("TotalRevenue"),
            F.sum("Quantity").alias("TotalQuantity"),
            F.countDistinct("InvoiceNo").alias("UniqueInvoices"),
            F.countDistinct("StockCode").alias("UniqueProducts"),
            F.min("InvoiceDate").alias("FirstPurchaseDate"),
            F.max("InvoiceDate").alias("LastPurchaseDate"),
        )
        .withColumn(
            "CustomerLifetimeDays",
            F.datediff(
                F.to_date("LastPurchaseDate"),
                F.to_date("FirstPurchaseDate")
            )
        )
        .withColumn(
            "AverageOrderValue",
            F.round(
                F.col("TotalRevenue") / F.col("UniqueInvoices"),
                2
            )
        )
        .orderBy(F.desc("TotalRevenue"))
    )

    print("\nTOP CUSTOMER METRICS")
    print("-" * 70)

    customer_metrics.show(20, truncate=False)

    print("\nGold Rows:", customer_metrics.count())

    (
        customer_metrics
        .write
        .mode("overwrite")
        .parquet(str(GOLD_PATH))
    )

    print("\nGold dataset written successfully.")
    print("Format : Parquet")
    print(f"Output : {GOLD_PATH}")

    print("=" * 70)
    print("GOLD CUSTOMER METRICS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    spark = create_spark_session()

    try:
        build_customer_metrics(spark)
    finally:
        spark.stop()
