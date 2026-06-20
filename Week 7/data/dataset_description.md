# Dataset Description

## Overview

For this assignment, both datasets were created directly within the Databricks notebook using PySpark/Python instead of importing external files. The datasets were designed specifically to demonstrate Delta Lake incremental processing and MERGE operations.

## 1. Customer Master Dataset

The Customer Master dataset represents the initial customer records loaded into the Delta table.

### Columns

* customer_id
* name
* city
* email

### Special Cases Included

* Duplicate records were intentionally added to demonstrate duplicate removal.
* Null values were intentionally added to demonstrate data cleaning operations.

### Screenshot

Refer customer_master.png for the sample table 

---

## 2. Customer Incremental Dataset

The Incremental dataset was created to simulate new and updated customer records arriving after the initial load.

### Purpose

* Update existing customer records.
* Insert new customer records.

### Updates Performed

* Customer ID 102 was updated.
* Customer ID 104 was updated.

### New Records Inserted

* Customer ID 107
* Customer ID 108

### Screenshot
Refer customer_incremental.png for the sample table 
---

## Usage in Assignment

The Customer Master dataset was cleaned and stored as a Delta table. The Incremental dataset was then merged into the Delta table using Delta Lake's MERGE operation to perform incremental processing. Validation checks were conducted to verify successful updates, inserts, and removal of duplicate records.

All datasets used in this assignment were generated within the notebook solely for educational and demonstration purposes.
