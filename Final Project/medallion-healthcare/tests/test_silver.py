"""
Tests — Silver Layer
Run with: pytest tests/test_silver.py -v
"""
import os, sys, pytest
import pandas as pd
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import SILVER_VITALS_PATH, VITAL_THRESHOLDS


def test_silver_exists():
    assert os.path.exists(SILVER_VITALS_PATH), "Silver vitals Parquet not found"

def test_silver_not_empty():
    df = pd.read_parquet(SILVER_VITALS_PATH)
    assert len(df) > 0

def test_silver_no_duplicates():
    df = pd.read_parquet(SILVER_VITALS_PATH)
    dupes = df.duplicated(subset=["patient_id", "timestamp"]).sum()
    assert dupes == 0, f"{dupes} duplicate (patient_id, timestamp) rows found"

def test_silver_vital_outliers_removed():
    df = pd.read_parquet(SILVER_VITALS_PATH)
    for col, bounds in VITAL_THRESHOLDS.items():
        if col in df.columns:
            out_of_range = ((df[col] < bounds["low"]) | (df[col] > bounds["high"])).sum()
            assert out_of_range == 0, f"{col}: {out_of_range} out-of-range rows remain"

def test_silver_no_nulls_in_vitals():
    df = pd.read_parquet(SILVER_VITALS_PATH)
    vital_cols = ["heart_rate", "spo2_pct", "temperature_c", "systolic_bp"]
    for col in vital_cols:
        if col in df.columns:
            nulls = df[col].isna().sum()
            assert nulls == 0, f"{col}: {nulls} nulls in Silver"

def test_silver_derived_features_exist():
    df = pd.read_parquet(SILVER_VITALS_PATH)
    for col in ["vital_flag", "ews_score", "risk_band"]:
        assert col in df.columns, f"Derived feature {col} missing from Silver"

def test_silver_ews_score_non_negative():
    df = pd.read_parquet(SILVER_VITALS_PATH)
    assert (df["ews_score"] >= 0).all(), "Negative EWS scores found"

def test_silver_has_fewer_rows_than_bronze():
    """Silver should be equal to or less than Bronze (outliers removed)."""
    from config.settings import BRONZE_VITALS_PATH
    bronze = pd.read_parquet(BRONZE_VITALS_PATH)
    silver = pd.read_parquet(SILVER_VITALS_PATH)
    assert len(silver) <= len(bronze), "Silver has MORE rows than Bronze — something went wrong"

def test_silver_registry_join_worked():
    df = pd.read_parquet(SILVER_VITALS_PATH)
    assert "ward" in df.columns, "Registry join failed — 'ward' column missing"
