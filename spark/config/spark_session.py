from pyspark.sql import SparkSession


def create_spark_session():
    """
    Create and configure the Spark session
    for the Retail Analytics & Revenue Forecasting Platform.
    """

    spark = (
        SparkSession.builder
        .appName("RetailAnalyticsForecasting")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.driver.memory", "2g")

        # Windows local filesystem configuration
        .config(
            "spark.hadoop.fs.file.impl",
            "org.apache.hadoop.fs.RawLocalFileSystem"
        )
        .config(
            "spark.hadoop.fs.file.impl.disable.cache",
            "true"
        )

        # Avoid Hadoop permission handling on local development
        .config(
            "spark.hadoop.fs.permissions.umask-mode",
            "022"
        )

        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    return spark