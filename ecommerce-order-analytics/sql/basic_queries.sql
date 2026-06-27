-- Query 1: Total Revenue per Category

SELECT
    p.category,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS total_revenue
FROM order_items oi
JOIN products p
ON oi.product_id = p.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;

-- Query 2: Top 10 Customers by Total Order Value

SELECT
    c.customer_id,
    c.customer_name,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS total_order_value
FROM customers c
JOIN orders o
ON c.customer_id = o.customer_id
JOIN order_items oi
ON o.order_id = oi.order_id
GROUP BY c.customer_id, c.customer_name
ORDER BY total_order_value DESC
LIMIT 10;

-- Query 3: Month-wise Order Count

SELECT
    strftime('%Y-%m', order_date) AS month,
    COUNT(order_id) AS total_orders
FROM orders
GROUP BY month
ORDER BY month DESC
LIMIT 12;