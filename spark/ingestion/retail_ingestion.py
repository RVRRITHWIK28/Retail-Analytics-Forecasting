from pathlib import Path

from pyspark.sql import DataFrame
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType,
    TimestampType,
)

from spark.config.spark_session import create_spark_session


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Input dataset
INPUT_FILE = PROJECT_ROOT / "data" / "cleaned_retail_data.csv"


# Explicit schema for the retail dataset
RETAIL_SCHEMA = StructType([
    StructField("InvoiceNo", StringType(), True),
    StructField("StockCode", StringType(), True),
    StructField("Description", StringType(), True),
    StructField("Quantity", IntegerType(), True),
    StructField("InvoiceDate", TimestampType(), True),
    StructField("UnitPrice", DoubleType(), True),
    StructField("CustomerID", DoubleType(), True),
    StructField("Country", StringType(), True),
    StructField("Revenue", DoubleType(), True),
    StructField("Month", StringType(), True),
])


def load_retail_data(spark) -> DataFrame:
    """
    Load the cleaned retail transaction dataset
    into a Spark DataFrame.
    """

    df = (
        spark.read
        .option("header", True)
        .schema(RETAIL_SCHEMA)
        .csv(str(INPUT_FILE))
    )

    return df


def main():
    spark = create_spark_session()

    print("=" * 70)
    print("RETAIL ANALYTICS & REVENUE FORECASTING")
    print("Spark Data Ingestion")
    print("=" * 70)

    print(f"Input file: {INPUT_FILE}")

    df = load_retail_data(spark)

    print("\nSchema:")
    df.printSchema()

    print(f"\nTotal Rows: {df.count()}")

    print("\nSample Records:")
    df.show(5, truncate=False)

    spark.stop()


if __name__ == "__main__":
    main()