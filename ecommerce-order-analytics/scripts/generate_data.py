import pandas as pd
import random
import os
from faker import Faker
from datetime import datetime, timedelta

# Initialize Faker
fake = Faker("en_IN")

# Create output folder if it doesn't exist
os.makedirs("data/raw", exist_ok=True)

# Number of records
NUM_CUSTOMERS = 500
NUM_PRODUCTS = 500
NUM_ORDERS = 1000
NUM_ORDER_ITEMS = 3000

# Categories and Subcategories
categories = {
    "Electronics": ["Mobile", "Laptop", "TV", "Headphones"],
    "Clothing": ["Shirt", "Jeans", "Jacket", "Shoes"],
    "Home": ["Furniture", "Kitchen", "Decor", "Appliances"],
    "Books": ["Fiction", "Education", "Comics", "Biography"]
}

customer_types = ["REGULAR", "PREMIUM", "VIP"]

order_status = [
    "PLACED",
    "SHIPPED",
    "DELIVERED",
    "CANCELLED",
    "RETURNED"
]

region_codes = ["NORTH", "SOUTH", "EAST", "WEST"]

def generate_customers():
    customers = []

    for i in range(1, NUM_CUSTOMERS + 1):

        customer_id = f"CUST{i:04d}"
        customer_name = fake.name()

        email = fake.email()

        # 2% Invalid Emails
        if random.random() < 0.02:
            email = random.choice([
                customer_name.replace(" ", "").lower() + "gmail.com",
                customer_name.replace(" ", "").lower() + "@",
                customer_name.replace(" ", "").lower() + ".com"
            ])

        registration_date = fake.date_between(
            start_date="-3y",
            end_date="today"
        )

        customer_type = random.choice(customer_types)

        customers.append([
            customer_id,
            customer_name,
            email,
            registration_date,
            customer_type
        ])

    df = pd.DataFrame(
        customers,
        columns=[
            "customer_id",
            "customer_name",
            "email",
            "registration_date",
            "customer_type"
        ]
    )

    df.to_csv("data/raw/customers.csv", index=False)

    print("customers.csv generated")

    return df

def generate_products():
    products = []

    product_words = [
        "Laptop", "Phone", "Headphones", "Camera", "Watch",
        "Chair", "Table", "Book", "Shirt", "Shoes",
        "Mixer", "Bottle", "Keyboard", "Mouse", "Speaker",
        "Printer", "Bag", "Notebook", "Monitor", "Fan"
    ]

    for i in range(1, NUM_PRODUCTS + 1):

        product_id = f"PROD{i:04d}"

        category = random.choice(list(categories.keys()))
        subcategory = random.choice(categories[category])

        product_name = random.choice(product_words) + " " + fake.word().title()

        # Introduce mixed case and extra spaces in ~5% records
        if random.random() < 0.05:

            option = random.choice([1, 2, 3])

            if option == 1:
                product_name = "  " + product_name + "  "

            elif option == 2:
                product_name = product_name.upper()

            else:
                product_name = product_name.swapcase()

        cost_price = round(random.uniform(100, 50000), 2)

        products.append([
            product_id,
            product_name,
            category,
            subcategory,
            cost_price
        ])

    df = pd.DataFrame(
        products,
        columns=[
            "product_id",
            "product_name",
            "category",
            "subcategory",
            "cost_price"
        ]
    )

    df.to_csv("data/raw/products.csv", index=False)

    print("products.csv generated")

    return df

def generate_orders(customers_df):
    orders = []

    customer_ids = customers_df["customer_id"].tolist()

    for i in range(1, NUM_ORDERS + 1):

        order_id = f"ORD{i:05d}"

        # 5% NULL customer_id
        if random.random() < 0.05:
            customer_id = None
        else:
            customer_id = random.choice(customer_ids)

        order_datetime = fake.date_time_between(
            start_date="-1y",
            end_date="now"
        )

        # Wrong date format in ~3% records
        if random.random() < 0.03:
            order_date = order_datetime.strftime("%d-%m-%Y")
        else:
            order_date = order_datetime.strftime("%Y-%m-%d %H:%M:%S")

        status = random.choices(
            order_status,
            weights=[10, 10, 70, 5, 5],
            k=1
        )[0]

        region = random.choice(region_codes)

        orders.append([
            order_id,
            customer_id,
            order_date,
            status,
            region
        ])

    df = pd.DataFrame(
        orders,
        columns=[
            "order_id",
            "customer_id",
            "order_date",
            "status",
            "region_code"
        ]
    )

    df.to_csv("data/raw/orders.csv", index=False)

    print("orders.csv generated")

    return df

def generate_order_items(orders_df, products_df):

    items = []

    order_ids = orders_df["order_id"].tolist()
    product_ids = products_df["product_id"].tolist()

    item_counter = 1

    for _ in range(NUM_ORDER_ITEMS):

        item_id = f"ITEM{item_counter:05d}"

        order_id = random.choice(order_ids)

        product_id = random.choice(product_ids)

        quantity = random.randint(1, 5)

        # 3% negative quantity
        if random.random() < 0.03:
            quantity = -random.randint(1, 3)

        unit_price = round(random.uniform(100, 50000), 2)

        discount = random.randint(0, 100)

        items.append([
            item_id,
            order_id,
            product_id,
            quantity,
            unit_price,
            discount
        ])

        item_counter += 1

    df = pd.DataFrame(
        items,
        columns=[
            "item_id",
            "order_id",
            "product_id",
            "quantity",
            "unit_price",
            "discount_percent"
        ]
    )

    df.to_csv("data/raw/order_items.csv", index=False)

    print("order_items.csv generated")

    return df

if __name__ == "__main__":

    print("Generating Customers...")
    customers = generate_customers()

    print("Generating Products...")
    products = generate_products()

    print("Generating Orders...")
    orders = generate_orders(customers)

    print("Generating Order Items...")
    generate_order_items(orders, products)

    print("\nAll CSV files generated successfully!")