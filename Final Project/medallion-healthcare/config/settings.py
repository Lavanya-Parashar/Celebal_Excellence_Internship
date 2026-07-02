"""
Central configuration for the Medallion Healthcare Analytics Platform.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Data paths ──────────────────────────────────────────────────────────────
RAW_DATA_DIR      = os.path.join(BASE_DIR, "data", "raw")
BRONZE_DIR        = os.path.join(BASE_DIR, "data", "bronze")
SILVER_DIR        = os.path.join(BASE_DIR, "data", "silver")
GOLD_DIR          = os.path.join(BASE_DIR, "data", "gold")
REPORTS_DIR       = os.path.join(BASE_DIR, "reports")
MODEL_DIR         = os.path.join(BASE_DIR, "ml", "model")

# ── Source CSV files (50 patient files, index 0–49) ─────────────────────────
SOURCE_CSV_PATTERN = os.path.join(RAW_DATA_DIR, "hospital_deterioration_ml_ready_{idx}.csv")
NUM_SOURCE_FILES   = 50

# ── Bronze layer settings ────────────────────────────────────────────────────
BRONZE_VITALS_PATH   = os.path.join(BRONZE_DIR, "vitals_raw.parquet")
BRONZE_REGISTRY_PATH = os.path.join(BRONZE_DIR, "patient_registry.parquet")

# ── Silver layer settings ────────────────────────────────────────────────────
SILVER_VITALS_PATH   = os.path.join(SILVER_DIR, "vitals_clean.parquet")

# ── Gold layer output paths ──────────────────────────────────────────────────
GOLD_VITALS_SUMMARY_PATH   = os.path.join(GOLD_DIR, "hourly_vitals_summary.parquet")
GOLD_RISK_SCORES_PATH      = os.path.join(GOLD_DIR, "deterioration_risk_scores.parquet")
GOLD_ALERT_RESPONSE_PATH   = os.path.join(GOLD_DIR, "alert_response_times.parquet")
GOLD_ICU_CAPACITY_PATH     = os.path.join(GOLD_DIR, "icu_capacity.parquet")
GOLD_HIGH_RISK_PATH        = os.path.join(GOLD_DIR, "high_risk_patients.parquet")

# ── ML model settings ────────────────────────────────────────────────────────
MODEL_PATH         = os.path.join(MODEL_DIR, "deterioration_rf_model.joblib")
SCALER_PATH        = os.path.join(MODEL_DIR, "feature_scaler.joblib")
RISK_THRESHOLD     = 0.40   # Probability above which patient is flagged high-risk

# ── Clinical thresholds (used for Silver-layer flagging) ────────────────────
VITAL_THRESHOLDS = {
    "heart_rate":        {"low": 40,  "high": 150},
    "spo2_pct":          {"low": 85,  "high": 100},
    "respiratory_rate":  {"low": 8,   "high": 30},
    "systolic_bp":       {"low": 80,  "high": 180},
    "temperature_c":     {"low": 35.0,"high": 40.0},
}

# ── Feature columns used for ML training ────────────────────────────────────
ML_FEATURES = [
    "heart_rate", "respiratory_rate", "spo2_pct", "temperature_c",
    "systolic_bp", "diastolic_bp", "oxygen_flow", "mobility_score",
    "nurse_alert", "wbc_count", "lactate", "creatinine", "crp_level",
    "hemoglobin", "sepsis_risk_score", "age", "comorbidity_index",
    "hour_from_admission",
]
ML_TARGET = "deterioration_next_12h"

# ── Kafka simulation settings ────────────────────────────────────────────────
KAFKA_TOPIC       = "patient_vitals"
KAFKA_BROKER      = "localhost:9092"
KAFKA_STREAM_DELAY = 0.05   # seconds between records (simulation speed)

# ── Streamlit dashboard settings ────────────────────────────────────────────
DASHBOARD_TITLE   = "Medallion Healthcare Analytics Platform"
DASHBOARD_ICON    = "🏥"
AUTO_REFRESH_SEC  = 30

# ── Reporting ────────────────────────────────────────────────────────────────
REPORT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
