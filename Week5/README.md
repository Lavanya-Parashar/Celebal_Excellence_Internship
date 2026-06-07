# Week 5 - Apache Spark Data Cleaning and Transformation

## Overview

In this assignment, I learned the basics of Apache Spark and PySpark. I worked with a sample retail dataset generated using the Faker library and performed data cleaning, filtering, transformation, and aggregation operations.

---

## Objectives

* Understand MapReduce and Apache Spark.
* Learn Spark DataFrames and immutability.
* Handle null values and duplicate records.
* Apply filters and transformations.
* Perform grouping and aggregation operations.
* Understand shuffle and wide transformations.

---

## Dataset Information

### Total Records

* 110 Rows

### Total Columns

* 14 Columns

### Columns Used

```text
user_id
transaction_date
region
product_category
sale_amount
city
age
subscription
email
username
price
store_id
raw_timestamp
status
```

### Dataset Features

* Duplicate records added for testing.
* Null values added in email, price, and status columns.
* Empty usernames added for cleaning operations.
* Timestamp column used for schema conversion.

---

## Technologies Used

* Python
* PySpark
* Pandas
* Faker
* Google Colab

---

## Tasks Performed

### Data Cleaning

* Checked null values.
* Filled missing values.
* Removed duplicate records.
* Removed invalid records.

### Data Transformation

* Renamed columns.
* Converted timestamp data type.
* Applied filtering conditions.

### Aggregation

* Calculated average sales.
* Counted records by city.
* Found minimum, maximum, and average prices.
* Calculated total revenue by store.

---

## Key Learnings

* Spark is faster than MapReduce because it uses in-memory processing.
* DataFrames are immutable, so every operation creates a new DataFrame.
* Data cleaning improves data quality and accuracy.
* GroupBy operations can trigger shuffle operations.
* Schema handling is important for correct data processing.

---

## Conclusion

This assignment helped me understand Spark DataFrames, data cleaning techniques, filtering, grouping, and aggregation operations. It also provided practical experience with handling real-world data issues such as null values and duplicate records using PySpark.
