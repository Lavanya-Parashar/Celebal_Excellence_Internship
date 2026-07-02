"""
Tests — Gold Layer
Run with: pytest tests/test_gold.py -v
"""
import os, sys, pytest
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    GOLD_VITALS_SUMMARY_PATH, GOLD_RISK_SCORES_PATH,
    GOLD_ALERT_RESPONSE_PATH, GOLD_ICU_CAPACITY_PATH, GOLD_HIGH_RISK_PATH,
    RISK_THRESHOLD,
)


def _load(path):
    assert os.path.exists(path), f"Gold table not found: {path}"
    return pd.read_parquet(path)

# ── Report 01 ─────────────────────────────────────────────────────────────────
def test_gold_vitals_summary_exists():     _load(GOLD_VITALS_SUMMARY_PATH)

def test_gold_vitals_summary_columns():
    df = _load(GOLD_VITALS_SUMMARY_PATH)
    for col in ["patient_id","hour_bucket","avg_heart_rate","avg_spo2"]:
        assert col in df.columns, f"Missing: {col}"

def test_gold_vitals_summary_no_nulls_in_key_cols():
    df = _load(GOLD_VITALS_SUMMARY_PATH)
    assert df["patient_id"].notna().all()
    assert df["avg_heart_rate"].notna().all()

# ── Report 02 ─────────────────────────────────────────────────────────────────
def test_gold_risk_scores_exists():     _load(GOLD_RISK_SCORES_PATH)

def test_gold_risk_scores_range():
    df = _load(GOLD_RISK_SCORES_PATH)
    assert df["risk_score"].between(0, 1).all(), "Risk scores outside [0,1]"

def test_gold_risk_flag_consistent():
    df = _load(GOLD_RISK_SCORES_PATH)
    expected_flag = (df["risk_score"] >= RISK_THRESHOLD).astype(int)
    assert (df["risk_flag"] == expected_flag).all(), "risk_flag inconsistent with risk_score"

def test_gold_risk_one_row_per_patient():
    df = _load(GOLD_RISK_SCORES_PATH)
    assert df["patient_id"].nunique() == len(df), "Duplicate patient_ids in risk score report"

# ── Report 03 ─────────────────────────────────────────────────────────────────
def test_gold_alert_response_exists():  _load(GOLD_ALERT_RESPONSE_PATH)

def test_gold_alert_response_times_non_negative():
    df = _load(GOLD_ALERT_RESPONSE_PATH)
    if "avg_response_min" in df.columns:
        assert (df["avg_response_min"] >= 0).all()
    elif "response_time_min" in df.columns:
        assert (df["response_time_min"] >= 0).all()

# ── Report 04 ─────────────────────────────────────────────────────────────────
def test_gold_icu_capacity_exists():    _load(GOLD_ICU_CAPACITY_PATH)

def test_gold_icu_utilisation_range():
    df = _load(GOLD_ICU_CAPACITY_PATH)
    assert "avg_util_pct" in df.columns
    assert (df["avg_util_pct"] >= 0).all() and (df["avg_util_pct"] <= 100).all()

# ── Report 05 ─────────────────────────────────────────────────────────────────
def test_gold_high_risk_exists():       _load(GOLD_HIGH_RISK_PATH)

def test_gold_high_risk_all_above_threshold():
    df = _load(GOLD_HIGH_RISK_PATH)
    assert (df["risk_score"] >= RISK_THRESHOLD).all(), \
        "High-risk report contains patients below risk threshold"

def test_gold_high_risk_has_recommended_action():
    df = _load(GOLD_HIGH_RISK_PATH)
    assert "recommended_action" in df.columns
    assert df["recommended_action"].notna().all()
