# Medallion-Based Healthcare Analytics & Prediction Platform

## **Real-Time Patient Vitals Monitoring · Early Deterioration Detection**  
## Celebal Excellence Internship 2025 — Data Engineering Track

---

## Project Overview

A full-stack, production-grade data engineering platform designed to continuously monitor patient vital signs and detect early signs of clinical deterioration before they become life-threatening. Built on the **Medallion Architecture** (Bronze → Silver → Gold) using Apache Kafka, PySpark, Delta Lake, Databricks, ADLS, and Azure Data Factory.

### The Problem
In hospitals, patient conditions can deteriorate rapidly. Traditional monitoring systems trigger alerts only **after** critical thresholds are breached — leaving no window for prevention. This platform addresses three core failures:

| Failure | Solution |
|---------|----------|
| Reactive monitoring | ML risk scoring 12h ahead of deterioration |
| Data silos | Unified Medallion lakehouse with all 5 data sources |
| No predictive capability | RandomForest model with AUC-ROC > 0.94 |

---

## Architecture

```
SOURCE SYSTEMS
Bedside monitors · Wearables · EHR systems · Nurse stations
                    ↓
        Apache Kafka (Real-time streaming)
                    ↓
    ┌───────────────────────────────────────┐
    │         BRONZE LAYER                  │
    │  Raw Delta Tables · Full audit trail  │
    │  No transforms · ACID writes          │
    └──────────────┬────────────────────────┘
                   ↓
    ┌───────────────────────────────────────┐
    │         SILVER LAYER                  │
    │  Deduplication · Outlier removal      │
    │  Registry join · EWS scoring          │
    └──────────────┬────────────────────────┘
                   ↓
    ┌───────────────────────────────────────┐
    │          GOLD LAYER                   │
    │  5 Clinical Reports · ML Risk Scores  │
    │  ICU Utilisation · Alert Analytics    │
    └──────────────┬────────────────────────┘
                   ↓
    Clinicians · ICU Teams · Hospital Operations
```

---

## Project Structure

```
medallion-healthcare/
├── data/
│   ├── raw/                   
│   ├── bronze/                 ← Raw Parquet (auto-generated)
│   ├── silver/                 ← Clean Parquet (auto-generated)
│   ├── gold/                   ← Reports Parquet + CSV (auto-generated)
│   └── prepare_datasets.py     ← Generates 5 source datasets from 50 CSVs
│
├── pipeline/
│   ├── bronze_layer.py         ← Raw ingestion (Delta Lake simulation)
│   ├── silver_layer.py         ← Cleaning, enrichment, EWS scoring
│   └── gold_layer.py           ← 5 Gold reports + ML scoring
│
├── ml/
│   ├── train_model.py          ← RandomForest training (AUC-ROC 0.94+)
│   ├── predict.py              ← Real-time patient risk scoring
│   └── model/                  ← Saved model artefacts (auto-generated)
│
├── kafka_simulation/
│   ├── producer.py             ← Simulates Kafka vitals stream
│   └── consumer.py             ← Micro-batch Bronze writer
│
├── dashboard/
│   ├── app.py                  ← Streamlit home page
│   ├── utils.py                ← Shared chart + data helpers
│   └── pages/
│       ├── 1_vitals_summary.py
│       ├── 2_risk_scores.py
│       ├── 3_alert_response.py
│       ├── 4_icu_capacity.py
│       └── 5_high_risk_patients.py
│
├── notebooks/
│   ├── 01_bronze_layer.ipynb
│   ├── 02_silver_layer.ipynb
│   ├── 03_gold_layer.ipynb
│   └── 04_ml_model.ipynb
│
├── orchestration/
│   └── pipeline_runner.py      ← ADF-style end-to-end runner
│
├── tests/
│   ├── test_bronze.py
│   ├── test_silver.py
│   └── test_gold.py
│
├── config/settings.py          ← All paths, thresholds, ML params
└── requirements.txt
```

---

## Setup & Installation

### 1. Clone / create the project folder
```bash
mkdir medallion-healthcare && cd medallion-healthcare
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate          # Linux/Mac
venv\Scripts\activate             # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## Running the Platform

### Option A — Full pipeline in one command 
```bash
python orchestration/pipeline_runner.py
```
This runs all 5 steps: Data Prep → Bronze → Silver → ML Training → Gold.

### Option B — Step by step

```bash
# Step 1: Generate source datasets from the 50 CSVs
python data/prepare_datasets.py

# Step 2: Bronze layer (raw ingestion)
python pipeline/bronze_layer.py

# Step 3: Silver layer (cleaning + enrichment)
python pipeline/silver_layer.py

# Step 4: Train ML model
python ml/train_model.py

# Step 5: Gold layer (5 reports)
python pipeline/gold_layer.py
```

### Step 6: Launch the dashboard
```bash
streamlit run dashboard/app.py
```
Open http://localhost:8501 in your browser.

---

## Machine Learning Model

| Metric | Value |
|--------|-------|
| Algorithm | Random Forest Classifier |
| Target | `deterioration_next_12h` (binary) |
| Features | 18 vitals + 12 engineered features = 30 total |
| AUC-ROC | > 0.94 |
| F1 Score | > 0.72 |
| Class imbalance | Handled via `class_weight="balanced"` |
| Validation | 5-fold stratified cross-validation |

Key features by importance: `sepsis_risk_score`, `lactate`, `spo2_pct`, `shock_index`, `organ_dysfunction`, `respiratory_rate`

---

## Gold Layer Reports

| # | Report | Consumers |
|---|--------|-----------|
| 01 | Hourly Patient Vitals Summary | Clinicians, Ward Nurses |
| 02 | Deterioration Risk Score Report | ICU Teams, Duty Doctors |
| 03 | Alert Response Time Report | Clinical Governance |
| 04 | ICU Capacity Utilisation | Hospital Operations |
| 05 | High-Risk Patient Detection | All Medical Staff |

---

## Running Tests
```bash
pytest tests/ -v
pytest tests/ -v --cov=pipeline --cov-report=term-missing
```

---

## Kafka Simulation Demo
```bash
# Run producer + consumer together
python kafka_simulation/consumer.py --demo --records 2000
```

---

## Technology Stack

| Component | Technology | Role |
|-----------|-----------|------|
| Streaming | Apache Kafka (simulated) | Real-time vitals ingestion |
| Processing | PySpark / pandas | Distributed transformation |
| Storage | Delta Lake / Parquet / ADLS | Lakehouse storage |
| Orchestration | Azure Data Factory (simulated) | Pipeline scheduling |
| ML | scikit-learn RandomForest | Deterioration risk scoring |
| Dashboard | Streamlit + Plotly | Clinical reporting UI |
| Notebooks | Jupyter | Databricks-compatible exploration |

---

## Author 
**Data Engineering Intern — Celebal Excellence Internship 2025**  
