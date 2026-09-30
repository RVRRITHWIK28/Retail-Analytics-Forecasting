from spark.config.spark_session import create_spark_session


def main():
    spark = create_spark_session()

    print("=" * 60)
    print("RETAIL ANALYTICS & REVENUE FORECASTING")
    print("Apache Spark Environment")
    print("=" * 60)

    print(f"Spark Version : {spark.version}")
    print(f"Application   : {spark.sparkContext.appName}")
    print("Status        : Spark session created successfully")

    spark.stop()


if __name__ == "__main__":
    main()