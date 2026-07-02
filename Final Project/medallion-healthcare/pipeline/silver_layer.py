"""
Silver Layer — Cleaned & Standardised Data
===========================================
Reads Bronze Parquet tables and applies data-quality rules:

  1. Deduplication    — remove exact duplicate (patient_id, timestamp) pairs
  2. Outlier removal  — drop physiologically impossible vital readings
  3. Null handling    — impute or drop remaining nulls
  4. Type casting     — ensure correct dtypes
  5. Unit normalisation — temperatures already in °C, BP in mmHg (validate)
  6. Patient enrichment — join vitals with patient registry (ward, condition)
  7. Derived features — vital_flag (any abnormal reading), risk_band

Output is a single enriched vitals Parquet in data/silver/.

Usage:
    from pipeline.silver_layer import SilverLayer
    sl = SilverLayer()
    sl.run()
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    BRONZE_DIR, SILVER_DIR,
    BRONZE_VITALS_PATH, BRONZE_REGISTRY_PATH,
    SILVER_VITALS_PATH, VITAL_THRESHOLDS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SILVER] %(levelname)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


class SilverLayer:
    """Transforms Bronze data into a clean, enriched Silver dataset."""

    def __init__(self):
        os.makedirs(SILVER_DIR, exist_ok=True)
        self.stats: dict = {}

    # ── Public API ───────────────────────────────────────────────────────────

    def run(self) -> pd.DataFrame:
        """Execute full Silver pipeline. Returns cleaned DataFrame."""
        log.info("Starting Silver layer transformation …")

        vitals   = self._load_bronze_vitals()
        registry = self._load_bronze_registry()

        vitals = self._deduplicate(vitals)
        vitals = self._remove_outliers(vitals)
        vitals = self._handle_nulls(vitals)
        vitals = self._cast_types(vitals)
        vitals = self._enrich_with_registry(vitals, registry)
        vitals = self._add_derived_features(vitals)
        vitals = self._add_silver_audit(vitals)

        self._write(vitals)
        self._log_stats(vitals)
        return vitals

    # ── Load ─────────────────────────────────────────────────────────────────

    def _load_bronze_vitals(self) -> pd.DataFrame:
        log.info("  Loading Bronze vitals …")
        df = pd.read_parquet(BRONZE_VITALS_PATH)
        log.info(f"    Bronze vitals: {len(df):,} rows")
        self.stats["bronze_rows"] = len(df)
        return df

    def _load_bronze_registry(self) -> pd.DataFrame:
        log.info("  Loading Bronze patient registry …")
        return pd.read_parquet(BRONZE_REGISTRY_PATH)

    # ── Quality Steps ────────────────────────────────────────────────────────

    def _deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove exact (patient_id, timestamp) duplicates — keep last."""
        before = len(df)
        df = df.drop_duplicates(subset=["patient_id", "timestamp"], keep="last")
        removed = before - len(df)
        if removed:
            log.info(f"    Dedup: removed {removed:,} duplicate rows")
        else:
            log.info("    Dedup: no duplicates found")
        self.stats["dedup_removed"] = removed
        return df

    def _remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop rows where any vital is physiologically impossible."""
        before = len(df)
        mask = pd.Series(True, index=df.index)
        for col, bounds in VITAL_THRESHOLDS.items():
            if col in df.columns:
                mask &= (df[col] >= bounds["low"]) & (df[col] <= bounds["high"])
        df = df[mask].copy()
        removed = before - len(df)
        log.info(f"    Outlier removal: removed {removed:,} rows with impossible vitals")
        self.stats["outliers_removed"] = removed
        return df

    def _handle_nulls(self, df: pd.DataFrame) -> pd.DataFrame:
        """Forward-fill numeric nulls within each patient; drop remaining."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        # Forward-fill per patient (mimics carrying last valid sensor reading)
        df[numeric_cols] = (
            df.sort_values(["patient_id", "timestamp"])
              .groupby("patient_id")[numeric_cols]
              .ffill()
        )
        before = len(df)
        df = df.dropna(subset=numeric_cols)
        dropped = before - len(df)
        if dropped:
            log.info(f"    Null handling: dropped {dropped:,} rows still null after ffill")
        else:
            log.info("    Null handling: no nulls remain")
        self.stats["nulls_dropped"] = dropped
        return df

    def _cast_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure correct dtypes."""
        df["timestamp"]           = pd.to_datetime(df["timestamp"])
        df["heart_rate"]          = df["heart_rate"].astype(float).round(2)
        df["spo2_pct"]            = df["spo2_pct"].astype(float).round(2)
        df["temperature_c"]       = df["temperature_c"].astype(float).round(2)
        df["systolic_bp"]         = df["systolic_bp"].astype(float).round(1)
        df["diastolic_bp"]        = df["diastolic_bp"].astype(float).round(1)
        df["respiratory_rate"]    = df["respiratory_rate"].astype(float).round(1)
        df["sepsis_risk_score"]   = df["sepsis_risk_score"].astype(float).round(4)
        df["oxygen_device"]       = df["oxygen_device"].str.strip().str.lower()
        return df

    # ── Enrichment ───────────────────────────────────────────────────────────

    def _enrich_with_registry(self, vitals: pd.DataFrame, registry: pd.DataFrame) -> pd.DataFrame:
        """Left-join vitals with patient registry to add ward, condition, age etc."""
        # Only bring in the demographic columns not already in vitals
        reg_cols = ["patient_id", "name", "ward", "primary_condition",
                    "admission_date", "comorbidity_index"]
        reg_cols = [c for c in reg_cols if c in registry.columns]
        merged = vitals.merge(registry[reg_cols], on="patient_id", how="left",
                              suffixes=("", "_reg"))
        # Resolve any column conflicts (comorbidity_index may exist in both)
        for col in ["comorbidity_index"]:
            if f"{col}_reg" in merged.columns:
                merged[col] = merged[col].combine_first(merged[f"{col}_reg"])
                merged.drop(columns=[f"{col}_reg"], inplace=True)
        log.info(f"    Registry join: enriched with ward & primary_condition")
        return merged

    # ── Derived Features ─────────────────────────────────────────────────────

    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute additional clinical features used by the Gold layer."""

        # Vital flag: 1 if any vital reading is outside normal range
        df["vital_flag"] = (
            (df["heart_rate"]       > 100) | (df["heart_rate"]       < 60)  |
            (df["spo2_pct"]         < 94)                                    |
            (df["respiratory_rate"] > 20)  | (df["respiratory_rate"] < 12)  |
            (df["systolic_bp"]      < 100) | (df["systolic_bp"]       > 160) |
            (df["temperature_c"]    > 38.0)| (df["temperature_c"]    < 36.0)
        ).astype(int)

        # Early Warning Score proxy (NEWS2-inspired, simplified)
        df["ews_score"] = (
            (df["respiratory_rate"] > 24).astype(int) * 3 +
            (df["spo2_pct"]         < 92).astype(int) * 3 +
            (df["systolic_bp"]      < 90).astype(int) * 3 +
            (df["heart_rate"]       > 130).astype(int) * 3 +
            (df["temperature_c"]    > 39.0).astype(int) * 2 +
            (df["sepsis_risk_score"]> 0.6).astype(int) * 2 +
            (df["nurse_alert"]      == 1).astype(int) * 2
        )

        # Risk band derived from EWS score
        df["risk_band"] = pd.cut(
            df["ews_score"],
            bins=[-1, 0, 3, 6, 100],
            labels=["Low", "Medium", "High", "Critical"],
        )

        # Hour of day (for trend analysis)
        df["hour_of_day"] = pd.to_datetime(df["timestamp"]).dt.hour

        log.info("    Derived features: vital_flag, ews_score, risk_band, hour_of_day")
        return df

    # ── Audit & Write ─────────────────────────────────────────────────────────

    def _add_silver_audit(self, df: pd.DataFrame) -> pd.DataFrame:
        df["_silver_processed_ts"] = datetime.utcnow().isoformat()
        df["_silver_layer"]        = "SILVER"
        return df

    def _write(self, df: pd.DataFrame):
        tmp = SILVER_VITALS_PATH + ".tmp"
        df.to_parquet(tmp, index=False, engine="pyarrow")
        os.replace(tmp, SILVER_VITALS_PATH)
        log.info(f"  ✔ Silver vitals written: {len(df):,} rows → {SILVER_VITALS_PATH}")

    def _log_stats(self, df: pd.DataFrame):
        self.stats["silver_rows"]  = len(df)
        self.stats["patients"]     = df["patient_id"].nunique()
        log.info(
            f"Silver summary: {self.stats['silver_rows']:,} rows | "
            f"{self.stats['patients']:,} patients | "
            f"High/Critical risk rows: "
            f"{(df['risk_band'].isin(['High','Critical'])).sum():,}"
        )

    @staticmethod
    def get_stats() -> pd.DataFrame:
        df = pd.read_parquet(SILVER_VITALS_PATH)
        return pd.DataFrame([{
            "table":    "vitals_clean",
            "rows":     len(df),
            "patients": df["patient_id"].nunique(),
            "columns":  len(df.columns),
        }])


if __name__ == "__main__":
    sl = SilverLayer()
    sl.run()
