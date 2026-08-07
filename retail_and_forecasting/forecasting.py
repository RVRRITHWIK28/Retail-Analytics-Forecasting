import pandas as pd
from statsmodels.tsa.arima.model import ARIMA


def forecast_sales(df):

    # Convert month column to datetime
    df["month"] = pd.to_datetime(
        df["year"].astype(str) + "-" + df["month"].astype(str)
    )

    df = df.sort_values("month")

    df.set_index("month", inplace=True)

    # Build ARIMA Model
    model = ARIMA(df["revenue"], order=(1, 1, 1))

    model_fit = model.fit()

    # Predict next 3 months
    forecast = model_fit.forecast(steps=3)

    forecast_df = pd.DataFrame({
        "Forecast": forecast
    })

    return forecast_df