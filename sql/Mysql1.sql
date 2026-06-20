SELECT COUNT(*)
FROM retail_sales_full;

USE retail_analytics;

SELECT CustomerID,
       ROUND(SUM(Revenue),2) AS TotalRevenue
FROM retail_sales_full
GROUP BY CustomerID
ORDER BY TotalRevenue DESC
LIMIT 10;

SELECT Description,
       ROUND(SUM(Revenue),2) AS TotalRevenue
FROM retail_sales_full
GROUP BY Description
ORDER BY TotalRevenue DESC
LIMIT 10;

SELECT Country,
       ROUND(SUM(Revenue),2) AS Revenue
FROM retail_sales_full
GROUP BY Country
ORDER BY Revenue DESC;

CREATE TABLE DimCustomer AS
SELECT DISTINCT
    CustomerID,
    Country
FROM retail_sales_full;

CREATE TABLE DimProduct AS
SELECT DISTINCT
    StockCode,
    Description
FROM retail_sales_full;

CREATE TABLE DimDate AS
SELECT DISTINCT
    DATE(InvoiceDate) AS DateKey,
    YEAR(InvoiceDate) AS Year,
    MONTH(InvoiceDate) AS Month,
    QUARTER(InvoiceDate) AS Quarter
FROM retail_sales_full;

CREATE TABLE FactSales AS
SELECT
    InvoiceNo,
    CustomerID,
    StockCode,
    DATE(InvoiceDate) AS DateKey,
    Quantity,
    Revenue
FROM retail_sales_full;

SHOW TABLES;
