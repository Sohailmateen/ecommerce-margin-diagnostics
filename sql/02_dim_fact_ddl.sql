CREATE SCHEMA IF NOT EXISTS dw;

-- 1. Date Dimension (Essential for Power BI and Time-Series Analytics)
DROP TABLE IF EXISTS dw.dim_date;
CREATE TABLE dw.dim_date AS
SELECT
    datum AS date_key,
    EXTRACT(YEAR FROM datum)::INT AS year,
    EXTRACT(QUARTER FROM datum)::INT AS quarter,
    EXTRACT(MONTH FROM datum)::INT AS month,
    TO_CHAR(datum, 'Month') AS month_name,
    EXTRACT(DAY FROM datum)::INT AS day,
    EXTRACT(DOW FROM datum)::INT AS day_of_week,
    TO_CHAR(datum, 'Day') AS day_name,
    CASE WHEN EXTRACT(DOW FROM datum) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend
FROM generate_series('2016-01-01'::DATE, '2019-12-31'::DATE, '1 day'::INTERVAL) datum;

ALTER TABLE dw.dim_date ADD PRIMARY KEY (date_key);

-- 2. Customer Dimension
DROP TABLE IF EXISTS dw.dim_customers CASCADE;
CREATE TABLE dw.dim_customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_unique_id VARCHAR(50),
    customer_city VARCHAR(100),
    customer_state VARCHAR(10)
);

INSERT INTO dw.dim_customers
SELECT customer_id, customer_unique_id, customer_city, customer_state
FROM staging.customers;

-- 3. Product Dimension
DROP TABLE IF EXISTS dw.dim_products CASCADE;
CREATE TABLE dw.dim_products (
    product_id VARCHAR(50) PRIMARY KEY,
    category_name VARCHAR(100),
    weight_g INT,
    volume_cm3 NUMERIC(10, 2)
);

INSERT INTO dw.dim_products
SELECT
    product_id,
    COALESCE(product_category_name, 'Unknown') AS category_name,
    COALESCE(product_weight_g, 0) AS weight_g,
    ROUND((COALESCE(product_length_cm, 0) * COALESCE(product_height_cm, 0) * COALESCE(product_width_cm, 0))::NUMERIC, 2) AS volume_cm3
FROM staging.products;

-- 4. Order Fact Table with Logistics SLA Calculation
DROP TABLE IF EXISTS dw.fact_orders CASCADE;
CREATE TABLE dw.fact_orders (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) REFERENCES dw.dim_customers(customer_id),
    order_status VARCHAR(30),
    purchase_date DATE REFERENCES dw.dim_date(date_key),
    delivered_date DATE,
    estimated_delivery_date DATE,
    delivery_lead_time_days INT,
    sla_delay_days INT,
    is_delayed BOOLEAN
);

INSERT INTO dw.fact_orders
SELECT
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp::DATE AS purchase_date,
    order_delivered_customer_date::DATE AS delivered_date,
    order_estimated_delivery_date::DATE AS estimated_delivery_date,
    EXTRACT(DAY FROM (order_delivered_customer_date - order_purchase_timestamp))::INT AS delivery_lead_time_days,
    GREATEST(0, EXTRACT(DAY FROM (order_delivered_customer_date - order_estimated_delivery_date))::INT) AS sla_delay_days,
    CASE 
        WHEN order_delivered_customer_date > order_estimated_delivery_date THEN TRUE 
        ELSE FALSE 
    END AS is_delayed
FROM staging.orders
WHERE order_purchase_timestamp IS NOT NULL;

-- 5. Order Items Fact Table (Financial & Margin Focus)
DROP TABLE IF EXISTS dw.fact_order_items CASCADE;
CREATE TABLE dw.fact_order_items (
    order_item_key SERIAL PRIMARY KEY,
    order_id VARCHAR(50) REFERENCES dw.fact_orders(order_id),
    order_item_id INT,
    product_id VARCHAR(50) REFERENCES dw.dim_products(product_id),
    gross_revenue NUMERIC(10, 2),
    freight_revenue NUMERIC(10, 2),
    -- Estimated unit economics (COGS assumed at 60% of item gross value, handling fee $3.50)
    estimated_cogs NUMERIC(10, 2),
    handling_cost NUMERIC(10, 2),
    net_contribution_margin NUMERIC(10, 2)
);

INSERT INTO dw.fact_order_items (
    order_id,
    order_item_id,
    product_id,
    gross_revenue,
    freight_revenue,
    estimated_cogs,
    handling_cost,
    net_contribution_margin
)
SELECT
    order_id,
    order_item_id,
    product_id,
    price AS gross_revenue,
    freight_value AS freight_revenue,
    ROUND((price * 0.60)::NUMERIC, 2) AS estimated_cogs,
    3.50 AS handling_cost,
    ROUND((price - (price * 0.60) - 3.50)::NUMERIC, 2) AS net_contribution_margin
FROM staging.order_items;

CREATE INDEX idx_orders_customer ON dw.fact_orders(customer_id);
CREATE INDEX idx_orders_purchase_date ON dw.fact_orders(purchase_date);
CREATE INDEX idx_items_product ON dw.fact_order_items(product_id);