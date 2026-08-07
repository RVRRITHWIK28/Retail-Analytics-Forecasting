import pandas as pd

df = pd.read_excel("data/Online Retail.xlsx")

print(df.head())
print(df.shape)
print(df.columns)
print(df.dtypes)

print("\nMissing Values:")
print(df.isnull().sum())

print("\nDuplicate Rows:")
print(df.duplicated().sum())

print("\nNegative Quantity Records:")
print((df['Quantity'] < 0).sum())

print("\nZero or Negative Price Records:")
print((df['UnitPrice'] <= 0).sum())

# Create a copy
df_clean = df.copy()

# Remove missing CustomerID
df_clean = df_clean.dropna(subset=['CustomerID'])

# Remove duplicates
df_clean = df_clean.drop_duplicates()

# Remove returns
df_clean = df_clean[df_clean['Quantity'] > 0]

# Remove invalid prices
df_clean = df_clean[df_clean['UnitPrice'] > 0]

print("\nCleaned Dataset Shape:")
print(df_clean.shape)

# Revenue Column

df_clean['Revenue'] = df_clean['Quantity'] * df_clean['UnitPrice']

print("\nRevenue Statistics:")
print(df_clean['Revenue'].describe())

print("\nTotal Revenue:")
print(round(df_clean['Revenue'].sum(), 2))

print("\nUnique Customers:")
print(df_clean['CustomerID'].nunique())

print("\nUnique Products:")
print(df_clean['StockCode'].nunique())

print("\nUnique Countries:")
print(df_clean['Country'].nunique())

print("\nTop 10 Products By Revenue:")

top_products = (
    df_clean.groupby('Description')['Revenue']
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

print(top_products)

print("\nTop 10 Countries By Revenue:")

top_countries = (
    df_clean.groupby('Country')['Revenue']
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

print(top_countries)

df_clean['Month'] = df_clean['InvoiceDate'].dt.to_period('M')

monthly_sales = (
    df_clean.groupby('Month')['Revenue']
    .sum()
)

print("\nMonthly Revenue Trend:")
print(monthly_sales)

import matplotlib.pyplot as plt

top_products = (
    df_clean.groupby('Description')['Revenue']
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

plt.figure(figsize=(12,6))
top_products.plot(kind='bar')
plt.title("Top 10 Products by Revenue")
plt.ylabel("Revenue")
plt.tight_layout()
plt.show()

plt.figure(figsize=(12,6))
monthly_sales.plot()
plt.title("Monthly Revenue Trend")
plt.ylabel("Revenue")
plt.xlabel("Month")
plt.grid(True)
plt.tight_layout()
plt.show()

df_clean.to_csv("data/cleaned_retail_data.csv", index=False)

print("Cleaned dataset saved successfully!")

