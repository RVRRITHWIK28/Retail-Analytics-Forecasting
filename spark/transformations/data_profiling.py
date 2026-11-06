from pyspark.sql import functions as F

from spark.config.spark_session import create_spark_session
from spark.ingestion.retail_ingestion import load_retail_data


def main():
    spark = create_spark_session()

    print("=" * 70)
    print("RETAIL ANALYTICS & REVENUE FORECASTING")
    print("Spark Data Quality & Profiling")
    print("=" * 70)

    # Load dataset
    df = load_retail_data(spark)

    # ---------------------------------------------------------
    # BASIC DATASET INFORMATION
    # ---------------------------------------------------------

    total_rows = df.count()
    total_columns = len(df.columns)

    print("\nDATASET OVERVIEW")
    print("-" * 70)
    print(f"Total Rows       : {total_rows}")
    print(f"Total Columns    : {total_columns}")

    # ---------------------------------------------------------
    # DATE RANGE
    # ---------------------------------------------------------

    date_range = df.select(
        F.min("InvoiceDate").alias("min_date"),
        F.max("InvoiceDate").alias("max_date")
    ).collect()[0]

    print(f"Start Date       : {date_range['min_date']}")
    print(f"End Date         : {date_range['max_date']}")

    # ---------------------------------------------------------
    # BUSINESS METRICS
    # ---------------------------------------------------------

    metrics = df.select(
        F.sum("Revenue").alias("total_revenue"),
        F.sum("Quantity").alias("total_quantity"),
        F.countDistinct("InvoiceNo").alias("unique_invoices"),
        F.countDistinct("StockCode").alias("unique_products"),
        F.countDistinct("CustomerID").alias("unique_customers"),
        F.countDistinct("Country").alias("unique_countries")
    ).collect()[0]

    print("\nBUSINESS METRICS")
    print("-" * 70)
    print(f"Total Revenue    : {metrics['total_revenue']}")
    print(f"Total Quantity   : {metrics['total_quantity']}")
    print(f"Unique Invoices  : {metrics['unique_invoices']}")
    print(f"Unique Products  : {metrics['unique_products']}")
    print(f"Unique Customers : {metrics['unique_customers']}")
    print(f"Unique Countries : {metrics['unique_countries']}")

    # ---------------------------------------------------------
    # NULL VALUE ANALYSIS
    # ---------------------------------------------------------

    print("\nNULL VALUE ANALYSIS")
    print("-" * 70)

    null_counts = df.select([
        F.sum(
            F.when(F.col(column).isNull(), 1).otherwise(0)
        ).alias(column)
        for column in df.columns
    ]).collect()[0]

    for column in df.columns:
        print(f"{column:<15}: {null_counts[column]}")

    # ---------------------------------------------------------
    # DUPLICATE CHECK
    # ---------------------------------------------------------

    duplicate_count = (
        df.groupBy(df.columns)
        .count()
        .filter(F.col("count") > 1)
        .agg(
            F.sum(F.col("count") - 1).alias("duplicates")
        )
        .collect()[0]["duplicates"]
    )

    duplicate_count = duplicate_count or 0

    print("\nDUPLICATE CHECK")
    print("-" * 70)
    print(f"Duplicate Rows   : {duplicate_count}")

    # ---------------------------------------------------------
    # BUSINESS RULE CHECKS
    # ---------------------------------------------------------

    negative_quantity = df.filter(
        F.col("Quantity") < 0
    ).count()

    invalid_price = df.filter(
        F.col("UnitPrice") <= 0
    ).count()

    revenue_mismatch = df.filter(
        F.abs(
            F.col("Revenue") -
            (F.col("Quantity") * F.col("UnitPrice"))
        ) > 0.01
    ).count()

    print("\nBUSINESS RULE VALIDATION")
    print("-" * 70)
    print(f"Negative Quantity : {negative_quantity}")
    print(f"Invalid UnitPrice : {invalid_price}")
    print(f"Revenue Mismatch  : {revenue_mismatch}")

    # ---------------------------------------------------------
    # FINAL STATUS
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("DATA PROFILING COMPLETED")
    print("=" * 70)

    spark.stop()


if __name__ == "__main__":
    main()