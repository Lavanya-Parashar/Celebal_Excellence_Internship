"""
Gold Layer — Business Insights & ML Scoring
============================================
Reads the Silver vitals table and ancillary Bronze tables, then produces
the five Gold reports consumed by dashboards, alerts and clinical staff.

Gold Reports:
  01  Hourly Patient Vitals Summary
  02  Deterioration Risk Score Report
  03  Alert Response Time Report
  04  ICU Capacity Utilisation Report
  05  High-Risk Patient Detection Report

Usage:
    from pipeline.gold_layer import GoldLayer
    gl = GoldLayer()
    gl.run()
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    BRONZE_DIR, SILVER_DIR, GOLD_DIR, REPORTS_DIR, MODEL_DIR,
    SILVER_VITALS_PATH,
    GOLD_VITALS_SUMMARY_PATH, GOLD_RISK_SCORES_PATH,
    GOLD_ALERT_RESPONSE_PATH, GOLD_ICU_CAPACITY_PATH, GOLD_HIGH_RISK_PATH,
    RISK_THRESHOLD, ML_FEATURES,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [GOLD] %(levelname)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


class GoldLayer:
    """Produces all five Gold-layer clinical reports."""

    def __init__(self):
        os.makedirs(GOLD_DIR, exist_ok=True)
        os.makedirs(REPORTS_DIR, exist_ok=True)
        self._silver: pd.DataFrame | None = None
        self._model = None
        self._scaler = None

    # ── Public API ───────────────────────────────────────────────────────────

    def run(self) -> dict:
        log.info("Starting Gold layer aggregation & reporting …")
        self._load_silver()
        self._load_ml_model()

        report1 = self.build_hourly_vitals_summary()
        report2 = self.build_risk_score_report()
        report3 = self.build_alert_response_report()
        report4 = self.build_icu_capacity_report()
        report5 = self.build_high_risk_report(report2)

        reports = {
            "hourly_vitals_summary":    report1,
            "deterioration_risk_scores": report2,
            "alert_response_times":     report3,
            "icu_capacity":             report4,
            "high_risk_patients":       report5,
        }
        log.info("Gold layer complete — all 5 reports generated")
        return reports

    # ── Data Loading ─────────────────────────────────────────────────────────

    def _load_silver(self):
        log.info("  Loading Silver vitals …")
        self._silver = pd.read_parquet(SILVER_VITALS_PATH)
        log.info(f"    {len(self._silver):,} rows, {self._silver['patient_id'].nunique()} patients")

    def _load_ml_model(self):
        """Load trained RandomForest model if available, else use sepsis_risk_score."""
        model_path  = os.path.join(MODEL_DIR, "deterioration_rf_model.joblib")
        scaler_path = os.path.join(MODEL_DIR, "feature_scaler.joblib")
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            import joblib
            self._model  = joblib.load(model_path)
            self._scaler = joblib.load(scaler_path)
            log.info("  ✔ ML model loaded")
        else:
            log.warning("  ML model not found — using sepsis_risk_score as proxy risk")

    def _engineer_features_for_scoring(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add engineered features matching those used in ML training."""
        df = df.copy()
        df["shock_index"]      = (df["heart_rate"] / df["systolic_bp"].replace(0, np.nan)).fillna(0)
        df["spo2_hr_product"]  = df["spo2_pct"] * df["heart_rate"] / 100
        df["pulse_pressure"]   = df["systolic_bp"] - df["diastolic_bp"]
        df["temp_deviation"]   = abs(df["temperature_c"] - 37.0)
        df["flag_low_spo2"]    = (df["spo2_pct"]         < 90).astype(int)
        df["flag_tachy"]       = (df["heart_rate"]        > 120).astype(int)
        df["flag_hypotension"] = (df["systolic_bp"]       < 90).astype(int)
        df["flag_tachypnea"]   = (df["respiratory_rate"]  > 24).astype(int)
        df["flag_fever"]       = (df["temperature_c"]     > 38.5).astype(int)
        df["flag_high_lactate"]= (df["lactate"]           > 2.0).astype(int)
        df["flag_high_crp"]    = (df["crp_level"]         > 50).astype(int)
        df["organ_dysfunction"]= (
            df["flag_low_spo2"] + df["flag_hypotension"] +
            df["flag_high_lactate"] + df["flag_tachypnea"]
        )
        return df

    def _score_patients(self, df: pd.DataFrame) -> np.ndarray:
        """Return per-row deterioration probability."""
        if self._model is not None:
            import json
            cols_path = os.path.join(MODEL_DIR, "feature_columns.json")
            if os.path.exists(cols_path):
                with open(cols_path) as f2:
                    feature_cols = json.load(f2)
            else:
                feature_cols = ML_FEATURES
            df_eng = self._engineer_features_for_scoring(df)
            X = df_eng.reindex(columns=feature_cols, fill_value=0).fillna(0).values
            X = self._scaler.transform(X)
            return self._model.predict_proba(X)[:, 1]
        # Fallback: linear blend of available risk signals
        score = df["sepsis_risk_score"].copy()
        if "ews_score" in df.columns:
            score = 0.5 * score + 0.5 * (df["ews_score"] / 15.0).clip(0, 1)
        return score.values

    # ── Report 01: Hourly Patient Vitals Summary ──────────────────────────────

    def build_hourly_vitals_summary(self) -> pd.DataFrame:
        log.info("  Building Report 01: Hourly Vitals Summary …")
        df = self._silver.copy()
        df["hour_bucket"] = pd.to_datetime(df["timestamp"]).dt.floor("h")

        summary = df.groupby(["patient_id", "hour_bucket"]).agg(
            avg_heart_rate      =("heart_rate",       "mean"),
            avg_spo2            =("spo2_pct",          "mean"),
            avg_respiratory_rate=("respiratory_rate",  "mean"),
            avg_systolic_bp     =("systolic_bp",       "mean"),
            avg_diastolic_bp    =("diastolic_bp",      "mean"),
            avg_temperature_c   =("temperature_c",     "mean"),
            min_spo2            =("spo2_pct",          "min"),
            max_heart_rate      =("heart_rate",        "max"),
            avg_sepsis_risk     =("sepsis_risk_score", "mean"),
            vital_flag_count    =("vital_flag",        "sum"),
            total_readings      =("heart_rate",        "count"),
        ).reset_index()

        for c in ["avg_heart_rate","avg_spo2","avg_respiratory_rate",
                  "avg_systolic_bp","avg_diastolic_bp","avg_temperature_c","avg_sepsis_risk"]:
            summary[c] = summary[c].round(2)

        # Merge ward/condition if available
        if "ward" in df.columns:
            ward_map = df.groupby("patient_id")["ward"].first()
            summary  = summary.merge(ward_map, on="patient_id", how="left")

        self._write_gold(summary, GOLD_VITALS_SUMMARY_PATH, "hourly_vitals_summary")
        return summary

    # ── Report 02: Deterioration Risk Score Report ────────────────────────────

    def build_risk_score_report(self) -> pd.DataFrame:
        log.info("  Building Report 02: Deterioration Risk Scores …")
        df = self._silver.copy()
        df["risk_score"] = self._score_patients(df)
        df["risk_score"] = df["risk_score"].round(4)
        df["risk_flag"]  = (df["risk_score"] >= RISK_THRESHOLD).astype(int)

        # Latest risk score per patient (most recent observation)
        latest = (
            df.sort_values("timestamp")
              .groupby("patient_id")
              .last()
              .reset_index()
        )
        risk_report = latest[[
            "patient_id", "timestamp", "risk_score", "risk_flag",
            "heart_rate", "spo2_pct", "respiratory_rate",
            "systolic_bp", "temperature_c", "sepsis_risk_score",
            "ews_score", "risk_band",
        ]].copy()
        # Add ward/name if available
        if "ward" in latest.columns:
            risk_report["ward"]    = latest["ward"].values
        if "name" in latest.columns:
            risk_report["name"]    = latest["name"].values
        if "age" in latest.columns:
            risk_report["age"]     = latest["age"].values
        if "primary_condition" in latest.columns:
            risk_report["primary_condition"] = latest["primary_condition"].values

        risk_report["last_updated"] = datetime.utcnow().isoformat()

        self._write_gold(risk_report, GOLD_RISK_SCORES_PATH, "deterioration_risk_scores")
        return risk_report

    # ── Report 03: Alert Response Time Report ────────────────────────────────

    def build_alert_response_report(self) -> pd.DataFrame:
        log.info("  Building Report 03: Alert Response Times …")
        alerts_path = os.path.join(BRONZE_DIR, "alert_events_raw.parquet")
        intv_path   = os.path.join(BRONZE_DIR, "interventions_raw.parquet")

        if not os.path.exists(alerts_path) or not os.path.exists(intv_path):
            log.warning("    Alert/Intervention tables not found — building from Silver")
            return self._fallback_alert_report()

        alerts = pd.read_parquet(alerts_path)
        intv   = pd.read_parquet(intv_path)

        merged = alerts.merge(
            intv[["alert_id", "response_time_min", "intervention_time", "action", "clinician_id"]],
            on="alert_id", how="left"
        )

        # SLA: Critical < 5 min, High < 10 min, Medium < 20 min
        sla_map   = {"Critical": 5, "High": 10, "Medium": 20, "Low": 45}
        merged["sla_minutes"] = merged["severity"].map(sla_map).fillna(30)
        merged["sla_met"]     = (merged["response_time_min"] <= merged["sla_minutes"]).astype(int)

        summary = merged.groupby(["severity", "alert_type"]).agg(
            total_alerts       =("alert_id",          "count"),
            avg_response_min   =("response_time_min", "mean"),
            median_response_min=("response_time_min", "median"),
            max_response_min   =("response_time_min", "max"),
            sla_met_pct        =("sla_met",            "mean"),
        ).reset_index()
        summary["avg_response_min"]    = summary["avg_response_min"].round(1)
        summary["median_response_min"] = summary["median_response_min"].round(1)
        summary["sla_met_pct"]         = (summary["sla_met_pct"] * 100).round(1)

        # Also save the full merged table
        full_path = os.path.join(GOLD_DIR, "alert_response_full.parquet")
        self._write_gold(merged, full_path, "alert_response_full")
        self._write_gold(summary, GOLD_ALERT_RESPONSE_PATH, "alert_response_times")
        return summary

    def _fallback_alert_report(self) -> pd.DataFrame:
        """Create alert report directly from Silver if Bronze alert tables missing."""
        df = self._silver.copy()
        flagged = df[df["vital_flag"] == 1].copy()
        import random
        rng = np.random.default_rng(99)
        severities = rng.choice(["Low","Medium","High","Critical"], size=len(flagged),
                                 p=[0.3, 0.35, 0.25, 0.10])
        resp_times = rng.integers(2, 45, size=len(flagged))
        sla_map  = {"Critical": 5, "High": 10, "Medium": 20, "Low": 45}
        report = pd.DataFrame({
            "patient_id":       flagged["patient_id"].values,
            "alert_time":       flagged["timestamp"].values,
            "severity":         severities,
            "response_time_min": resp_times,
        })
        report["sla_minutes"] = report["severity"].map(sla_map)
        report["sla_met"]     = (report["response_time_min"] <= report["sla_minutes"]).astype(int)
        self._write_gold(report, GOLD_ALERT_RESPONSE_PATH, "alert_response_times")
        return report

    # ── Report 04: ICU Capacity Utilisation ──────────────────────────────────

    def build_icu_capacity_report(self) -> pd.DataFrame:
        log.info("  Building Report 04: ICU Capacity Utilisation …")
        icu_path = os.path.join(BRONZE_DIR, "icu_capacity_raw.parquet")

        if os.path.exists(icu_path):
            icu = pd.read_parquet(icu_path)
        else:
            log.warning("    ICU capacity table not found — generating")
            icu = self._generate_icu_data()

        icu["last_updated"]      = pd.to_datetime(icu["last_updated"])
        icu["utilisation_pct"]   = (icu["occupied_beds"] / icu["total_beds"] * 100).round(1)
        icu["pressure_level"]    = pd.cut(
            icu["utilisation_pct"],
            bins=[0, 60, 80, 95, 101],
            labels=["Normal", "Moderate", "High", "Critical"],
        )

        # Hourly average per unit
        icu["hour_bucket"] = icu["last_updated"].dt.floor("h")
        summary = icu.groupby(["unit_id", "floor", "hour_bucket"]).agg(
            total_beds     =("total_beds",      "first"),
            avg_occupied   =("occupied_beds",   "mean"),
            avg_available  =("available_beds",  "mean"),
            avg_util_pct   =("utilisation_pct", "mean"),
            peak_util_pct  =("utilisation_pct", "max"),
        ).reset_index()
        summary["avg_occupied"]  = summary["avg_occupied"].round(1)
        summary["avg_util_pct"]  = summary["avg_util_pct"].round(1)
        summary["peak_util_pct"] = summary["peak_util_pct"].round(1)

        self._write_gold(summary, GOLD_ICU_CAPACITY_PATH, "icu_capacity")
        return summary

    def _generate_icu_data(self) -> pd.DataFrame:
        rng = np.random.default_rng(7)
        UNITS = [("ICU-A",3,20),("ICU-B",3,18),("CCU",2,12),("HDU",4,24)]
        rows  = []
        for h in range(72):
            ts = pd.Timestamp("2025-01-01") + pd.Timedelta(hours=h)
            for uid, fl, tot in UNITS:
                occ = int(rng.integers(max(0,tot-6), tot+1))
                rows.append({"unit_id":uid,"floor":fl,"total_beds":tot,
                              "occupied_beds":min(occ,tot),
                              "available_beds":max(tot-occ,0),"last_updated":ts})
        return pd.DataFrame(rows)

    # ── Report 05: High-Risk Patient Detection ────────────────────────────────

    def build_high_risk_report(self, risk_df: pd.DataFrame) -> pd.DataFrame:
        log.info("  Building Report 05: High-Risk Patient Detection …")
        high_risk = risk_df[risk_df["risk_score"] >= RISK_THRESHOLD].copy()
        high_risk = high_risk.sort_values("risk_score", ascending=False)
        high_risk["recommended_action"] = high_risk["risk_score"].apply(
            lambda s: "Immediate ICU Review" if s >= 0.75
                 else "Urgent Ward Review"   if s >= 0.55
                 else "Increase Monitoring Frequency"
        )
        high_risk["report_date"] = datetime.utcnow().date().isoformat()
        self._write_gold(high_risk, GOLD_HIGH_RISK_PATH, "high_risk_patients")
        log.info(f"    High-risk patients flagged: {len(high_risk)}")
        return high_risk

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _write_gold(self, df: pd.DataFrame, path: str, label: str):
        tmp = path + ".tmp"
        df.to_parquet(tmp, index=False, engine="pyarrow")
        os.replace(tmp, path)
        # Also export as CSV for easy inspection
        csv_path = path.replace(".parquet", ".csv")
        df.to_csv(csv_path, index=False)
        log.info(f"  ✔ {label}: {len(df):,} rows → {os.path.basename(path)}")


if __name__ == "__main__":
    gl = GoldLayer()
    reports = gl.run()
    for name, df in reports.items():
        print(f"\n{'='*50}")
        print(f"Report: {name}  ({len(df)} rows)")
        print(df.head(3).to_string())
