from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.preprocessing import MinMaxScaler
from statsmodels.tsa.statespace.sarimax import SARIMAX


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "gold"
    / "forecasting_features"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "gold"
    / "model_comparison"
)

LOOKBACK = 3


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    df = pd.read_parquet(INPUT_PATH)

    df["Date"] = pd.to_datetime(df["Date"])

    df = (
        df[["Date", "Revenue"]]
        .sort_values("Date")
        .reset_index(drop=True)
    )

    return df


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(actual, predicted):

    actual = np.asarray(actual)
    predicted = np.asarray(predicted)

    mae = np.mean(
        np.abs(actual - predicted)
    )

    rmse = np.sqrt(
        np.mean((actual - predicted) ** 2)
    )

    mape = np.mean(
        np.abs(
            (actual - predicted) / actual
        )
    ) * 100

    return mae, rmse, mape


# ============================================================
# LSTM SEQUENCE CREATION
# ============================================================

def create_sequences(values, lookback):

    X = []
    y = []

    for i in range(len(values) - lookback):

        X.append(
            values[i:i + lookback]
        )

        y.append(
            values[i + lookback]
        )

    return np.array(X), np.array(y)


# ============================================================
# BUILD LSTM
# ============================================================

def build_lstm():

    model = tf.keras.Sequential([
        tf.keras.layers.Input(
            shape=(LOOKBACK, 1)
        ),

        tf.keras.layers.LSTM(
            32,
            activation="tanh"
        ),

        tf.keras.layers.Dense(
            16,
            activation="relu"
        ),

        tf.keras.layers.Dense(1)
    ])

    model.compile(
        optimizer="adam",
        loss="mse"
    )

    return model


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("SARIMA vs TENSORFLOW LSTM")
    print("FAIR VALIDATION COMPARISON")
    print("=" * 70)

    df = load_data()

    print(f"\nTotal observations: {len(df)}")

    # --------------------------------------------------------
    # TRAIN / VALIDATION SPLIT
    # --------------------------------------------------------

    train_size = 10

    train = df.iloc[:train_size].copy()
    validation = df.iloc[train_size:].copy()

    print("\nTRAINING PERIOD")
    print("-" * 70)

    print(
        f"{train['Date'].iloc[0].date()} "
        f"→ "
        f"{train['Date'].iloc[-1].date()}"
    )

    print(f"Rows: {len(train)}")

    print("\nVALIDATION PERIOD")
    print("-" * 70)

    print(
        f"{validation['Date'].iloc[0].date()} "
        f"→ "
        f"{validation['Date'].iloc[-1].date()}"
    )

    print(f"Rows: {len(validation)}")

    # ========================================================
    # SARIMA
    # ========================================================

    print("\n" + "=" * 70)
    print("SARIMA VALIDATION")
    print("=" * 70)

    sarima_model = SARIMAX(
        train["Revenue"],
        order=(1, 1, 1),
        seasonal_order=(0, 0, 0, 0),
        enforce_stationarity=False,
        enforce_invertibility=False
    )

    sarima_fit = sarima_model.fit(
        disp=False
    )

    sarima_predictions = sarima_fit.forecast(
        steps=len(validation)
    )

    sarima_mae, sarima_rmse, sarima_mape = calculate_metrics(
        validation["Revenue"].values,
        sarima_predictions.values
    )

    print(f"MAE  : {sarima_mae:,.2f}")
    print(f"RMSE : {sarima_rmse:,.2f}")
    print(f"MAPE : {sarima_mape:.2f}%")

    # ========================================================
    # LSTM
    # ========================================================

    print("\n" + "=" * 70)
    print("TENSORFLOW LSTM VALIDATION")
    print("=" * 70)

    # --------------------------------------------------------
    # IMPORTANT:
    # Fit scaler ONLY on training data.
    # --------------------------------------------------------

    scaler = MinMaxScaler()

    train_values = train["Revenue"].values.reshape(-1, 1)

    scaler.fit(train_values)

    train_scaled = scaler.transform(
        train_values
    )

    # --------------------------------------------------------
    # Create training sequences
    # --------------------------------------------------------

    X_train, y_train = create_sequences(
        train_scaled,
        LOOKBACK
    )

    X_train = X_train.reshape(
        X_train.shape[0],
        X_train.shape[1],
        1
    )

    # --------------------------------------------------------
    # Build model
    # --------------------------------------------------------

    tf.keras.utils.set_random_seed(42)

    lstm_model = build_lstm()

    print(
        f"Training sequences: {len(X_train)}"
    )

    # --------------------------------------------------------
    # Train
    # --------------------------------------------------------

    lstm_model.fit(
        X_train,
        y_train,
        epochs=100,
        batch_size=2,
        verbose=0
    )

    # --------------------------------------------------------
    # Recursive validation forecasting
    # --------------------------------------------------------

    history = train_scaled.flatten().tolist()

    predictions_scaled = []

    for _ in range(len(validation)):

        sequence = np.array(
            history[-LOOKBACK:]
        ).reshape(
            1,
            LOOKBACK,
            1
        )

        prediction = lstm_model.predict(
            sequence,
            verbose=0
        )[0][0]

        predictions_scaled.append(
            prediction
        )

        # Feed prediction back into history
        history.append(
            prediction
        )

    lstm_predictions = scaler.inverse_transform(
        np.array(predictions_scaled).reshape(-1, 1)
    ).flatten()

    lstm_mae, lstm_rmse, lstm_mape = calculate_metrics(
        validation["Revenue"].values,
        lstm_predictions
    )

    print(f"MAE  : {lstm_mae:,.2f}")
    print(f"RMSE : {lstm_rmse:,.2f}")
    print(f"MAPE : {lstm_mape:.2f}%")

    # ========================================================
    # COMPARISON TABLE
    # ========================================================

    comparison = pd.DataFrame({
        "Model": [
            "SARIMA",
            "TensorFlow LSTM"
        ],

        "MAE": [
            sarima_mae,
            lstm_mae
        ],

        "RMSE": [
            sarima_rmse,
            lstm_rmse
        ],

        "MAPE": [
            sarima_mape,
            lstm_mape
        ]
    })

    print("\n" + "=" * 70)
    print("MODEL COMPARISON")
    print("=" * 70)

    print(
        comparison.to_string(
            index=False,
            formatters={
                "MAE": "{:,.2f}".format,
                "RMSE": "{:,.2f}".format,
                "MAPE": "{:.2f}%".format
            }
        )
    )

    # ========================================================
    # PREDICTION DETAILS
    # ========================================================

    predictions_df = pd.DataFrame({
        "Date": validation["Date"],

        "ActualRevenue":
            validation["Revenue"].values,

        "SARIMA":
            sarima_predictions.values,

        "LSTM":
            lstm_predictions
    })

    print("\nVALIDATION PREDICTIONS")
    print("-" * 70)

    print(
        predictions_df.to_string(
            index=False
        )
    )

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    OUTPUT_PATH.mkdir(
        parents=True,
        exist_ok=True
    )

    comparison.to_csv(
        OUTPUT_PATH / "model_comparison.csv",
        index=False
    )

    predictions_df.to_csv(
        OUTPUT_PATH / "validation_predictions.csv",
        index=False
    )

    # Save Parquet outputs for Spark / Snowflake / Power BI
    comparison.to_parquet(
        OUTPUT_PATH / "model_comparison.parquet",
        index=False
    )

    predictions_df.to_parquet(
        OUTPUT_PATH / "validation_predictions.parquet",
        index=False
    )


    print("\nResults saved:")
    print(
        OUTPUT_PATH
        / "model_comparison.csv"
    )

    print(
        OUTPUT_PATH
        / "validation_predictions.csv"
    )

    print(
        OUTPUT_PATH
        / "model_comparison.parquet"
    )

    print(
        OUTPUT_PATH
        / "validation_predictions.parquet"
    )

    # ========================================================
    # LIMITATION
    # ========================================================

    print("\n" + "=" * 70)
    print("IMPORTANT DATA LIMITATION")
    print("=" * 70)

    print(
        "Only 13 monthly observations are available."
    )

    print(
        "Therefore, this comparison demonstrates "
        "the evaluation pipeline but is not sufficient "
        "for production model selection."
    )

    print("=" * 70)
    print("MODEL COMPARISON COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
