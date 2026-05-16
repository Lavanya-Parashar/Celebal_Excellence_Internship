CREATE TABLE customers (
customer_id INTEGER PRIMARY KEY,
first_name TEXT NOT NULL,
last_name TEXT NOT NULL,
email TEXT UNIQUE NOT NULL,
city TEXT NOT NULL,
state TEXT NOT NULL,
join_date DATE NOT NULL,
is_premium BOOLEAN DEFAULT 0
);
CREATE TABLE products (
product_id INTEGER PRIMARY KEY,
product_name TEXT NOT NULL,
category TEXT NOT NULL,
brand TEXT NOT NULL,
unit_price REAL NOT NULL CHECK (unit_price > 0),
stock_qty INTEGER NOT NULL DEFAULT 0 CHECK (stock_qty >= 0)
);
CREATE TABLE orders (
order_id INTEGER PRIMARY KEY,
customer_id INTEGER NOT NULL,
order_date DATE NOT NULL,
status TEXT NOT NULL DEFAULT 'Pending'
CHECK (status IN ('Pending','Shipped','Delivered','Cancelled')),
total_amount REAL NOT NULL CHECK (total_amount >= 0),
FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
CREATE TABLE order_items (
item_id INTEGER PRIMARY KEY,
order_id INTEGER NOT NULL,
product_id INTEGER NOT NULL,
quantity INTEGER NOT NULL CHECK (quantity > 0),
unit_price REAL NOT NULL CHECK (unit_price > 0),
discount_pct REAL DEFAULT 0 CHECK (discount_pct BETWEEN 0 AND 100),
FOREIGN KEY (order_id) REFERENCES orders(order_id),
FOREIGN KEY (product_id) REFERENCES products(product_id)
);


INSERT INTO customers VALUES 
(101, 'Aarav',  'Sharma', 'aarav.s@email.com',  'Mumbai',    'Maharashtra', '2024-01-15', TRUE), 
(102, 'Priya',  'Patel',  'priya.p@email.com',  'Ahmedabad', 'Gujarat',     '2024-02-20', FALSE), 
(103, 'Rohan',  'Gupta',  'rohan.g@email.com',  'Delhi',     'Delhi',       '2024-03-10', TRUE), 
(104, 'Sneha',  'Reddy',  'sneha.r@email.com',  'Hyderabad', 'Telangana',   '2024-04-05', FALSE), 
(105, 'Vikram', 'Singh',  'vikram.s@email.com', 'Jaipur',    'Rajasthan',   '2024-05-12', TRUE), 
(106, 'Ananya', 'Iyer',   'ananya.i@email.com', 'Chennai',   'Tamil Nadu',  '2024-06-18', FALSE), 
(107, 'Karan',  'Mehta',  'karan.m@email.com',  'Pune',      'Maharashtra', '2024-07-22', TRUE), 
(108, 'Divya',  'Nair',   'divya.n@email.com',  'Kochi',     'Kerala',      '2024-08-30', FALSE); 

-- ========== INSERT: products ========== 
INSERT INTO products VALUES 
(201, 'Wireless Earbuds',     'Electronics', 'BoAt',          1499.00, 250), 
(202, 'Cotton T-Shirt',       'Clothing',    'Levis',         799.00,  500), 
(203, 'Smart Watch',          'Electronics', 'Noise',         2999.00, 150), 
(204, 'Running Shoes',        'Clothing',    'Nike',          4599.00, 120), 
(205, 'Bluetooth Speaker',    'Electronics', 'JBL',           3499.00, 200), 
(206, 'Bedsheet Set',         'Home',        'Spaces',        1299.00, 300), 
(207, 'Laptop Stand',         'Electronics', 'AmazonBasics',  899.00,  180), 
(208, 'Cushion Covers (Set)', 'Home',        'HomeCenter',    599.00,  400); 

-- ========== INSERT: orders ========== 
INSERT INTO orders VALUES 
(1001, 101, '2024-08-01', 'Delivered',  4498.00), 
(1002, 102, '2024-08-03', 'Delivered',  799.00), 
(1003, 103, '2024-08-05', 'Shipped',    7498.00), 
(1004, 101, '2024-08-10', 'Delivered',  3499.00), 
(1005, 104, '2024-08-12', 'Cancelled',  2999.00), 
(1006, 105, '2024-08-15', 'Delivered',  5898.00), 
(1007, 106, '2024-08-18', 'Pending',    1299.00), 
(1008, 103, '2024-08-20', 'Delivered',  899.00), 
(1009, 107, '2024-08-25', 'Shipped',    6098.00), 
(1010, 108, '2024-08-28', 'Delivered',  1598.00); 

-- ========== INSERT: order_items ========== 
INSERT INTO order_items VALUES 
(5001, 1001, 201, 2, 1499.00, 0), 
(5002, 1001, 207, 1, 899.00,  10), 
(5003, 1002, 202, 1, 799.00,  0), 
(5004, 1003, 203, 1, 2999.00, 0), 
(5005, 1003, 204, 1, 4599.00, 5), 
(5006, 1004, 205, 1, 3499.00, 0), 
(5007, 1005, 203, 1, 2999.00, 0), 
(5008, 1006, 201, 1, 1499.00, 10), 
(5009, 1006, 204, 1, 4599.00, 5), 
(5010, 1007, 206, 1, 1299.00, 0), 
(5011, 1008, 207, 1, 899.00,  0), 
(5012, 1009, 205, 1, 3499.00, 0), 
(5013, 1009, 208, 2, 599.00,  15), 
(5014, 1010, 206, 1, 1299.00, 0), 
(5015, 1010, 208, 1, 599.00,  0); 


-- Q1. Display all columns and rows from the customers table
SELECT * FROM customers;

-- Q2. Retrieve first_name, last_name, and city of all customers
SELECT first_name, last_name, city
FROM customers;

-- Q3. List all unique categories available in the products table
SELECT DISTINCT category
FROM products;

-- Q4. Primary Keys in the schema
-- customers    -> customer_id
-- products     -> product_id
-- orders       -> order_id
-- order_items  -> item_id
-- Primary Keys uniquely identify each row and cannot be NULL.

-- Q5. Constraints on email column in customers table
-- email VARCHAR(100) UNIQUE NOT NULL
-- Duplicate email insertion will fail with a UNIQUE constraint error.

-- Q6. Insert a product with negative unit_price (will fail)
INSERT INTO products
VALUES (999, 'Test Product', 'Electronics', 'TestBrand', -50, 10);
-- Error occurs because of CHECK (unit_price > 0)

-- Q7. Retrieve all orders with status = 'Delivered'
SELECT *
FROM orders
WHERE status = 'Delivered';

-- Q8. Products in Electronics category with unit_price > 2000
SELECT *
FROM products
WHERE category = 'Electronics'
  AND unit_price > 2000;

-- Q9. Customers who joined in 2024 and belong to Maharashtra
SELECT *
FROM customers
WHERE join_date BETWEEN '2024-01-01' AND '2024-12-31'
  AND state = 'Maharashtra';

-- Q10. Orders between 2024-08-10 and 2024-08-25 (inclusive) that are not cancelled
SELECT *
FROM orders
WHERE order_date BETWEEN '2024-08-10' AND '2024-08-25'
  AND status <> 'Cancelled';

-- Q11. Example query that benefits from idx_orders_date
SELECT *
FROM orders
WHERE order_date >= '2024-08-01';
-- Index idx_orders_date speeds up filtering on order_date.

-- Q12. Index-friendly (SARGable) query for customers joined in 2024
SELECT *
FROM customers
WHERE join_date BETWEEN '2024-01-01' AND '2024-12-31';

-- Q13. Count total number of orders
SELECT COUNT(*) AS total_orders
FROM orders;

-- Q14. Total revenue from Delivered orders
SELECT SUM(total_amount) AS delivered_revenue
FROM orders
WHERE status = 'Delivered';

-- Q15. Average unit_price of products in each category
SELECT category,
       AVG(unit_price) AS avg_unit_price
FROM products
GROUP BY category;

-- Q16. For each order status, count orders and total revenue
SELECT status,
       COUNT(*) AS order_count,
       SUM(total_amount) AS total_revenue
FROM orders
GROUP BY status
ORDER BY total_revenue DESC;

-- Q17. Most expensive and cheapest product in each category
SELECT category,
       MAX(unit_price) AS max_price,
       MIN(unit_price) AS min_price
FROM products
GROUP BY category;

-- Q18. Categories where average unit_price > 2000
SELECT category,
       AVG(unit_price) AS avg_unit_price
FROM products
GROUP BY category
HAVING AVG(unit_price) > 2000;

-- Q19. INNER JOIN: orders with customer names
SELECT o.order_id,
       o.order_date,
       c.first_name,
       c.last_name,
       o.total_amount
FROM orders o
INNER JOIN customers c
ON o.customer_id = c.customer_id;

-- Q20. LEFT JOIN: all customers and their orders
SELECT c.customer_id,
       c.first_name,
       c.last_name,
       o.order_id,
       o.order_date
FROM customers c
LEFT JOIN orders o
ON c.customer_id = o.customer_id;

-- Q21. JOIN across orders, order_items, and products
SELECT o.order_id,
       p.product_name,
       oi.quantity,
       oi.unit_price,
       oi.discount_pct
FROM orders o
JOIN order_items oi
ON o.order_id = oi.order_id
JOIN products p
ON oi.product_id = p.product_id;

-- Q22. LEFT JOIN vs RIGHT JOIN vs FULL OUTER JOIN
-- LEFT JOIN  : returns all rows from left table and matching rows from right table.
-- RIGHT JOIN : returns all rows from right table and matching rows from left table.
-- FULL OUTER JOIN: returns all rows from both tables, matched where possible.

-- Q23. Foreign Key relationships
-- orders.customer_id      -> customers.customer_id
-- order_items.order_id    -> orders.order_id
-- order_items.product_id  -> products.product_id
-- Inserting an order with customer_id = 999 will fail due to FOREIGN KEY constraint.

-- Q24. CASE statement to classify products into price tiers
SELECT product_name,
       unit_price,
       CASE
           WHEN unit_price < 1000 THEN 'Budget'
           WHEN unit_price BETWEEN 1000 AND 3000 THEN 'Mid-Range'
           ELSE 'Premium'
       END AS price_tier
FROM products;

-- Q25. Count Delivered vs Not Delivered orders in a single row
SELECT
    SUM(CASE WHEN status = 'Delivered' THEN 1 ELSE 0 END) AS delivered_orders,
    SUM(CASE WHEN status <> 'Delivered' THEN 1 ELSE 0 END) AS not_delivered_orders
FROM orders;

-- Q26. ACID Properties
-- Atomicity  : All operations in a transaction succeed or none do.
-- Consistency: Data remains valid before and after the transaction.
-- Isolation  : Concurrent transactions do not interfere with each other.
-- Durability : Committed changes are permanently saved.

-- Q27. Transaction example
BEGIN TRANSACTION;

INSERT INTO orders
VALUES (1011, 102, DATE('now'), 'Pending', 1598.00);

INSERT INTO order_items
VALUES (5016, 1011, 206, 1, 1299.00, 0);

INSERT INTO order_items
VALUES (5017, 1011, 208, 1, 299.00, 0);

UPDATE products
SET stock_qty = stock_qty - 1
WHERE product_id = 206;

UPDATE products
SET stock_qty = stock_qty - 1
WHERE product_id = 208;

COMMIT;

-- If any statement fails, execute:
-- ROLLBACK;