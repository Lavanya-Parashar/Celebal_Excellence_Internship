"""
Data Preparation Script
=======================
Generates all 5 source datasets required by the Medallion pipeline from the
50 patient CSV files (hospital_deterioration_ml_ready_0.csv … _49.csv).

Run this ONCE before the pipeline:
    python data/prepare_datasets.py

Outputs (all in data/raw/):
    vitals_stream.csv        — core vitals per patient per hour
    patient_registry.csv     — one row per patient (demographics)
    alert_events.csv         — simulated clinical alerts
    icu_capacity.csv         — hourly ICU bed utilisation
    interventions.csv        — clinical actions taken after alerts
"""

import os
import glob
import pandas as pd
import numpy as np
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import RAW_DATA_DIR, NUM_SOURCE_FILES

rng = np.random.default_rng(42)

# ── Helpers ──────────────────────────────────────────────────────────────────

def load_all_files() -> pd.DataFrame:
    """Load all available source CSVs and tag each with patient_id."""
    frames = []
    for idx in range(NUM_SOURCE_FILES):
        path = os.path.join(RAW_DATA_DIR, f"hospital_deterioration_ml_ready_{idx}.csv")
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path)
        df["patient_id"] = f"P{idx:04d}"
        frames.append(df)
    if not frames:
        raise FileNotFoundError(
            f"No source CSVs found in {RAW_DATA_DIR}. "
            "Copy all 50 files there and re-run."
        )
    combined = pd.concat(frames, ignore_index=True)
    print(f"  Loaded {len(frames)} patient files → {len(combined):,} rows total")
    return combined


# ── Dataset 1: vitals_stream.csv ─────────────────────────────────────────────

def build_vitals_stream(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (patient_id, hour_from_admission) with all vital columns."""
    cols = [
        "patient_id", "hour_from_admission",
        "heart_rate", "respiratory_rate", "spo2_pct",
        "temperature_c", "systolic_bp", "diastolic_bp",
        "oxygen_device", "oxygen_flow",
        "mobility_score", "nurse_alert",
        "wbc_count", "lactate", "creatinine",
        "crp_level", "hemoglobin", "sepsis_risk_score",
        "deterioration_next_12h",
    ]
    vitals = df[cols].copy()
    # Create a realistic wall-clock timestamp (anchor = 2025-01-01)
    base_ts = pd.Timestamp("2025-01-01 00:00:00")
    vitals["timestamp"] = base_ts + pd.to_timedelta(
        vitals["hour_from_admission"], unit="h"
    )
    vitals["ingest_ts"] = vitals["timestamp"]   # Bronze ingestion timestamp
    return vitals


# ── Dataset 2: patient_registry.csv ─────────────────────────────────────────

def build_patient_registry(df: pd.DataFrame) -> pd.DataFrame:
    """One row per patient with demographics and ward assignment."""
    WARDS = ["ICU", "CCU", "General", "HDU", "Emergency"]
    CONDITIONS = [
        "Sepsis", "Heart Failure", "COPD Exacerbation",
        "Pneumonia", "Post-Op Monitoring", "Renal Failure",
        "Stroke", "Trauma",
    ]

    registry = (
        df.groupby("patient_id")
        .first()
        .reset_index()[["patient_id", "age", "gender", "comorbidity_index", "admission_type"]]
    )

    n = len(registry)
    registry["ward"]              = rng.choice(WARDS, size=n)
    registry["primary_condition"] = rng.choice(CONDITIONS, size=n)
    base_admissions = pd.date_range("2024-12-01", periods=n, freq="3h")
    registry["admission_date"]    = base_admissions[:n]
    registry["name"]              = [f"Patient_{pid}" for pid in registry["patient_id"]]
    return registry[["patient_id", "name", "age", "gender", "ward",
                      "admission_date", "primary_condition",
                      "comorbidity_index", "admission_type"]]


# ── Dataset 3: alert_events.csv ──────────────────────────────────────────────

def build_alert_events(vitals: pd.DataFrame) -> pd.DataFrame:
    """Generate clinical alerts for rows where vitals cross thresholds."""
    ALERT_TYPES = [
        "Tachycardia", "Hypoxia", "Hypotension",
        "Tachypnea", "Fever", "High Sepsis Risk",
    ]
    SEVERITIES  = ["Low", "Medium", "High", "Critical"]

    triggered = vitals[
        (vitals["heart_rate"]        > 120) |
        (vitals["spo2_pct"]          < 90)  |
        (vitals["systolic_bp"]       < 90)  |
        (vitals["respiratory_rate"]  > 24)  |
        (vitals["temperature_c"]     > 38.5)|
        (vitals["sepsis_risk_score"] > 0.7)
    ].copy()

    n = len(triggered)
    alerts = pd.DataFrame({
        "alert_id":    [f"ALT{i:06d}" for i in range(n)],
        "patient_id":  triggered["patient_id"].values,
        "alert_time":  triggered["timestamp"].values,
        "alert_type":  rng.choice(ALERT_TYPES, size=n),
        "severity":    rng.choice(SEVERITIES,  size=n, p=[0.3, 0.35, 0.25, 0.10]),
        "resolved":    rng.choice([0, 1],       size=n, p=[0.15, 0.85]),
    })
    return alerts


# ── Dataset 4: icu_capacity.csv ──────────────────────────────────────────────

def build_icu_capacity() -> pd.DataFrame:
    """Hourly ICU bed utilisation over 72 hours across 4 units."""
    UNITS  = ["ICU-A", "ICU-B", "CCU", "HDU"]
    FLOORS = [3, 3, 2, 4]
    TOTAL  = [20, 18, 12, 24]

    rows = []
    for hour in range(72):
        ts = pd.Timestamp("2025-01-01") + pd.Timedelta(hours=hour)
        for unit, floor, total in zip(UNITS, FLOORS, TOTAL):
            occupied = int(rng.integers(
                low=max(0, total - 6),
                high=total + 1,
            ))
            rows.append({
                "unit_id":      unit,
                "total_beds":   total,
                "occupied_beds": min(occupied, total),
                "available_beds": max(total - occupied, 0),
                "last_updated": ts,
                "floor":        floor,
            })
    return pd.DataFrame(rows)


# ── Dataset 5: interventions.csv ─────────────────────────────────────────────

def build_interventions(alerts: pd.DataFrame) -> pd.DataFrame:
    """One clinical intervention per alert (with realistic response times)."""
    ACTIONS     = [
        "IV Fluids", "O2 Therapy", "Medication Adjustment",
        "Emergency Consult", "Lab Work Ordered", "ECG Performed",
        "Repositioning", "Escalated to ICU",
    ]
    CLINICIANS  = [f"CLN{i:03d}" for i in range(1, 31)]

    n = len(alerts)
    response_min = rng.integers(low=2, high=45, size=n)

    interventions = pd.DataFrame({
        "intervention_id": [f"INT{i:06d}" for i in range(n)],
        "alert_id":        alerts["alert_id"].values,
        "patient_id":      alerts["patient_id"].values,
        "action":          rng.choice(ACTIONS,    size=n),
        "clinician_id":    rng.choice(CLINICIANS, size=n),
        "response_time_min": response_min,
        "intervention_time": pd.to_datetime(alerts["alert_time"].values)
                             + pd.to_timedelta(response_min, unit="m"),
    })
    return interventions


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    print("=" * 60)
    print("Preparing source datasets …")
    print("=" * 60)

    print("\n[1/5] Loading source CSVs …")
    df = load_all_files()

    print("[2/5] Building vitals_stream …")
    vitals = build_vitals_stream(df)
    vitals.to_csv(os.path.join(RAW_DATA_DIR, "vitals_stream.csv"), index=False)
    print(f"      → {len(vitals):,} rows")

    print("[3/5] Building patient_registry …")
    registry = build_patient_registry(df)
    registry.to_csv(os.path.join(RAW_DATA_DIR, "patient_registry.csv"), index=False)
    print(f"      → {len(registry):,} rows")

    print("[4/5] Building alert_events …")
    alerts = build_alert_events(vitals)
    alerts.to_csv(os.path.join(RAW_DATA_DIR, "alert_events.csv"), index=False)
    print(f"      → {len(alerts):,} rows")

    print("[5/5] Building icu_capacity …")
    icu = build_icu_capacity()
    icu.to_csv(os.path.join(RAW_DATA_DIR, "icu_capacity.csv"), index=False)
    print(f"      → {len(icu):,} rows")

    print("      Building interventions …")
    interventions = build_interventions(alerts)
    interventions.to_csv(os.path.join(RAW_DATA_DIR, "interventions.csv"), index=False)
    print(f"      → {len(interventions):,} rows")

    print("\n✅  All 5 datasets written to", RAW_DATA_DIR)
    print("=" * 60)


if __name__ == "__main__":
    main()
