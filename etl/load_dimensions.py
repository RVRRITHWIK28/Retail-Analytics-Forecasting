from sqlalchemy import text
from database.connection import engine

with engine.begin() as conn:

    # ==========================
    # CUSTOMER DIMENSION
    # ==========================
    print("Loading Customers...")

    conn.execute(text("""
        INSERT INTO dim_customer(customer_id)

        SELECT DISTINCT
        "CustomerID"::TEXT

        FROM staging_sales

        WHERE "CustomerID" IS NOT NULL

        ON CONFLICT(customer_id) DO NOTHING;
    """))

    print("✅ Customers Loaded")


    # ==========================
    # PRODUCT DIMENSION
    # ==========================
    print("Loading Products...")

    conn.execute(text("""
        INSERT INTO dim_product(stock_code, description)

        SELECT DISTINCT
        "StockCode",
        "Description"

        FROM staging_sales;
    """))

    print("✅ Products Loaded")


    # ==========================
    # COUNTRY DIMENSION
    # ==========================
    print("Loading Countries...")

    conn.execute(text("""
        INSERT INTO dim_country(country)

        SELECT DISTINCT
        "Country"

        FROM staging_sales

        ON CONFLICT(country) DO NOTHING;
    """))

    print("✅ Countries Loaded")


    # ==========================
    # DATE DIMENSION
    # ==========================
    print("Loading Dates...")

    conn.execute(text("""
        INSERT INTO dim_date
        (
            invoice_date,
            year,
            month,
            day,
            weekday
        )

        SELECT DISTINCT

        "InvoiceDate",

        EXTRACT(YEAR FROM "InvoiceDate"),

        EXTRACT(MONTH FROM "InvoiceDate"),

        EXTRACT(DAY FROM "InvoiceDate"),

        TO_CHAR("InvoiceDate",'Day')

        FROM staging_sales

        ON CONFLICT(invoice_date) DO NOTHING;
    """))

    print("✅ Dates Loaded")

print("\n🎉 All Dimension Tables Loaded Successfully!")