from sqlalchemy import text
from database.connection import engine

with engine.begin() as conn:

    print("Loading Fact Table...")

    conn.execute(text("""

    INSERT INTO fact_sales
    (
        invoice_no,
        customer_key,
        product_key,
        country_key,
        date_key,
        quantity,
        unit_price,
        revenue
    )

    SELECT

        s."InvoiceNo",

        c.customer_key,

        p.product_key,

        co.country_key,

        d.date_key,

        s."Quantity",

        s."UnitPrice",

        s."Revenue"

    FROM staging_sales s

    JOIN dim_customer c
        ON c.customer_id = s."CustomerID"::TEXT

    JOIN dim_product p
        ON p.stock_code = s."StockCode"
       AND p.description = s."Description"

    JOIN dim_country co
        ON co.country = s."Country"

    JOIN dim_date d
        ON d.invoice_date = s."InvoiceDate";

    """))

print("🎉 Fact Table Loaded Successfully!")