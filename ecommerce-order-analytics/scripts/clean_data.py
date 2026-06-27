import pandas as pd
import os
from datetime import datetime

# Create output folders
os.makedirs("data/cleaned", exist_ok=True)
os.makedirs("data/reports", exist_ok=True)

report = []

def clean_orders():

    df = pd.read_csv("data/raw/orders.csv")

    # Count NULL customer IDs
    null_customer_count = df["customer_id"].isna().sum()

    # Replace NULL with UNKNOWN
    df["customer_id"] = df["customer_id"].fillna("UNKNOWN")

    wrong_date_count = 0

    cleaned_dates = []

    for date in df["order_date"]:

        try:
            # Correct format
            dt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

        except:

            try:
                # Wrong format -> Convert
                dt = datetime.strptime(date, "%d-%m-%Y")
                wrong_date_count += 1

            except:
                dt = pd.NaT

        cleaned_dates.append(dt)

    df["order_date"] = cleaned_dates

    df.to_csv("data/cleaned/orders.csv", index=False)

    report.append(f"NULL customer IDs fixed : {null_customer_count}")
    report.append(f"Wrong date formats fixed : {wrong_date_count}")

    print("orders cleaned")

    return df

def clean_products():

    df = pd.read_csv("data/raw/products.csv")

    before = df["product_name"].copy()

    df["product_name"] = (
        df["product_name"]
        .str.strip()
        .str.title()
    )

    changes = (before != df["product_name"]).sum()

    df.to_csv("data/cleaned/products.csv", index=False)

    report.append(f"Product names normalized : {changes}")

    print("products cleaned")

    return df

def validate_emails():

    df = pd.read_csv("data/raw/customers.csv")

    invalid = []

    for _, row in df.iterrows():

        email = str(row["email"])

        if (
            "@" not in email
            or "." not in email.split("@")[-1]
        ):
            invalid.append(row["customer_id"])

    df.to_csv("data/cleaned/customers.csv", index=False)

    report.append(f"Invalid emails found : {len(invalid)}")

    print("customers validated")

    return invalid

def check_referential_integrity():

    orders = pd.read_csv("data/cleaned/orders.csv")

    items = pd.read_csv("data/raw/order_items.csv")

    valid_orders = set(orders["order_id"])

    invalid_rows = items[
        ~items["order_id"].isin(valid_orders)
    ]

    items.to_csv(
        "data/cleaned/order_items.csv",
        index=False
    )

    report.append(
        f"Broken order references : {len(invalid_rows)}"
    )

    print("referential integrity checked")

    return invalid_rows

def save_report():

    with open(
        "data/reports/issues_report.txt",
        "w"
    ) as file:

        file.write("DATA CLEANING REPORT\n")
        file.write("=" * 30 + "\n\n")

        for line in report:
            file.write(line + "\n")

    print("Report Generated")

if __name__ == "__main__":

    clean_orders()

    clean_products()

    invalid = validate_emails()

    check_referential_integrity()

    save_report()

    print("\nInvalid Customer IDs")

    print(invalid)