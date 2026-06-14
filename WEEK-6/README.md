# Week 6 - Spark Architecture and Efficient Data Processing

## Overview

This assignment focuses on understanding Apache Spark Architecture and performing efficient data processing using PySpark DataFrames. Various operations such as filtering, transformations, schema handling, file format comparison, and data pipeline creation were performed.

---

## Objectives

* Understand Spark Architecture (Driver, Cluster Manager, Executors).
* Learn Lazy Evaluation and DAG concepts.
* Read and process data using Spark DataFrames.
* Apply filtering and transformation operations.
* Handle schemas and data types.
* Understand performance concepts such as Shuffle and Predicate Pushdown.
* Work with CSV and Parquet file formats.
* Build a simple ETL pipeline using Spark.

---

## Dataset Information

The dataset used in this assignment was generated using the Faker library and contains retail transaction data.

### Dataset Details

* Total Records: 110
* Total Columns: 18
* Contains duplicate records
* Contains null values
* Includes timestamp data for schema conversion

### Main Columns

```text
user_id
transaction_date
region
category
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
product_id
amount
base_price
priority
```

---

## Tasks Performed

### Data Loading

* Loaded CSV file using Spark.
* Enabled header and inferSchema options.

### Data Processing

* Selected required columns.
* Applied filtering conditions.
* Renamed columns.
* Cast data types.
* Added calculated columns.

### Performance Concepts

* Studied Lazy Evaluation.
* Understood DAG and fault tolerance.
* Learned Shuffle operations.
* Explored Predicate Pushdown.

### File Formats

* Compared CSV and Parquet.
* Read and wrote Parquet files.
* Exported processed data as CSV.

---

## Technologies Used

* Python
* PySpark
* Pandas
* Faker
* Google Colab

---

## Key Learnings

* Spark uses distributed computing for faster processing.
* Lazy Evaluation helps optimize execution plans.
* DAG provides fault tolerance.
* Parquet is more efficient than CSV for analytics workloads.
* DataFrames are immutable and create new objects after transformations.
* Using show() is safer than collect() for large datasets.

---

## Conclusion

This assignment provided hands-on experience with Spark Architecture, DataFrame transformations, filtering, schema management, and performance optimization techniques. It demonstrated how Spark efficiently processes large datasets using distributed computing and optimized storage formats.
