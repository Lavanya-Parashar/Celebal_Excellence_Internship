# E-Commerce Order Analytics System

## Overview

This project is a mini data analytics pipeline developed using Python and SQLite. It simulates an e-commerce order processing system by generating synthetic datasets, cleaning and validating the data, loading it into a SQLite database, and performing SQL-based business analytics.

## Tech Stack

- Python
- Pandas
- SQLite
- Faker

## Project Structure

```
data/
scripts/
tests/
ecommerce.db
README.md
```

## Features

- Generate realistic e-commerce datasets
- Introduce intentional data quality issues
- Clean and validate datasets
- Load data into SQLite
- Execute 16 SQL business analysis queries
- Generate reports in CSV format
- Command Line Interface (CLI)
- Edge case testing

## Datasets

- customers.csv
- products.csv
- orders.csv
- order_items.csv

## Reports

- Revenue by Category
- Top Customers
- Monthly Orders
- Return Analysis
- Running Revenue
- Customer Segmentation
- Cohort Analysis
- Product Ranking
- Frequently Bought Together

## How to Run

Install dependencies

```bash
py -m pip install pandas faker
```

Generate Data

```bash
py scripts\generate_data.py
```

Clean Data

```bash
py scripts\clean_data.py
```

Load Database

```bash
py scripts\load_database.py
```

Generate Reports

```bash
py scripts\report_generator.py
py scripts\advanced_reports.py
```

Run CLI

```bash
py scripts\cli.py
```

Run Tests

```bash
py tests\test_edge_cases.py
```

## Author

Lavanya Parashar