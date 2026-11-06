from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "gold"
    / "forecasting_features"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "gold"
    / "tensorflow_forecast"
)

LOOKBACK = 3
EPOCHS = 100
BATCH_SIZE = 2


# ============================================================
# LOAD FORECASTING DATA
# ============================================================

def load_data():

    parquet_files = list(INPUT_FILE.rglob("*.parquet"))

    if not parquet_files:
        raise FileNotFoundError(
            f"No parquet files found in {INPUT_FILE}"
        )

    df = pd.read_parquet(INPUT_FILE)

    df["Date"] = pd.to_datetime(df["Date"])

    df = (
        df[["Date", "Revenue"]]
        .sort_values("Date")
        .reset_index(drop=True)
    )

    return df


# ============================================================
# CREATE SEQUENCES
# ============================================================

def create_sequences(values, lookback):

    X = []
    y = []

    for i in range(len(values) - lookback):

        X.append(values[i:i + lookback])

        y.append(values[i + lookback])

    return np.array(X), np.array(y)


# ============================================================
# BUILD LSTM MODEL
# ============================================================

def build_model():

    model = tf.keras.Sequential([
        tf.keras.layers.Input(
            shape=(LOOKBACK, 1)
        ),

        tf.keras.layers.LSTM(
            32,
            activation="tanh"
        ),

        tf.keras.layers.Dense(16, activation="relu"),

        tf.keras.layers.Dense(1)
    ])

    model.compile(
        optimizer="adam",
        loss="mse",
        metrics=["mae"]
    )

    return model


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("RETAIL ANALYTICS & REVENUE FORECASTING")
    print("TensorFlow LSTM Forecast")
    print("=" * 70)

    print(f"Input : {INPUT_FILE}")
    print(f"Output: {OUTPUT_DIR}")

    df = load_data()

    print(f"\nInput Rows: {len(df)}")

    print("\nREVENUE TIME SERIES")
    print("-" * 70)

    print(df.to_string(index=False))

    # --------------------------------------------------------
    # IMPORTANT DATA LIMITATION
    # --------------------------------------------------------

    if len(df) <= LOOKBACK + 3:

        print("\n" + "=" * 70)
        print("IMPORTANT MODEL LIMITATION")
        print("=" * 70)

        print(
            f"Only {len(df)} monthly observations are available."
        )

        print(
            "There are not enough observations to train and "
            "validate an LSTM reliably."
        )

        print(
            "\nThe TensorFlow model architecture will therefore "
            "be validated for pipeline integration only."
        )

        print(
            "\nA production LSTM requires a substantially larger "
            "historical time series."
        )

        return

    # --------------------------------------------------------
    # SCALE REVENUE
    # --------------------------------------------------------

    values = df["Revenue"].values.reshape(-1, 1)

    scaler = MinMaxScaler()

    scaled_values = scaler.fit_transform(values)

    # --------------------------------------------------------
    # CREATE SEQUENCES
    # --------------------------------------------------------

    X, y = create_sequences(
        scaled_values,
        LOOKBACK
    )

    X = X.reshape(
        X.shape[0],
        X.shape[1],
        1
    )

    print("\nSEQUENCE INFORMATION")
    print("-" * 70)

    print(f"Lookback : {LOOKBACK}")
    print(f"Sequences: {len(X)}")

    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    model = build_model()

    print("\nMODEL")
    print("-" * 70)

    model.summary()

    # --------------------------------------------------------
    # TRAIN
    # --------------------------------------------------------

    print("\nTRAINING LSTM...")
    print("-" * 70)

    history = model.fit(
        X,
        y,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        verbose=1
    )

    # --------------------------------------------------------
    # IN-SAMPLE PREDICTION
    # --------------------------------------------------------

    predictions_scaled = model.predict(
        X,
        verbose=0
    )

    predictions = scaler.inverse_transform(
        predictions_scaled
    ).flatten()

    actual = scaler.inverse_transform(
        y.reshape(-1, 1)
    ).flatten()

    mae = np.mean(
        np.abs(actual - predictions)
    )

    rmse = np.sqrt(
        np.mean(
            (actual - predictions) ** 2
        )
    )

    mape = np.mean(
        np.abs(
            (actual - predictions)
            / actual
        )
    ) * 100

    print("\nMODEL METRICS")
    print("-" * 70)

    print(f"MAE  : {mae:,.2f}")
    print(f"RMSE : {rmse:,.2f}")
    print(f"MAPE : {mape:.2f}%")

    # --------------------------------------------------------
    # SAVE MODEL
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    model_path = (
        OUTPUT_DIR
        / "lstm_revenue_model.keras"
    )

    model.save(model_path)

    print(
        f"\nModel saved successfully:\n{model_path}"
    )

    print("\n" + "=" * 70)
    print("TENSORFLOW LSTM COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
