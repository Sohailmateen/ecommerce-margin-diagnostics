CREATE SCHEMA IF NOT EXISTS analytics;

-- Cohort Retention & Margin Erosion View
CREATE OR REPLACE VIEW analytics.vw_cohort_margin_analysis AS
WITH customer_first_orders AS (
    SELECT
        c.customer_unique_id,
        MIN(DATE_TRUNC('month', o.purchase_date))::DATE AS cohort_month
    FROM dw.fact_orders o
    JOIN dw.dim_customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
order_aggregates AS (
    SELECT
        o.order_id,
        c.customer_unique_id,
        DATE_TRUNC('month', o.purchase_date)::DATE AS order_month,
        o.is_delayed,
        SUM(i.gross_revenue) AS order_gross_revenue,
        SUM(i.net_contribution_margin) AS order_net_margin
    FROM dw.fact_orders o
    JOIN dw.dim_customers c ON o.customer_id = c.customer_id
    JOIN dw.fact_order_items i ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY o.order_id, c.customer_unique_id, o.purchase_date, o.is_delayed
)
SELECT
    f.cohort_month,
    a.order_month,
    -- Months elapsed between initial cohort date and transaction
    (EXTRACT(YEAR FROM a.order_month) - EXTRACT(YEAR FROM f.cohort_month)) * 12 +
    (EXTRACT(MONTH FROM a.order_month) - EXTRACT(MONTH FROM f.cohort_month)) AS period_month,
    COUNT(DISTINCT a.customer_unique_id) AS active_customers,
    SUM(a.order_gross_revenue) AS total_gross_revenue,
    SUM(a.order_net_margin) AS total_net_margin,
    ROUND((SUM(a.order_net_margin) / NULLIF(SUM(a.order_gross_revenue), 0) * 100), 2) AS margin_percentage,
    ROUND(AVG(CASE WHEN a.is_delayed THEN 1.0 ELSE 0.0 END) * 100, 2) AS delayed_orders_rate
FROM order_aggregates a
JOIN customer_first_orders f ON a.customer_unique_id = f.customer_unique_id
GROUP BY f.cohort_month, a.order_month
ORDER BY f.cohort_month, period_month;


-- Order-Level Diagnostics View for Statistical Inference
CREATE OR REPLACE VIEW analytics.vw_order_diagnostics AS
WITH review_dedup AS (
    SELECT 
        order_id,
        AVG(review_score) AS avg_review_score
    FROM staging.order_reviews
    GROUP BY order_id
),
payment_agg AS (
    SELECT
        order_id,
        SUM(payment_value) AS total_paid,
        MAX(payment_installments) AS max_installments
    FROM staging.order_payments
    GROUP BY order_id
)
SELECT
    o.order_id,
    c.customer_unique_id,
    c.customer_state,
    o.purchase_date,
    o.delivery_lead_time_days,
    o.sla_delay_days,
    o.is_delayed,
    COUNT(i.order_item_id) AS item_count,
    SUM(i.gross_revenue) AS gross_revenue,
    SUM(i.freight_revenue) AS freight_revenue,
    SUM(i.net_contribution_margin) AS net_margin,
    ROUND((SUM(i.net_contribution_margin) / NULLIF(SUM(i.gross_revenue), 0)) * 100, 2) AS margin_pct,
    ROUND((SUM(i.freight_revenue) / NULLIF(SUM(i.gross_revenue), 0)) * 100, 2) AS freight_to_price_ratio,
    r.avg_review_score,
    p.total_paid,
    p.max_installments
FROM dw.fact_orders o
JOIN dw.dim_customers c ON o.customer_id = c.customer_id
JOIN dw.fact_order_items i ON o.order_id = i.order_id
LEFT JOIN review_dedup r ON o.order_id = r.order_id
LEFT JOIN payment_agg p ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
GROUP BY 
    o.order_id, c.customer_unique_id, c.customer_state, 
    o.purchase_date, o.delivery_lead_time_days, o.sla_delay_days, 
    o.is_delayed, r.avg_review_score, p.total_paid, p.max_installments;