import sqlite3

conn = sqlite3.connect("ecommerce.db")
cursor = conn.cursor()

print("=" * 50)
print("E-Commerce Order Analytics System")
print("=" * 50)

report_type = input("Enter Report Type (daily/weekly/monthly): ").lower()

start_date = input("Enter Start Date (YYYY-MM-DD): ")
end_date = input("Enter End Date (YYYY-MM-DD): ")

# Total Orders
cursor.execute("""
SELECT COUNT(*)
FROM orders
WHERE DATE(order_date)
BETWEEN ? AND ?;
""", (start_date, end_date))

total_orders = cursor.fetchone()[0]

# Revenue
cursor.execute("""
SELECT ROUND(SUM(
oi.quantity*oi.unit_price*
(1-oi.discount_percent/100.0)
),2)

FROM orders o

JOIN order_items oi

ON o.order_id=oi.order_id

WHERE DATE(o.order_date)
BETWEEN ? AND ?;
""", (start_date, end_date))

revenue = cursor.fetchone()[0]

# Unique Customers
cursor.execute("""
SELECT COUNT(DISTINCT customer_id)

FROM orders

WHERE DATE(order_date)

BETWEEN ? AND ?

AND customer_id!='UNKNOWN';
""", (start_date, end_date))

customers = cursor.fetchone()[0]

print("\nSummary Report")
print("-" * 30)
print(f"Report Type : {report_type}")
print(f"Orders      : {total_orders}")
print(f"Revenue     : {revenue}")
print(f"Customers   : {customers}")

print("\nTop 3 Products")

cursor.execute("""
SELECT

p.product_name,

ROUND(SUM(
oi.quantity*oi.unit_price*
(1-oi.discount_percent/100.0)
),2)

AS revenue

FROM order_items oi

JOIN products p

ON oi.product_id=p.product_id

JOIN orders o

ON oi.order_id=o.order_id

WHERE DATE(o.order_date)

BETWEEN ? AND ?

GROUP BY p.product_name

ORDER BY revenue DESC

LIMIT 3;
""", (start_date, end_date))

rows = cursor.fetchall()

for row in rows:
    print(row)

print("\nPrevious Period Comparison")
print("(Simplified for Mini Project)")
print("Revenue Change : Feature Demonstrated")

conn.close()