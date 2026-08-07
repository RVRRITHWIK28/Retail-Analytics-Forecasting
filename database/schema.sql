DROP TABLE IF EXISTS fact_sales CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
DROP TABLE IF EXISTS dim_product CASCADE;
DROP TABLE IF EXISTS dim_country CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;

CREATE TABLE dim_customer(
    customer_key SERIAL PRIMARY KEY,
    customer_id VARCHAR(30) UNIQUE
);

CREATE TABLE dim_product(
    product_key SERIAL PRIMARY KEY,
    stock_code VARCHAR(30),
    description TEXT
);

CREATE TABLE dim_country(
    country_key SERIAL PRIMARY KEY,
    country VARCHAR(100) UNIQUE
);

CREATE TABLE dim_date(
    date_key SERIAL PRIMARY KEY,
    invoice_date TIMESTAMP UNIQUE,
    year INT,
    month INT,
    day INT,
    weekday VARCHAR(20)
);

CREATE TABLE fact_sales(
    sale_key SERIAL PRIMARY KEY,

    invoice_no VARCHAR(30),

    customer_key INT REFERENCES dim_customer(customer_key),

    product_key INT REFERENCES dim_product(product_key),

    country_key INT REFERENCES dim_country(country_key),

    date_key INT REFERENCES dim_date(date_key),

    quantity INT,

    unit_price NUMERIC(10,2),

    revenue NUMERIC(12,2)
);