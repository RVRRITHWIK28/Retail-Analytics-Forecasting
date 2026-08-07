import pandas as pd
from sqlalchemy import create_engine

# -----------------------------
# Database Configuration
# -----------------------------
DATABASE_URL = "postgresql://postgres:9440211075%40Rv@localhost:5432/retail_db"

engine = create_engine(DATABASE_URL)

# -----------------------------
# Load Cleaned Dataset
# -----------------------------
df = pd.read_csv("data/raw/superstore.csv")

# Convert InvoiceDate to datetime
df["InvoiceDate"] = pd.to_datetime(
    df["InvoiceDate"],
    dayfirst=True,
    errors="coerce"
)

# Remove invalid rows
df = df.dropna(subset=["InvoiceDate"])

# -----------------------------
# Load into PostgreSQL
# -----------------------------
df.to_sql(
    "staging_sales",
    con=engine,
    if_exists="replace",
    index=False
)

print(f"✅ {len(df)} rows loaded into staging_sales")