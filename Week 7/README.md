# Delta Lake Incremental Processing Assignment

## Objective

To perform incremental data processing using Delta Lake and demonstrate update and insert operations using the MERGE command.

## Dataset

A customer master dataset was created containing customer information such as customer_id, name, city, and email.

An incremental dataset was created to simulate:

* Updates to existing customers
* Insertion of new customers

## Steps Performed

### 1. Data Loading

Loaded the customer master dataset into a Spark DataFrame.

### 2. Data Cleaning

* Removed null values
* Removed duplicate records

### 3. Delta Table Creation

Stored the cleaned dataset as a Delta table.

### 4. Incremental Data Processing

Created a second dataset containing updated and new customer records.

### 5. MERGE Operation

Used Delta Lake MERGE functionality to:

* Update existing customer records
* Insert new customer records

### 6. Validation

Validated the final dataset by:

* Checking row counts
* Ensuring no duplicate customer IDs existed

## Technologies Used

* Databricks
* Apache Spark
* PySpark
* Delta Lake

## Outcome

Successfully implemented incremental data processing using Delta Lake MERGE operation and validated the final dataset.
