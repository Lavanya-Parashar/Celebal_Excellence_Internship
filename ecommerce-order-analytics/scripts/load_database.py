import sqlite3
import pandas as pd

# Connect to SQLite database
conn = sqlite3.connect("ecommerce.db")

print("Connected to SQLite database.")

# Read cleaned CSV files
customers = pd.read_csv("data/cleaned/customers.csv")
products = pd.read_csv("data/cleaned/products.csv")
orders = pd.read_csv("data/cleaned/orders.csv")
order_items = pd.read_csv("data/cleaned/order_items.csv")

# Load data into SQLite tables
customers.to_sql("customers", conn, if_exists="replace", index=False)
products.to_sql("products", conn, if_exists="replace", index=False)
orders.to_sql("orders", conn, if_exists="replace", index=False)
order_items.to_sql("order_items", conn, if_exists="replace", index=False)

print("All tables loaded successfully!")

# Verify row counts
cursor = conn.cursor()

tables = ["customers", "products", "orders", "order_items"]

print("\nTable Records:")

for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"{table}: {count}")

conn.close()

print("\nDatabase created successfully!")