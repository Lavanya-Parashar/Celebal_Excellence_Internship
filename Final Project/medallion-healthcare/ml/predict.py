"""
ML Inference — Real-Time Patient Risk Scoring
=============================================
Loads the trained RandomForest model and scores new patient vitals records.
Can be called by the Gold layer, dashboard, or any external service.

Usage:
    from ml.predict import Predictor
    predictor = Predictor()

    # Score a single record (dict)
    score = predictor.score_single({"heart_rate": 130, "spo2_pct": 88, ...})

    # Score a full DataFrame
    df_with_scores = predictor.score_dataframe(df)

    # Get risk band from raw score
    band = predictor.risk_band(0.65)   # → "High"
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import MODEL_DIR, RISK_THRESHOLD, ML_FEATURES

log = logging.getLogger(__name__)


class Predictor:
    """Wraps the trained deterioration model for inference."""

    def __init__(self):
        self._model         = None
        self._scaler        = None
        self._feature_cols  = None
        self._metrics       = None
        self._loaded        = False
        self._load()

    # ── Model Loading ─────────────────────────────────────────────────────────

    def _load(self):
        try:
            import joblib
            model_path   = os.path.join(MODEL_DIR, "deterioration_rf_model.joblib")
            scaler_path  = os.path.join(MODEL_DIR, "feature_scaler.joblib")
            cols_path    = os.path.join(MODEL_DIR, "feature_columns.json")
            metrics_path = os.path.join(MODEL_DIR, "model_metrics.json")

            if not os.path.exists(model_path):
                log.warning("Model not found — run `python ml/train_model.py` first")
                return

            self._model  = joblib.load(model_path)
            self._scaler = joblib.load(scaler_path)

            if os.path.exists(cols_path):
                with open(cols_path) as f:
                    self._feature_cols = json.load(f)
            else:
                self._feature_cols = ML_FEATURES

            if os.path.exists(metrics_path):
                with open(metrics_path) as f:
                    self._metrics = json.load(f)

            self._loaded = True
            log.info(f"Model loaded — {len(self._feature_cols)} features")
        except Exception as e:
            log.error(f"Failed to load model: {e}")

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def metrics(self) -> dict:
        return self._metrics or {}

    # ── Feature Engineering (must match train_model.py) ───────────────────────

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["shock_index"]      = (df.get("heart_rate", 80) /
                                   df.get("systolic_bp", 120).replace(0, np.nan)).fillna(0)
        df["spo2_hr_product"]  = df.get("spo2_pct", 98) * df.get("heart_rate", 80) / 100
        df["pulse_pressure"]   = df.get("systolic_bp", 120) - df.get("diastolic_bp", 80)
        df["temp_deviation"]   = abs(df.get("temperature_c", 37.0) - 37.0)
        df["flag_low_spo2"]    = (df.get("spo2_pct", 98)        < 90).astype(int)
        df["flag_tachy"]       = (df.get("heart_rate", 80)       > 120).astype(int)
        df["flag_hypotension"] = (df.get("systolic_bp", 120)     < 90).astype(int)
        df["flag_tachypnea"]   = (df.get("respiratory_rate", 16) > 24).astype(int)
        df["flag_fever"]       = (df.get("temperature_c", 37.0)  > 38.5).astype(int)
        df["flag_high_lactate"]= (df.get("lactate", 1.0)         > 2.0).astype(int)
        df["flag_high_crp"]    = (df.get("crp_level", 10)        > 50).astype(int)
        df["organ_dysfunction"]= (
            df["flag_low_spo2"] + df["flag_hypotension"] +
            df["flag_high_lactate"] + df["flag_tachypnea"]
        )
        return df

    def _prepare_X(self, df: pd.DataFrame) -> np.ndarray:
        df = self._engineer_features(df)
        X  = df.reindex(columns=self._feature_cols, fill_value=0).fillna(0).values
        return self._scaler.transform(X)

    # ── Inference API ─────────────────────────────────────────────────────────

    def score_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add risk_score and risk_flag columns to df. Returns copy."""
        if not self._loaded:
            df = df.copy()
            df["risk_score"] = df.get("sepsis_risk_score", 0.3)
            df["risk_flag"]  = (df["risk_score"] >= RISK_THRESHOLD).astype(int)
            df["risk_band"]  = df["risk_score"].apply(self.risk_band)
            return df

        X                  = self._prepare_X(df)
        probs              = self._model.predict_proba(X)[:, 1]
        out                = df.copy()
        out["risk_score"]  = np.round(probs, 4)
        out["risk_flag"]   = (probs >= RISK_THRESHOLD).astype(int)
        out["risk_band"]   = pd.Series(probs).apply(self.risk_band).values
        return out

    def score_single(self, record: dict) -> dict:
        """Score a single patient record (dict). Returns enriched dict."""
        df    = pd.DataFrame([record])
        out   = self.score_dataframe(df)
        score = float(out["risk_score"].iloc[0])
        return {
            "risk_score":  score,
            "risk_flag":   int(score >= RISK_THRESHOLD),
            "risk_band":   self.risk_band(score),
            "alert":       score >= RISK_THRESHOLD,
            "explanation": self._explain(record, score),
        }

    def score_batch(self, records: list[dict]) -> list[dict]:
        """Score a list of patient records."""
        df  = pd.DataFrame(records)
        out = self.score_dataframe(df)
        return out[["risk_score", "risk_flag", "risk_band"]].to_dict(orient="records")

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def risk_band(score: float) -> str:
        if score >= 0.75: return "Critical"
        if score >= 0.55: return "High"
        if score >= 0.35: return "Medium"
        return "Low"

    @staticmethod
    def risk_color(score: float) -> str:
        if score >= 0.75: return "#e74c3c"
        if score >= 0.55: return "#e67e22"
        if score >= 0.35: return "#f1c40f"
        return "#27ae60"

    def _explain(self, record: dict, score: float) -> list[str]:
        """Return list of contributing risk factors for a given record."""
        reasons = []
        if record.get("heart_rate", 0)        > 120: reasons.append("Tachycardia (HR > 120)")
        if record.get("spo2_pct", 100)         < 90:  reasons.append("Hypoxia (SpO2 < 90%)")
        if record.get("systolic_bp", 120)      < 90:  reasons.append("Hypotension (SBP < 90)")
        if record.get("respiratory_rate", 16)  > 24:  reasons.append("Tachypnea (RR > 24)")
        if record.get("temperature_c", 37)     > 38.5:reasons.append("Fever (Temp > 38.5°C)")
        if record.get("lactate", 1.0)          > 2.0: reasons.append("Elevated Lactate (> 2 mmol/L)")
        if record.get("sepsis_risk_score", 0)  > 0.6: reasons.append("High Sepsis Risk Score")
        if record.get("nurse_alert", 0)        == 1:  reasons.append("Nurse Alert triggered")
        if not reasons and score >= RISK_THRESHOLD:
            reasons.append("Composite clinical score elevated")
        return reasons

    def get_model_info(self) -> dict:
        """Return model metadata for dashboard display."""
        if not self._metrics:
            return {"status": "Model not loaded"}
        return {
            "status":          "Loaded",
            "auc_roc":         self._metrics.get("auc_roc"),
            "f1_score":        self._metrics.get("f1_score"),
            "precision":       self._metrics.get("precision"),
            "recall":          self._metrics.get("recall"),
            "cv_auc_mean":     self._metrics.get("cv_auc_mean"),
            "train_rows":      self._metrics.get("train_rows"),
            "n_features":      self._metrics.get("n_features"),
            "risk_threshold":  RISK_THRESHOLD,
        }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    p = Predictor()
    if p.is_loaded:
        test_record = {
            "heart_rate": 138, "spo2_pct": 86, "respiratory_rate": 28,
            "systolic_bp": 85, "diastolic_bp": 55, "temperature_c": 39.1,
            "oxygen_flow": 6, "mobility_score": 1, "nurse_alert": 1,
            "wbc_count": 18, "lactate": 3.2, "creatinine": 2.1,
            "crp_level": 120, "hemoglobin": 9, "sepsis_risk_score": 0.85,
            "age": 72, "comorbidity_index": 5, "hour_from_admission": 8,
        }
        result = p.score_single(test_record)
        print("Risk Score :", result["risk_score"])
        print("Risk Band  :", result["risk_band"])
        print("Alert      :", result["alert"])
        print("Reasons    :", result["explanation"])
        print("\nModel Info :")
        for k, v in p.get_model_info().items():
            print(f"  {k}: {v}")
    else:
        print("Model not loaded. Run: python ml/train_model.py")
