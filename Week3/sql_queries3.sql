CREATE TABLE customers AS
SELECT DISTINCT
    `Customer ID`,
    `Customer Name`,
    Segment,
    Country,
    City,
    State,
    Region
FROM superstore_raw;


CREATE TABLE orders AS
SELECT DISTINCT
    `Order ID`,
    `Order Date`,
    `Ship Date`,
    `Ship Mode`,
    `Customer ID`,
    Sales,
    Quantity,
    Discount,
    Profit
FROM superstore_raw;


CREATE TABLE products AS
SELECT DISTINCT
    `Product ID`,
    `Product Name`,
    Category,
    `Sub-Category`
FROM superstore_raw;


SELECT * FROM customers
LIMIT 5;


SELECT * FROM orders
LIMIT 5;


SELECT * FROM products
LIMIT 5;



# Q1. Find all orders where sales are greater than the average sales (Subquery)
SELECT *
FROM orders
WHERE Sales > (
    SELECT AVG(Sales)
    FROM orders
);


# Q2. Find the highest sales order for each customer (Subquery)
SELECT *
FROM orders o
WHERE Sales = (
    SELECT MAX(Sales)
    FROM orders
    WHERE `Customer ID` = o.`Customer ID`
);


# Q3. Calculate total sales for each customer (CTE)
WITH customer_sales AS (
    SELECT
        `Customer ID`,
        SUM(Sales) AS total_sales
    FROM orders
    GROUP BY `Customer ID`
)
SELECT *
FROM customer_sales;


# Q4. Find customers whose total sales are above average (CTE + Subquery)
WITH customer_sales AS (
    SELECT
        `Customer ID`,
        SUM(Sales) AS total_sales
    FROM orders
    GROUP BY `Customer ID`
)
SELECT *
FROM customer_sales
WHERE total_sales > (
    SELECT AVG(total_sales)
    FROM customer_sales
);


# Q5. Rank all customers based on total sales (Window Function)
WITH customer_sales AS (
    SELECT
        `Customer ID`,
        SUM(Sales) AS total_sales
    FROM orders
    GROUP BY `Customer ID`
)
SELECT *,
       RANK() OVER (ORDER BY total_sales DESC) AS customer_rank
FROM customer_sales;


# Q6. Assign row numbers to each order within a customer
SELECT *,
       ROW_NUMBER() OVER (
           PARTITION BY `Customer ID`
           ORDER BY Sales DESC
       ) AS row_num
FROM orders;


# Q7. Display top 3 customers based on total sales
WITH customer_sales AS (
    SELECT
        `Customer ID`,
        SUM(Sales) AS total_sales
    FROM orders
    GROUP BY `Customer ID`
)
SELECT *
FROM (
    SELECT *,
           RANK() OVER (ORDER BY total_sales DESC) AS rank_num
    FROM customer_sales
)
WHERE rank_num <= 3;


# Final Combined Query
# Show Customer Name, Total Sales, and Rank
# Using JOIN + CTE + Window Function
WITH customer_sales AS (
    SELECT
        c.`Customer Name`,
        SUM(o.Sales) AS total_sales
    FROM customers c
    JOIN orders o
    ON c.`Customer ID` = o.`Customer ID`
    GROUP BY c.`Customer Name`
)
SELECT
    `Customer Name`,
    total_sales,
    RANK() OVER (ORDER BY total_sales DESC) AS customer_rank
FROM customer_sales;



# Q1. Top 5 customers based on total sales
WITH customer_sales AS (
    SELECT
        c.`Customer Name`,
        SUM(o.Sales) AS total_sales
    FROM customers c
    JOIN orders o
    ON c.`Customer ID` = o.`Customer ID`
    GROUP BY c.`Customer Name`
)
SELECT *
FROM customer_sales
ORDER BY total_sales DESC
LIMIT 5;


# Q2. Bottom 5 customers based on total sales
WITH customer_sales AS (
    SELECT
        c.`Customer Name`,
        SUM(o.Sales) AS total_sales
    FROM customers c
    JOIN orders o
    ON c.`Customer ID` = o.`Customer ID`
    GROUP BY c.`Customer Name`
)
SELECT *
FROM customer_sales
ORDER BY total_sales ASC
LIMIT 5;


# Q3. Customers who made only one order
SELECT
    c.`Customer Name`,
    COUNT(o.`Order ID`) AS total_orders
FROM customers c
JOIN orders o
ON c.`Customer ID` = o.`Customer ID`
GROUP BY c.`Customer Name`
HAVING COUNT(o.`Order ID`) = 1;


# Q4. Customers with above-average sales
WITH customer_sales AS (
    SELECT
        c.`Customer Name`,
        SUM(o.Sales) AS total_sales
    FROM customers c
    JOIN orders o
    ON c.`Customer ID` = o.`Customer ID`
    GROUP BY c.`Customer Name`
)
SELECT *
FROM customer_sales
WHERE total_sales > (
    SELECT AVG(total_sales)
    FROM customer_sales
);


# Q5. Highest order value per customer
SELECT
    c.`Customer Name`,
    MAX(o.Sales) AS highest_order_value
FROM customers c
JOIN orders o
ON c.`Customer ID` = o.`Customer ID`
GROUP BY c.`Customer Name`;