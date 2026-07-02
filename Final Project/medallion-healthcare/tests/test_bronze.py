"""
Tests — Bronze Layer
Run with: pytest tests/test_bronze.py -v
"""
import os, sys, pytest, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import BRONZE_VITALS_PATH, BRONZE_REGISTRY_PATH, BRONZE_DIR


def test_bronze_vitals_exists():
    assert os.path.exists(BRONZE_VITALS_PATH), "Bronze vitals Parquet not found"

def test_bronze_vitals_not_empty():
    df = pd.read_parquet(BRONZE_VITALS_PATH)
    assert len(df) > 0, "Bronze vitals is empty"

def test_bronze_vitals_required_columns():
    df = pd.read_parquet(BRONZE_VITALS_PATH)
    required = ["patient_id", "heart_rate", "spo2_pct", "timestamp",
                "_bronze_ingest_ts", "_bronze_layer"]
    for col in required:
        assert col in df.columns, f"Missing column: {col}"

def test_bronze_audit_columns_populated():
    df = pd.read_parquet(BRONZE_VITALS_PATH)
    assert df["_bronze_layer"].eq("BRONZE").all(), "Audit column _bronze_layer incorrect"
    assert df["_bronze_ingest_ts"].notna().all(), "Some ingest timestamps are null"

def test_bronze_registry_exists():
    assert os.path.exists(BRONZE_REGISTRY_PATH), "Bronze registry Parquet not found"

def test_bronze_registry_patient_ids():
    df = pd.read_parquet(BRONZE_REGISTRY_PATH)
    assert "patient_id" in df.columns
    assert df["patient_id"].nunique() == len(df), "Duplicate patient_ids in registry"

def test_bronze_all_tables_present():
    expected = [
        "vitals_raw.parquet", "patient_registry.parquet",
        "alert_events_raw.parquet", "icu_capacity_raw.parquet",
        "interventions_raw.parquet",
    ]
    for fname in expected:
        assert os.path.exists(os.path.join(BRONZE_DIR, fname)), f"Missing: {fname}"

def test_bronze_vitals_no_empty_patient_ids():
    df = pd.read_parquet(BRONZE_VITALS_PATH)
    assert df["patient_id"].notna().all(), "Null patient_ids in Bronze vitals"
