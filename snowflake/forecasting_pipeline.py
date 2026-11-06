import os

import numpy as np
import pandas as pd
import snowflake.connector
import tensorflow as tf

from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from statsmodels.tsa.statespace.sarimax import SARIMAX

def load_forecasting_data():
    """Load monthly forecasting features from Snowflake."""

    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse="COMPUTE_WH",
        database="RETAIL_ANALYTICS",
        schema="ANALYTICS",
    )

    try:
        query = """
            SELECT
                DATE,
                REVENUE,
                QUANTITY,
                ORDERS,
                CUSTOMERS,
                PRODUCTS
            FROM VW_FORECASTING_FEATURES
            ORDER BY DATE
        """

        df = pd.read_sql(query, conn)

        df["DATE"] = pd.to_datetime(df["DATE"])
        df["REVENUE"] = pd.to_numeric(df["REVENUE"])

        return df

    finally:
        conn.close()


def calculate_metrics(actual, predicted):
    """Calculate forecasting evaluation metrics."""

    mae = mean_absolute_error(actual, predicted)
    rmse = mean_squared_error(actual, predicted) ** 0.5

    actual_series = pd.Series(actual)
    predicted_series = pd.Series(predicted)

    mape = (
        ((actual_series - predicted_series).abs() / actual_series)
        .replace([float("inf"), -float("inf")], pd.NA)
        .dropna()
        .mean()
        * 100
    )

    return mae, rmse, mape


def run_sarima_forecast(df):
    """Train SARIMA on first 10 months and validate on final 3 months."""

    train = df.iloc[:10]
    validation = df.iloc[10:]

    train_revenue = train.set_index("DATE")["REVENUE"]
    actual = validation["REVENUE"].values

    model = SARIMAX(
        train_revenue,
        order=(1, 1, 1),
        seasonal_order=(0, 0, 0, 0),
        enforce_stationarity=False,
        enforce_invertibility=False,
    )

    fitted_model = model.fit(disp=False)

    predictions = fitted_model.forecast(steps=len(validation))
    predictions = predictions.values

    mae, rmse, mape = calculate_metrics(actual, predictions)

    return {
        "predictions": predictions,
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
    }

def run_lstm_forecast(df):
    """Train and validate an LSTM using the same 10/3 split."""

    train = df.iloc[:10]
    validation = df.iloc[10:]

    train_values = train["REVENUE"].values.reshape(-1, 1)
    validation_values = validation["REVENUE"].values.reshape(-1, 1)

    scaler = MinMaxScaler()

    scaled_train = scaler.fit_transform(train_values)

    lookback = 3

    X_train = []
    y_train = []

    for i in range(lookback, len(scaled_train)):
        X_train.append(scaled_train[i - lookback:i])
        y_train.append(scaled_train[i])

    X_train = np.array(X_train)
    y_train = np.array(y_train)

    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(lookback, 1)),
        tf.keras.layers.LSTM(32),
        tf.keras.layers.Dense(16, activation="relu"),
        tf.keras.layers.Dense(1)
    ])

    model.compile(
        optimizer="adam",
        loss="mse"
    )

    model.fit(
        X_train,
        y_train,
        epochs=100,
        batch_size=2,
        verbose=0
    )

    # Recursive forecasting for the 3-month validation period
    history = list(scaled_train.flatten())
    predictions_scaled = []

    for _ in range(len(validation)):
        sequence = np.array(history[-lookback:]).reshape(1, lookback, 1)

        prediction = model.predict(sequence, verbose=0)[0, 0]

        predictions_scaled.append(prediction)
        history.append(prediction)

    predictions = scaler.inverse_transform(
        np.array(predictions_scaled).reshape(-1, 1)
    ).flatten()

    actual = validation_values.flatten()

    mae, rmse, mape = calculate_metrics(
        actual,
        predictions
    )

    return {
        "predictions": predictions,
        "mae": mae,
        "rmse": rmse,
        "mape": mape
    }


def generate_future_forecasts(df):
    """Generate 3-month future forecasts using all Snowflake data."""

    forecast_steps = 3

    revenue = df["REVENUE"].values

    # --------------------------------------------------
    # SARIMA — train on all available data
    # --------------------------------------------------

    revenue_series = pd.Series(
        revenue,
        index=pd.DatetimeIndex(df["DATE"]),
    )

    sarima_model = SARIMAX(
        revenue_series,
        order=(1, 1, 1),
        seasonal_order=(0, 0, 0, 0),
        enforce_stationarity=False,
        enforce_invertibility=False,
    )

    sarima_fitted = sarima_model.fit(disp=False)

    sarima_forecast = sarima_fitted.forecast(
        steps=forecast_steps
    ).values

    # --------------------------------------------------
    # LSTM — train on all available data
    # --------------------------------------------------

    values = revenue.reshape(-1, 1)

    scaler = MinMaxScaler()
    scaled_values = scaler.fit_transform(values)

    lookback = 3

    X_train = []
    y_train = []

    for i in range(lookback, len(scaled_values)):
        X_train.append(scaled_values[i - lookback:i])
        y_train.append(scaled_values[i])

    X_train = np.array(X_train)
    y_train = np.array(y_train)

    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(lookback, 1)),
        tf.keras.layers.LSTM(32),
        tf.keras.layers.Dense(16, activation="relu"),
        tf.keras.layers.Dense(1)
    ])

    model.compile(
        optimizer="adam",
        loss="mse"
    )

    model.fit(
        X_train,
        y_train,
        epochs=100,
        batch_size=2,
        verbose=0
    )

    history = list(scaled_values.flatten())
    lstm_forecast_scaled = []

    for _ in range(forecast_steps):

        sequence = np.array(
            history[-lookback:]
        ).reshape(1, lookback, 1)

        prediction = model.predict(
            sequence,
            verbose=0
        )[0, 0]

        lstm_forecast_scaled.append(prediction)
        history.append(prediction)

    lstm_forecast = scaler.inverse_transform(
        np.array(lstm_forecast_scaled).reshape(-1, 1)
    ).flatten()

    future_dates = pd.date_range(
        start=df["DATE"].max() + pd.offsets.MonthBegin(1),
        periods=forecast_steps,
        freq="MS"
    )

    return future_dates, sarima_forecast, lstm_forecast

def write_future_forecasts_to_snowflake(
    future_dates,
    sarima_forecast,
    lstm_forecast
):
    """Write future revenue forecasts to Snowflake."""

    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse="COMPUTE_WH",
        database="RETAIL_ANALYTICS",
        schema="FORECASTING",
    )

    try:
        cursor = conn.cursor()

        for date, sarima_value, lstm_value in zip(
            future_dates,
            sarima_forecast,
            lstm_forecast
        ):

            cursor.execute("""
                INSERT INTO REVENUE_FORECAST
                    (FORECAST_DATE, MODEL_NAME, FORECAST_REVENUE)
                VALUES
                    (%s, %s, %s)
            """, (
                date.date(),
                "SARIMA",
                float(sarima_value)
            ))

            cursor.execute("""
                INSERT INTO REVENUE_FORECAST
                    (FORECAST_DATE, MODEL_NAME, FORECAST_REVENUE)
                VALUES
                    (%s, %s, %s)
            """, (
                date.date(),
                "LSTM",
                float(lstm_value)
            ))

        conn.commit()

        print("\nFuture forecasts written to Snowflake successfully.")

    finally:
        cursor.close()
        conn.close()

def write_results_to_snowflake(sarima_result, lstm_result):
    """Write model metrics and future forecasts to Snowflake."""

    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse="COMPUTE_WH",
        database="RETAIL_ANALYTICS",
        schema="FORECASTING",
    )

    try:
        cursor = conn.cursor()

        # --------------------------------------------------
        # Model comparison
        # --------------------------------------------------

        cursor.execute("""
            INSERT INTO MODEL_COMPARISON
                (MODEL_NAME, MAE, RMSE, MAPE)
            VALUES
                (%s, %s, %s, %s)
        """, (
            "SARIMA",
            float(sarima_result["mae"]),
            float(sarima_result["rmse"]),
            float(sarima_result["mape"]),
        ))

        cursor.execute("""
            INSERT INTO MODEL_COMPARISON
                (MODEL_NAME, MAE, RMSE, MAPE)
            VALUES
                (%s, %s, %s, %s)
        """, (
            "LSTM",
            float(lstm_result["mae"]),
            float(lstm_result["rmse"]),
            float(lstm_result["mape"]),
        ))

        conn.commit()

        print("\nModel metrics written to Snowflake successfully.")

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":

    print("=" * 60)
    print("SNOWFLAKE → SARIMA + LSTM FORECASTING PIPELINE")
    print("=" * 60)

    df = load_forecasting_data()

    print(f"\nSnowflake rows loaded: {len(df)}")
    print(f"Training rows: {len(df.iloc[:10])}")
    print(f"Validation rows: {len(df.iloc[10:])}")

    # --------------------------------------------------
    # SARIMA
    # --------------------------------------------------

    sarima_result = run_sarima_forecast(df)

    print("\nSARIMA Validation Results")
    print("-" * 40)
    print(f"MAE  : {sarima_result['mae']:,.2f}")
    print(f"RMSE : {sarima_result['rmse']:,.2f}")
    print(f"MAPE : {sarima_result['mape']:.2f}%")

    # --------------------------------------------------
    # LSTM
    # --------------------------------------------------

    print("\nTraining TensorFlow LSTM...")

    lstm_result = run_lstm_forecast(df)

    print("\nLSTM Validation Results")
    print("-" * 40)
    print(f"MAE  : {lstm_result['mae']:,.2f}")
    print(f"RMSE : {lstm_result['rmse']:,.2f}")
    print(f"MAPE : {lstm_result['mape']:.2f}%")

    # --------------------------------------------------
    # Model Comparison
    # --------------------------------------------------

    validation = df.iloc[10:].copy()

    validation["SARIMA_PREDICTION"] = sarima_result["predictions"]
    validation["LSTM_PREDICTION"] = lstm_result["predictions"]

    print("\nModel Comparison")
    print("-" * 60)

    comparison = pd.DataFrame({
        "MODEL": ["SARIMA", "LSTM"],
        "MAE": [
            sarima_result["mae"],
            lstm_result["mae"]
        ],
        "RMSE": [
            sarima_result["rmse"],
            lstm_result["rmse"]
        ],
        "MAPE": [
            sarima_result["mape"],
            lstm_result["mape"]
        ]
    })

    print(comparison.to_string(index=False))

    print("\nValidation Predictions")
    print("-" * 60)

    print(
        validation[
            [
                "DATE",
                "REVENUE",
                "SARIMA_PREDICTION",
                "LSTM_PREDICTION"
            ]
        ].to_string(index=False)
    )

    print("\nPipeline completed successfully.")
    write_results_to_snowflake(
        sarima_result,
        lstm_result
    )

    future_dates, sarima_future, lstm_future = generate_future_forecasts(df)

    print("\nFuture Revenue Forecasts")
    print("-" * 60)

    future_forecasts = pd.DataFrame({
        "DATE": future_dates,
        "SARIMA_FORECAST": sarima_future,
        "LSTM_FORECAST": lstm_future
    })

    print(
        future_forecasts.to_string(index=False)
    )

    write_future_forecasts_to_snowflake(
        future_dates,
        sarima_future,
        lstm_future
    )

    print("\nSnowflake forecast write-back completed.")
