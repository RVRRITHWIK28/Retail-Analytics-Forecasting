import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
import warnings

def forecast_sales_with_ci(df: pd.DataFrame, steps: int = 3) -> pd.DataFrame:
    """
    Generates revenue forecast for next `steps` months with 80% and 95% confidence intervals.
    """
    if df.empty or "revenue" not in df.columns or len(df) < 4:
        return _fallback_forecast(df, steps)

    data = df.copy()
    data["date"] = pd.to_datetime(
        data["year"].astype(str) + "-" + data["month"].astype(str) + "-01"
    )
    data = data.sort_values("date").drop_duplicates(subset=["date"])
    data = data.set_index("date").resample("MS").asfreq()
    data["revenue"] = data["revenue"].fillna(0)

    series = data["revenue"]

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = ARIMA(series, order=(1, 1, 1))
            model_fit = model.fit()

            forecast_res = model_fit.get_forecast(steps=steps)
            forecast_vals = forecast_res.predicted_mean

            ci_80 = forecast_res.conf_int(alpha=0.20)
            ci_95 = forecast_res.conf_int(alpha=0.05)

            last_date = series.index[-1]
            future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=steps, freq="MS")

            forecast_df = pd.DataFrame({
                "Forecast": np.maximum(0, forecast_vals.values),
                "Lower_80": np.maximum(0, ci_80.iloc[:, 0].values),
                "Upper_80": np.maximum(0, ci_80.iloc[:, 1].values),
                "Lower_95": np.maximum(0, ci_95.iloc[:, 0].values),
                "Upper_95": np.maximum(0, ci_95.iloc[:, 1].values),
            }, index=future_dates)

            forecast_df.index = forecast_df.index.strftime("%b %Y")
            return forecast_df

    except Exception:
        return _fallback_forecast(df, steps)


def _fallback_forecast(df: pd.DataFrame, steps: int) -> pd.DataFrame:
    start_date = pd.Timestamp.now()
    base_val = max(0.0, float(df["revenue"].iloc[-1])) if not df.empty and "revenue" in df.columns and len(df) > 0 else 0.0

    future_dates = pd.date_range(start=start_date, periods=steps, freq="MS")
    forecast_df = pd.DataFrame({
        "Forecast": [base_val] * steps,
        "Lower_80": [base_val * 0.9] * steps,
        "Upper_80": [base_val * 1.1] * steps,
        "Lower_95": [base_val * 0.8] * steps,
        "Upper_95": [base_val * 1.2] * steps,
    }, index=future_dates)
    forecast_df.index = forecast_df.index.strftime("%b %Y")
    return forecast_df


# Backward compatibility alias
forecast_sales = forecast_sales_with_ci