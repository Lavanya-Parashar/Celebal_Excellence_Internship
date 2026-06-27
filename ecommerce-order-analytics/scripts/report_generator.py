import sqlite3
import pandas as pd
import os

# Create reports folder
os.makedirs("data/reports", exist_ok=True)

# Connect to SQLite
conn = sqlite3.connect("ecommerce.db")

def execute_query(query, title, filename):

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    df = pd.read_sql_query(query, conn)

    print(df)

    df.to_csv(f"data/reports/{filename}", index=False)

    print(f"\nReport saved as {filename}")

query1 = """
SELECT
    p.category,
    ROUND(SUM(oi.quantity * oi.unit_price *
    (1 - oi.discount_percent/100.0)),2) AS total_revenue
FROM order_items oi
JOIN products p
ON oi.product_id = p.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;
"""

execute_query(
    query1,
    "Query 1 : Revenue Per Category",
    "query1_revenue_per_category.csv"
)

query2 = """
SELECT
    c.customer_id,
    c.customer_name,
    ROUND(SUM(
    oi.quantity*oi.unit_price*
    (1-oi.discount_percent/100.0)
    ),2) AS total_order_value

FROM customers c

JOIN orders o
ON c.customer_id=o.customer_id

JOIN order_items oi
ON o.order_id=oi.order_id

GROUP BY c.customer_id,c.customer_name

ORDER BY total_order_value DESC

LIMIT 10;
"""

execute_query(
    query2,
    "Query 2 : Top 10 Customers",
    "query2_top_customers.csv"
)

query3="""
SELECT

strftime('%Y-%m',order_date) AS month,

COUNT(*) AS total_orders

FROM orders

GROUP BY month

ORDER BY month DESC;

"""

execute_query(

query3,

"Query 3 : Month Wise Orders",

"query3_month_orders.csv"

)

query4="""

SELECT DISTINCT

c.customer_id,

c.customer_name

FROM customers c

JOIN orders o

ON c.customer_id=o.customer_id

WHERE c.customer_id NOT IN(

SELECT customer_id

FROM orders

WHERE status='DELIVERED'

);

"""

execute_query(

query4,

"Query 4 : Never Delivered",

"query4_never_delivered.csv"

)

query5="""

SELECT

p.product_name,

SUM(CASE
WHEN quantity>0
THEN quantity
ELSE 0
END) purchases,

ABS(SUM(CASE
WHEN quantity<0
THEN quantity
ELSE 0
END)) returns

FROM order_items oi

JOIN products p

ON oi.product_id=p.product_id

GROUP BY p.product_name

HAVING returns>purchases;

"""

execute_query(

query5,

"Query 5 : More Returns",

"query5_more_returns.csv"

)

query6="""

SELECT

p.category,

ROUND(

ABS(SUM(

CASE

WHEN quantity<0

THEN quantity

ELSE 0

END

))*100.0/

SUM(ABS(quantity))

,2)

AS return_rate

FROM order_items oi

JOIN products p

ON oi.product_id=p.product_id

GROUP BY p.category;

"""

execute_query(

query6,

"Query 6 : Return Rate",

"query6_return_rate.csv"

)

conn.close()

print("\nAll Reports Generated Successfully.")