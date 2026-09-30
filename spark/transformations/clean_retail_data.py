from pathlib import Path

from pyspark.sql import functions as F

from spark.config.spark_session import create_spark_session
from spark.ingestion.retail_ingestion import load_retail_data


PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "retail_cleaned"


def transform_retail_data(df):
    """
    Apply Spark-based cleaning, validation, and
    analytical transformations to retail transactions.
    """

    # ---------------------------------------------------------
    # 1. Standardize text fields
    # ---------------------------------------------------------

    df = (
        df
        .withColumn("Description", F.trim(F.col("Description")))
        .withColumn("Country", F.trim(F.col("Country")))
        .withColumn("StockCode", F.trim(F.col("StockCode")))
        .withColumn("InvoiceNo", F.trim(F.col("InvoiceNo")))
    )

    # ---------------------------------------------------------
    # 2. Remove records that cannot participate in analytics
    # ---------------------------------------------------------

    df = df.filter(
        F.col("InvoiceNo").isNotNull()
        & F.col("StockCode").isNotNull()
        & F.col("InvoiceDate").isNotNull()
        & F.col("Quantity").isNotNull()
        & F.col("UnitPrice").isNotNull()
        & F.col("Revenue").isNotNull()
    )

    # ---------------------------------------------------------
    # 3. Validate business values
    # ---------------------------------------------------------

    df = df.filter(
        (F.col("Quantity") > 0)
        & (F.col("UnitPrice") > 0)
    )

    # ---------------------------------------------------------
    # 4. Recalculate revenue from transaction values
    # ---------------------------------------------------------

    df = df.withColumn(
        "CalculatedRevenue",
        F.round(
            F.col("Quantity") * F.col("UnitPrice"),
            2
        )
    )

    # ---------------------------------------------------------
    # 5. Create analytical date attributes
    # ---------------------------------------------------------

    df = (
        df
        .withColumn("Year", F.year("InvoiceDate"))
        .withColumn("MonthNumber", F.month("InvoiceDate"))
        .withColumn("Day", F.dayofmonth("InvoiceDate"))
        .withColumn("DayOfWeek", F.dayofweek("InvoiceDate"))
        .withColumn("Hour", F.hour("InvoiceDate"))
    )

    # ---------------------------------------------------------
    # 6. Create a consistent Year-Month key
    # ---------------------------------------------------------

    df = df.withColumn(
        "YearMonth",
        F.date_format("InvoiceDate", "yyyy-MM")
    )

    return df


def main():

    spark = create_spark_session()

    print("=" * 70)
    print("RETAIL ANALYTICS & REVENUE FORECASTING")
    print("PySpark Cleaning & Transformation")
    print("=" * 70)

    # Load source data
    df = load_retail_data(spark)

    source_count = df.count()

    print(f"\nSource Rows       : {source_count}")

    # Transform
    transformed_df = transform_retail_data(df)

    transformed_count = transformed_df.count()

    print(f"Transformed Rows  : {transformed_count}")
    print(f"Rows Removed      : {source_count - transformed_count}")

    # Display resulting schema
    print("\nTRANSFORMED SCHEMA")
    print("-" * 70)

    transformed_df.printSchema()

    # Display sample
    print("\nTRANSFORMED SAMPLE")
    print("-" * 70)

    transformed_df.select(
        "InvoiceNo",
        "StockCode",
        "Quantity",
        "UnitPrice",
        "Revenue",
        "CalculatedRevenue",
        "Year",
        "MonthNumber",
        "Day",
        "DayOfWeek",
        "Hour",
        "YearMonth"
    ).show(5, truncate=False)

    # ---------------------------------------------------------
    # Write curated Spark dataset
    # ---------------------------------------------------------

    print("\nWriting curated dataset...")

    (
        transformed_df
        .write
        .mode("overwrite")
        .partitionBy("Year", "MonthNumber")
        .parquet(str(OUTPUT_PATH))
    )

    print(f"Output Path       : {OUTPUT_PATH}")
    print("Format            : Parquet")
    print("Partitioned By    : Year, MonthNumber")

    print("\n" + "=" * 70)
    print("SPARK TRANSFORMATION COMPLETED")
    print("=" * 70)

    spark.stop()


if __name__ == "__main__":
    main()