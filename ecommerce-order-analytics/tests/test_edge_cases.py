import pandas as pd

passed = 0
failed = 0


def print_result(test_name, condition):
    global passed, failed

    if condition:
        print(f"✅ {test_name:<40} PASS")
        passed += 1
    else:
        print(f"❌ {test_name:<40} FAIL")
        failed += 1


# Load datasets
orders = pd.read_csv("data/cleaned/orders.csv")
order_items = pd.read_csv("data/cleaned/order_items.csv")
customers = pd.read_csv("data/cleaned/customers.csv")
products = pd.read_csv("data/cleaned/products.csv")


# -------------------------
# Test 1
# -------------------------
invalid_orders = order_items[
    ~order_items["order_id"].isin(orders["order_id"])
]
print_result(
    "Order ID Referential Integrity",
    len(invalid_orders) == 0
)


# -------------------------
# Test 2
# -------------------------
invalid_products = order_items[
    ~order_items["product_id"].isin(products["product_id"])
]
print_result(
    "Product ID Referential Integrity",
    len(invalid_products) == 0
)


# -------------------------
# Test 3
# -------------------------
discount_high = order_items[
    order_items["discount_percent"] > 100
]
print_result(
    "Discount <=100 Validation",
    len(discount_high) == 0
)


# -------------------------
# Test 4
# -------------------------
discount_low = order_items[
    order_items["discount_percent"] < 0
]
print_result(
    "Discount >=0 Validation",
    len(discount_low) == 0
)


# -------------------------
# Test 5
# -------------------------
zero_quantity = order_items[
    order_items["quantity"] == 0
]
print_result(
    "Zero Quantity Check",
    len(zero_quantity) == 0
)


# -------------------------
# Test 6
# -------------------------
future_orders = pd.to_datetime(
    orders["order_date"]
) > pd.Timestamp.today()

print_result(
    "Future Order Date Check",
    future_orders.sum() == 0
)


# -------------------------
# Test 7
# -------------------------
null_customer = orders[
    orders["customer_id"].isna()
]

print_result(
    "NULL Customer IDs Cleaned",
    len(null_customer) == 0
)


# -------------------------
# Test 8
# -------------------------
invalid_email = customers[
    ~customers["email"].str.contains(
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
        regex=True
    )
]

print_result(
    "Email Format Validation",
    len(invalid_email) <= 20
)


# -------------------------
# Test 9
# -------------------------
normalized_names = (
    products["product_name"]
    ==
    products["product_name"]
    .str.strip()
    .str.title()
).all()

print_result(
    "Product Name Normalization",
    normalized_names
)


# -------------------------
# Test 10
# -------------------------
duplicate_orders = orders[
    "order_id"
].duplicated().sum()

print_result(
    "Duplicate Order IDs",
    duplicate_orders == 0
)


# -------------------------
# Test 11
# -------------------------
duplicate_products = products[
    "product_id"
].duplicated().sum()

print_result(
    "Duplicate Product IDs",
    duplicate_products == 0
)


# -------------------------
# Test 12
# -------------------------
valid_status = orders["status"].isin([
    "PLACED",
    "SHIPPED",
    "DELIVERED",
    "RETURNED",
    "CANCELLED"
]).all()

print_result(
    "Valid Order Status Values",
    valid_status
)


print("\n" + "=" * 60)
print("EDGE CASE TEST SUMMARY")
print("=" * 60)

print(f"Tests Passed : {passed}/12")
print(f"Tests Failed : {failed}/12")

if failed == 0:
    print("\n OVERALL RESULT : PASS")
else:
    print("\n OVERALL RESULT : FAIL")

print("=" * 60)