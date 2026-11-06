from pathlib import Path

from pyspark.sql import functions as F

from spark.config.spark_session import create_spark_session


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SILVER_PATH = PROJECT_ROOT / "data" / "silver" / "retail"
GOLD_PATH = PROJECT_ROOT / "data" / "gold" / "product_performance"


def build_product_performance(spark):
    print("=" * 70)
    print("RETAIL ANALYTICS & REVENUE FORECASTING")
    print("Gold Layer - Product Performance")
    print("=" * 70)

    print(f"Silver Input : {SILVER_PATH}")
    print(f"Gold Output  : {GOLD_PATH}")

    silver_df = spark.read.parquet(str(SILVER_PATH))

    print(f"\nSilver Rows : {silver_df.count()}")

    product_performance = (
        silver_df
        .groupBy("StockCode", "Description")
        .agg(
            F.round(F.sum("Revenue"), 2).alias("TotalRevenue"),
            F.sum("Quantity").alias("TotalQuantity"),
            F.countDistinct("InvoiceNo").alias("UniqueInvoices"),
            F.countDistinct("CustomerID").alias("UniqueCustomers"),
            F.round(F.avg("UnitPrice"), 2).alias("AverageUnitPrice"),
        )
        .orderBy(F.desc("TotalRevenue"))
    )

    print("\nTOP PRODUCT PERFORMANCE")
    print("-" * 70)

    (
        product_performance
        .show(20, truncate=False)
    )

    print("\nGold Rows:", product_performance.count())

    (
        product_performance
        .write
        .mode("overwrite")
        .parquet(str(GOLD_PATH))
    )

    print("\nGold dataset written successfully.")
    print("Format : Parquet")
    print(f"Output : {GOLD_PATH}")

    print("=" * 70)
    print("GOLD PRODUCT PERFORMANCE COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    spark = create_spark_session()

    try:
        build_product_performance(spark)
    finally:
        spark.stop()
