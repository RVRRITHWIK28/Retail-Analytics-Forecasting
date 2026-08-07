from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:9440211075%40Rv@localhost:5432/retail_db"

engine = create_engine(DATABASE_URL)

with engine.begin() as conn:

    print("Creating Customer Dimension...")

    conn.execute(text("""
        INSERT INTO dim_customer(customer_id, customer_name, segment)
        SELECT DISTINCT
            CustomerID::TEXT,
            'Unknown',
            'Retail'
        FROM staging_sales
        WHERE CustomerID IS NOT NULL
        ON CONFLICT (customer_id) DO NOTHING;
    """))

    print("✅ Customer Dimension Loaded")

    print("Creating Product Dimension...")

conn.execute(text("""
INSERT INTO dim_product(product_name, category, sub_category)

SELECT DISTINCT
Description,
'General',
'General'

FROM staging_sales;
"""))

print("✅ Product Dimension Loaded")

print("Creating Location Dimension...")

conn.execute(text("""
INSERT INTO dim_location
(country,state,city,region,postal_code)

SELECT DISTINCT
Country,
NULL,
NULL,
NULL,
NULL

FROM staging_sales;
"""))

print("✅ Location Dimension Loaded")

print("Creating Date Dimension...")

conn.execute(text("""
INSERT INTO dim_date
(full_date,day,month,month_name,quarter,year,weekday)

SELECT DISTINCT

DATE(InvoiceDate),

EXTRACT(DAY FROM InvoiceDate),

EXTRACT(MONTH FROM InvoiceDate),

TO_CHAR(InvoiceDate,'Month'),

EXTRACT(QUARTER FROM InvoiceDate),

EXTRACT(YEAR FROM InvoiceDate),

TO_CHAR(InvoiceDate,'Day')

FROM staging_sales

ON CONFLICT(full_date) DO NOTHING;
"""))

print("✅ Date Dimension Loaded")