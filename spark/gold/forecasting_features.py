from pathlib import Path

from pyspark.sql import functions as F

from spark.config.spark_session import create_spark_session


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = PROJECT_ROOT / "data" / "gold" / "monthly_revenue"
OUTPUT_PATH = PROJECT_ROOT / "data" / "gold" / "forecasting_features"


def build_forecasting_features(spark):
    print("=" * 70)
    print("RETAIL ANALYTICS & REVENUE FORECASTING")
    print("Gold Layer - Forecasting Features")
    print("=" * 70)

    print(f"Input  : {INPUT_PATH}")
    print(f"Output : {OUTPUT_PATH}")

    df = spark.read.parquet(str(INPUT_PATH))

    print(f"\nInput Rows: {df.count()}")

    forecasting_df = (
        df
        .withColumn(
            "Date",
            F.to_date(
                F.concat(F.col("YearMonth"), F.lit("-01"))
            )
        )
        .select(
            "Date",
            F.col("TotalRevenue").alias("Revenue"),
            F.col("TotalQuantity").alias("Quantity"),
            F.col("UniqueInvoices").alias("Orders"),
            F.col("UniqueCustomers").alias("Customers"),
            F.col("UniqueProducts").alias("Products"),
        )
        .orderBy("Date")
    )

    print("\nFORECASTING DATASET")
    print("-" * 70)

    forecasting_df.show(20, truncate=False)

    print("\nForecasting Rows:", forecasting_df.count())

    print("\nDate Range:")
    forecasting_df.select(
        F.min("Date").alias("StartDate"),
        F.max("Date").alias("EndDate")
    ).show()

    print("\nNull Check:")
    forecasting_df.select([
        F.sum(F.col(c).isNull().cast("int")).alias(c)
        for c in forecasting_df.columns
    ]).show()

    (
        forecasting_df
        .write
        .mode("overwrite")
        .parquet(str(OUTPUT_PATH))
    )

    print("\nForecasting dataset written successfully.")
    print("Format : Parquet")
    print(f"Output : {OUTPUT_PATH}")

    print("=" * 70)
    print("FORECASTING FEATURE ENGINEERING COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    spark = create_spark_session()

    try:
        build_forecasting_features(spark)
    finally:
        spark.stop()
