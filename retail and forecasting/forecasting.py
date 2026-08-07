import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/cleaned_retail_data.csv")

df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

monthly_sales = (
    df.groupby(df['InvoiceDate'].dt.to_period('M'))['Revenue']
      .sum()
)

monthly_sales.index = monthly_sales.index.to_timestamp()

plt.figure(figsize=(12,6))
plt.plot(monthly_sales)
plt.title("Monthly Revenue Trend")
plt.xlabel("Month")
plt.ylabel("Revenue")
plt.grid(True)
plt.show()

from statsmodels.tsa.arima.model import ARIMA

# Train ARIMA Model
model = ARIMA(monthly_sales, order=(1,1,1))
model_fit = model.fit()

# Forecast next 3 months
forecast = model_fit.forecast(steps=3)

print("\nNext 3 Months Forecast:")
print(forecast)

forecast_index = pd.date_range(
    start=monthly_sales.index[-1] + pd.offsets.MonthBegin(1),
    periods=3,
    freq='MS'
)

plt.figure(figsize=(12,6))
plt.plot(monthly_sales, label='Historical Revenue')
plt.plot(forecast_index, forecast, label='Forecast')
plt.legend()
plt.title("Revenue Forecast")
plt.grid(True)
plt.show()

# Create forecast dataframe
forecast_df = pd.DataFrame({
    'Month': forecast_index,
    'Revenue': forecast.values,
    'Type': 'Forecast'
})

# Historical dataframe
historical_df = pd.DataFrame({
    'Month': monthly_sales.index,
    'Revenue': monthly_sales.values,
    'Type': 'Historical'
})

# Combine both
combined_df = pd.concat([historical_df, forecast_df])

# Save CSV
combined_df.to_csv("data/forecast_dashboard.csv", index=False)

print("Forecast dashboard data saved successfully!")