-- Query 4

SELECT DISTINCT
    c.customer_id,
    c.customer_name
FROM customers c
JOIN orders o
ON c.customer_id = o.customer_id
WHERE c.customer_id NOT IN (
    SELECT customer_id
    FROM orders
    WHERE status = 'DELIVERED'
);

-- Query 5

SELECT
    p.product_name,
    SUM(CASE WHEN oi.quantity > 0 THEN oi.quantity ELSE 0 END) AS purchased,
    ABS(SUM(CASE WHEN oi.quantity < 0 THEN oi.quantity ELSE 0 END)) AS returned
FROM order_items oi
JOIN products p
ON oi.product_id = p.product_id
GROUP BY p.product_name
HAVING returned > purchased;

-- Query 6

SELECT
    p.category,
    ROUND(
        ABS(SUM(CASE WHEN oi.quantity < 0 THEN oi.quantity ELSE 0 END))
        *100.0/
        SUM(ABS(oi.quantity))
    ,2) AS return_rate
FROM order_items oi
JOIN products p
ON oi.product_id = p.product_id
GROUP BY p.category;

