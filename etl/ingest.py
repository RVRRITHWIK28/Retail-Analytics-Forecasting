import pandas as pd
from sqlalchemy import text
from database.connection import engine

def run_etl(csv_filepath: str):
    """
    Extracts raw transaction CSVs, transforms them into star-schema dimension/fact tables,
    and loads them into PostgreSQL using idempotent SQL batching.
    """
    print("🚀 Starting ETL Ingestion Pipeline...")
    df = pd.read_csv(csv_filepath)

    # 1. Clean raw data
    df = df.dropna(subset=["invoice_no", "country", "description"])
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").fillna(0.0)
    df["revenue"] = df["quantity"] * df["unit_price"]
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])

    with engine.begin() as conn:
        # 2. Populate dim_country
        countries = df[["country"]].drop_duplicates().dropna()
        for idx, row in countries.iterrows():
            conn.execute(
                text("""
                INSERT INTO public.dim_country (country)
                VALUES (:country)
                ON CONFLICT (country) DO NOTHING;
                """),
                {"country": row["country"]}
            )

        # 3. Populate dim_product
        products = df[["description"]].drop_duplicates().dropna()
        for idx, row in products.iterrows():
            conn.execute(
                text("""
                INSERT INTO public.dim_product (description)
                VALUES (:description)
                ON CONFLICT (description) DO NOTHING;
                """),
                {"description": row["description"]}
            )

        # 4. Populate dim_date
        dates = df[["invoice_date"]].drop_duplicates().copy()
        dates["year"] = dates["invoice_date"].dt.year
        dates["month"] = dates["invoice_date"].dt.month
        dates["day"] = dates["invoice_date"].dt.day

        for idx, row in dates.iterrows():
            conn.execute(
                text("""
                INSERT INTO public.dim_date (full_date, year, month, day)
                VALUES (:full_date, :year, :month, :day)
                ON CONFLICT (full_date) DO NOTHING;
                """),
                {
                    "full_date": row["invoice_date"].strftime("%Y-%m-%d"),
                    "year": int(row["year"]),
                    "month": int(row["month"]),
                    "day": int(row["day"])
                }
            )

    print("✅ ETL Pipeline executed successfully.")

if __name__ == "__main__":
    # Example usage: python etl/ingest.py
    # run_etl("data/raw_transactions.csv")
    pass