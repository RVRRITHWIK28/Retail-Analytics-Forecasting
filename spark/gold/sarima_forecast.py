from pathlib import Path

import pandas as pd
from pyspark.sql import functions as F

from spark.config.spark_session import create_spark_session


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = PROJECT_ROOT / "data" / "gold" / "forecasting_features"
OUTPUT_PATH = PROJECT_ROOT / "data" / "gold" / "sarima_forecast"


def build_sarima_forecast(spark):
    print("=" * 70)
    print("RETAIL ANALYTICS & REVENUE FORECASTING")
    print("SARIMA Baseline Forecast")
    print("=" * 70)

    print(f"Input : {INPUT_PATH}")
    print(f"Output: {OUTPUT_PATH}")

    # Read forecasting features from Gold
    spark_df = spark.read.parquet(str(INPUT_PATH))

    print(f"\nInput Rows: {spark_df.count()}")

    # Only the time series required by SARIMA
    pdf = (
        spark_df
        .select("Date", "Revenue")
        .orderBy("Date")
        .toPandas()
    )

    pdf["Date"] = pd.to_datetime(pdf["Date"])
    pdf = pdf.set_index("Date").sort_index()

    # Monthly frequency
    pdf = pdf.asfreq("MS")

    print("\nREVENUE TIME SERIES")
    print("-" * 70)
    print(pdf)

    # ------------------------------------------------------------
    # Train / validation split
    # ------------------------------------------------------------
    # With only 13 observations, reserve the final 3 months
    # for validation.
    train = pdf.iloc[:-3]["Revenue"]
    test = pdf.iloc[-3:]["Revenue"]

    print("\nTRAINING PERIOD")
    print("-" * 70)
    print(f"Start : {train.index.min().date()}")
    print(f"End   : {train.index.max().date()}")
    print(f"Rows  : {len(train)}")

    print("\nVALIDATION PERIOD")
    print("-" * 70)
    print(f"Start : {test.index.min().date()}")
    print(f"End   : {test.index.max().date()}")
    print(f"Rows  : {len(test)}")

    # ------------------------------------------------------------
    # SARIMA
    # ------------------------------------------------------------
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
    except ImportError:
        raise ImportError(
            "statsmodels is required. Install it with: "
            "pip install statsmodels"
        )

    print("\nTraining SARIMA model...")

    # Small-data baseline.
    # Seasonal component is intentionally omitted because
    # 10 training observations are insufficient to estimate
    # a reliable 12-month seasonal pattern.
    model = SARIMAX(
        train,
        order=(1, 1, 1),
        seasonal_order=(0, 0, 0, 0),
        enforce_stationarity=False,
        enforce_invertibility=False,
    )

    fitted_model = model.fit(disp=False)

    # ------------------------------------------------------------
    # Validation forecast
    # ------------------------------------------------------------
    forecast = fitted_model.forecast(steps=len(test))

    comparison = pd.DataFrame({
        "ActualRevenue": test.values,
        "ForecastRevenue": forecast.values,
    }, index=test.index)

    comparison["AbsoluteError"] = (
        comparison["ActualRevenue"]
        - comparison["ForecastRevenue"]
    ).abs()

    comparison["AbsolutePercentageError"] = (
        comparison["AbsoluteError"]
        / comparison["ActualRevenue"].abs()
    ) * 100

    mae = comparison["AbsoluteError"].mean()
    rmse = (
        (
            comparison["ActualRevenue"]
            - comparison["ForecastRevenue"]
        ) ** 2
    ).mean() ** 0.5

    mape = comparison["AbsolutePercentageError"].mean()

    print("\nVALIDATION RESULTS")
    print("-" * 70)
    print(comparison)

    print("\nMODEL METRICS")
    print("-" * 70)
    print(f"MAE  : {mae:,.2f}")
    print(f"RMSE : {rmse:,.2f}")
    print(f"MAPE : {mape:.2f}%")

    # ------------------------------------------------------------
    # Future forecast
    # ------------------------------------------------------------
    # Refit using all available observations before producing
    # the next 3-month forecast.
    full_model = SARIMAX(
        pdf["Revenue"],
        order=(1, 1, 1),
        seasonal_order=(0, 0, 0, 0),
        enforce_stationarity=False,
        enforce_invertibility=False,
    )

    full_fitted_model = full_model.fit(disp=False)

    future_forecast = full_fitted_model.forecast(steps=3)

    future_df = pd.DataFrame({
        "Date": future_forecast.index,
        "ForecastRevenue": future_forecast.values,
    })

    print("\nNEXT 3-MONTH FORECAST")
    print("-" * 70)
    print(future_df.to_string(index=False))

    # ------------------------------------------------------------
    # Save validation + future forecast
    # ------------------------------------------------------------
    validation_df = comparison.reset_index()
    validation_df.columns = [
        "Date",
        "ActualRevenue",
        "ForecastRevenue",
        "AbsoluteError",
        "AbsolutePercentageError",
    ]

    validation_spark = spark.createDataFrame(validation_df)

    future_spark = spark.createDataFrame(future_df)

    validation_output = OUTPUT_PATH / "validation"
    future_output = OUTPUT_PATH / "future_forecast"

    (
        validation_spark
        .write
        .mode("overwrite")
        .parquet(str(validation_output))
    )

    (
        future_spark
        .write
        .mode("overwrite")
        .parquet(str(future_output))
    )

    print("\nForecast results written successfully.")
    print(f"Validation : {validation_output}")
    print(f"Future     : {future_output}")

    print("\nIMPORTANT MODEL LIMITATION")
    print("-" * 70)
    print(
        "Only 13 monthly observations are available. "
        "Therefore this SARIMA result is a baseline demonstration, "
        "not a statistically robust production forecast."
    )

    print("=" * 70)
    print("SARIMA BASELINE COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    spark = create_spark_session()

    try:
        build_sarima_forecast(spark)
    finally:
        spark.stop()
