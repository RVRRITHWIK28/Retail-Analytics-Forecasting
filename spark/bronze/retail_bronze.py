from pathlib import Path

from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    TimestampType,
    DoubleType,
)

from spark.config.spark_session import create_spark_session


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = PROJECT_ROOT / "data" / "cleaned_retail_data.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "bronze" / "retail"


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


def build_bronze_layer(spark):
    print("=" * 70)
    print("RETAIL ANALYTICS & REVENUE FORECASTING")
    print("Bronze Layer Ingestion")
    print("=" * 70)

    print(f"Input Path  : {INPUT_PATH}")
    print(f"Output Path : {OUTPUT_PATH}")

    df = (
        spark.read
        .option("header", True)
        .schema(RETAIL_SCHEMA)
        .csv(str(INPUT_PATH))
    )

    source_rows = df.count()

    # Bronze keeps the source fields intact.
    # Only ingestion metadata is added.
    bronze_df = (
        df
        .withColumn("_ingestion_timestamp", F.current_timestamp())
        .withColumn("_source_file", F.lit(INPUT_PATH.name))
        .withColumn("_ingestion_date", F.current_date())
    )

    print(f"Source Rows : {source_rows}")
    print(f"Bronze Rows : {bronze_df.count()}")

    print("\nBRONZE SCHEMA")
    print("-" * 70)
    bronze_df.printSchema()

    (
        bronze_df
        .write
        .mode("overwrite")
        .partitionBy("Month")
        .parquet(str(OUTPUT_PATH))
    )

    print("\nBronze dataset written successfully.")
    print(f"Format      : Parquet")
    print(f"Partitioned : Month")
    print(f"Output      : {OUTPUT_PATH}")

    print("=" * 70)
    print("BRONZE INGESTION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    spark = create_spark_session()

    try:
        build_bronze_layer(spark)
    finally:
        spark.stop()

