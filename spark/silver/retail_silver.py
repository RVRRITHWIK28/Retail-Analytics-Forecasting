from pathlib import Path

from pyspark.sql import functions as F

from spark.config.spark_session import create_spark_session


PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRONZE_PATH = PROJECT_ROOT / "data" / "bronze" / "retail"
SILVER_PATH = PROJECT_ROOT / "data" / "silver" / "retail"


def build_silver_layer(spark):
    print("=" * 70)
    print("RETAIL ANALYTICS & REVENUE FORECASTING")
    print("Silver Layer Transformation")
    print("=" * 70)

    print(f"Bronze Input : {BRONZE_PATH}")
    print(f"Silver Output: {SILVER_PATH}")

    # Read Bronze
    bronze_df = spark.read.parquet(str(BRONZE_PATH))

    bronze_rows = bronze_df.count()

    print(f"\nBronze Rows : {bronze_rows}")

    # Clean and validate
    silver_df = (
        bronze_df
        .withColumn("Description", F.trim(F.col("Description")))
        .withColumn("Country", F.trim(F.col("Country")))
        .withColumn("StockCode", F.trim(F.col("StockCode")))
        .withColumn("InvoiceNo", F.trim(F.col("InvoiceNo")))
        .filter(F.col("InvoiceNo").isNotNull())
        .filter(F.col("StockCode").isNotNull())
        .filter(F.col("InvoiceDate").isNotNull())
        .filter(F.col("Quantity").isNotNull())
        .filter(F.col("UnitPrice").isNotNull())
        .filter(F.col("Revenue").isNotNull())
        .filter(F.col("Quantity") > 0)
        .filter(F.col("UnitPrice") > 0)
        .withColumn(
            "CalculatedRevenue",
            F.round(F.col("Quantity") * F.col("UnitPrice"), 2)
        )
        .withColumn("Year", F.year("InvoiceDate"))
        .withColumn("MonthNumber", F.month("InvoiceDate"))
        .withColumn("Day", F.dayofmonth("InvoiceDate"))
        .withColumn("DayOfWeek", F.dayofweek("InvoiceDate"))
        .withColumn("Hour", F.hour("InvoiceDate"))
        .withColumn(
            "YearMonth",
            F.date_format("InvoiceDate", "yyyy-MM")
        )
    )

    silver_rows = silver_df.count()

    print(f"Silver Rows : {silver_rows}")
    print(f"Rows Removed: {bronze_rows - silver_rows}")

    print("\nSILVER SCHEMA")
    print("-" * 70)
    silver_df.printSchema()

    print("\nSILVER SAMPLE")
    print("-" * 70)

    (
        silver_df
        .select(
            "InvoiceNo",
            "StockCode",
            "Quantity",
            "UnitPrice",
            "Revenue",
            "CalculatedRevenue",
            "Year",
            "MonthNumber",
            "YearMonth",
        )
        .show(5, truncate=False)
    )

    # Revenue validation
    revenue_mismatches = (
        silver_df
        .filter(
            F.abs(
                F.col("Revenue") - F.col("CalculatedRevenue")
            ) > 0.01
        )
        .count()
    )

    print("\nSILVER QUALITY CHECKS")
    print("-" * 70)
    print(f"Revenue Mismatches: {revenue_mismatches}")

    # Remove Bronze-only ingestion metadata from Silver.
    silver_output = silver_df.drop(
        "_ingestion_timestamp",
        "_source_file",
        "_ingestion_date",
        "Month",
    )

    (
        silver_output
        .write
        .mode("overwrite")
        .partitionBy("Year", "MonthNumber")
        .parquet(str(SILVER_PATH))
    )

    print("\nSilver dataset written successfully.")
    print("Format      : Parquet")
    print("Partitioned : Year, MonthNumber")
    print(f"Output      : {SILVER_PATH}")

    print("=" * 70)
    print("SILVER TRANSFORMATION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    spark = create_spark_session()

    try:
        build_silver_layer(spark)
    finally:
        spark.stop()
