"""
ML Model Training — Patient Deterioration Predictor
=====================================================
Trains a Random Forest classifier on the 50-file patient dataset to predict
whether a patient will deteriorate in the next 12 hours.

Target variable : deterioration_next_12h  (0 / 1)
Features        : 18 clinical vitals + demographics (see ML_FEATURES in settings)

Output artefacts (saved to ml/model/):
    deterioration_rf_model.joblib   — trained RandomForestClassifier
    feature_scaler.joblib           — StandardScaler fitted on training data
    model_metrics.json              — precision, recall, F1, AUC-ROC
    feature_importance.csv          — ranked feature importances

Usage:
    python ml/train_model.py
"""

import os
import sys
import json
import glob
import logging
import warnings
import pandas as pd
import numpy as np
import joblib

from sklearn.ensemble          import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing     import StandardScaler
from sklearn.model_selection   import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics           import (
    classification_report, confusion_matrix,
    roc_auc_score, precision_recall_curve, average_precision_score,
    f1_score, precision_score, recall_score,
)
from sklearn.utils.class_weight import compute_class_weight

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    RAW_DATA_DIR, MODEL_DIR, ML_FEATURES, ML_TARGET,
    NUM_SOURCE_FILES,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ML-TRAIN] %(levelname)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Data Loading ─────────────────────────────────────────────────────────────

def load_training_data() -> pd.DataFrame:
    """Load all available patient CSVs from RAW_DATA_DIR."""
    frames = []
    found  = 0
    for idx in range(NUM_SOURCE_FILES):
        path = os.path.join(RAW_DATA_DIR, f"hospital_deterioration_ml_ready_{idx}.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            df["patient_id"] = f"P{idx:04d}"
            frames.append(df)
            found += 1

    if not frames:
        raise FileNotFoundError(
            f"No source CSVs found in {RAW_DATA_DIR}.\n"
            "Copy all 50 hospital_deterioration_ml_ready_*.csv files there."
        )

    combined = pd.concat(frames, ignore_index=True)
    log.info(f"Loaded {found} patient files → {len(combined):,} rows")
    log.info(f"Class balance: {combined[ML_TARGET].value_counts().to_dict()}")
    return combined


# ── Feature Engineering ───────────────────────────────────────────────────────

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add interaction and rolling features to improve model performance."""
    df = df.copy()

    # Shock index (HR / SBP) — elevated in haemodynamic instability
    df["shock_index"] = (df["heart_rate"] / df["systolic_bp"].replace(0, np.nan)).fillna(0)

    # SpO2 × HR interaction (both dropping = severe)
    df["spo2_hr_product"] = df["spo2_pct"] * df["heart_rate"] / 100

    # Pulse pressure
    df["pulse_pressure"] = df["systolic_bp"] - df["diastolic_bp"]

    # Temperature deviation from 37°C
    df["temp_deviation"] = abs(df["temperature_c"] - 37.0)

    # Binary flags for critical thresholds
    df["flag_low_spo2"]      = (df["spo2_pct"]         < 90).astype(int)
    df["flag_tachy"]         = (df["heart_rate"]        > 120).astype(int)
    df["flag_hypotension"]   = (df["systolic_bp"]       < 90).astype(int)
    df["flag_tachypnea"]     = (df["respiratory_rate"]  > 24).astype(int)
    df["flag_fever"]         = (df["temperature_c"]     > 38.5).astype(int)
    df["flag_high_lactate"]  = (df["lactate"]           > 2.0).astype(int)
    df["flag_high_crp"]      = (df["crp_level"]         > 50).astype(int)

    # Composite organ dysfunction score
    df["organ_dysfunction"] = (
        df["flag_low_spo2"] + df["flag_hypotension"] +
        df["flag_high_lactate"] + df["flag_tachypnea"]
    )

    return df


def get_feature_columns(df: pd.DataFrame) -> list:
    """Return all feature columns (ML_FEATURES + engineered)."""
    engineered = [
        "shock_index", "spo2_hr_product", "pulse_pressure", "temp_deviation",
        "flag_low_spo2", "flag_tachy", "flag_hypotension", "flag_tachypnea",
        "flag_fever", "flag_high_lactate", "flag_high_crp", "organ_dysfunction",
    ]
    base    = [c for c in ML_FEATURES    if c in df.columns]
    extra   = [c for c in engineered     if c in df.columns]
    return base + extra


# ── Training ──────────────────────────────────────────────────────────────────

def train(df: pd.DataFrame):
    os.makedirs(MODEL_DIR, exist_ok=True)

    log.info("Engineering features …")
    df = engineer_features(df)

    feature_cols = get_feature_columns(df)
    X = df[feature_cols].fillna(0).values
    y = df[ML_TARGET].values

    log.info(f"Feature matrix: {X.shape[0]:,} rows × {X.shape[1]} features")

    # ── Train / test split (stratified to handle 5% positive rate) ──────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # ── Scale ────────────────────────────────────────────────────────────────
    scaler  = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test  = scaler.transform(X_test)

    # ── Class weights (handle imbalance ~5% positive rate) ──────────────────
    classes = np.unique(y_train)
    weights = compute_class_weight("balanced", classes=classes, y=y_train)
    cw      = dict(zip(classes, weights))
    log.info(f"Class weights: {cw}")

    # ── Random Forest ────────────────────────────────────────────────────────
    log.info("Training RandomForestClassifier …")
    rf = RandomForestClassifier(
        n_estimators   = 200,
        max_depth      = 12,
        min_samples_leaf = 5,
        class_weight   = "balanced",
        n_jobs         = -1,
        random_state   = 42,
    )
    rf.fit(X_train, y_train)

    # ── Evaluation ───────────────────────────────────────────────────────────
    y_pred      = rf.predict(X_test)
    y_prob      = rf.predict_proba(X_test)[:, 1]

    auc_roc     = roc_auc_score(y_test, y_prob)
    avg_prec    = average_precision_score(y_test, y_prob)
    f1          = f1_score(y_test, y_pred)
    precision   = precision_score(y_test, y_pred, zero_division=0)
    recall      = recall_score(y_test, y_pred)

    log.info(f"AUC-ROC : {auc_roc:.4f}")
    log.info(f"Avg Prec: {avg_prec:.4f}")
    log.info(f"F1 Score: {f1:.4f}")
    log.info(f"Precision: {precision:.4f}  Recall: {recall:.4f}")
    log.info("\nClassification Report:\n" +
             classification_report(y_test, y_pred, target_names=["No Deterioration","Deterioration"]))

    # ── Cross-validation ─────────────────────────────────────────────────────
    log.info("5-fold cross-validation …")
    X_full = scaler.transform(
        df[feature_cols].fillna(0).values
    )
    cv_scores = cross_val_score(rf, X_full, y, cv=5, scoring="roc_auc", n_jobs=-1)
    log.info(f"CV AUC-ROC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # ── Save model artefacts ──────────────────────────────────────────────────
    model_path  = os.path.join(MODEL_DIR, "deterioration_rf_model.joblib")
    scaler_path = os.path.join(MODEL_DIR, "feature_scaler.joblib")
    joblib.dump(rf,     model_path)
    joblib.dump(scaler, scaler_path)
    log.info(f"Model saved  → {model_path}")
    log.info(f"Scaler saved → {scaler_path}")

    # ── Feature importance ────────────────────────────────────────────────────
    fi_df = pd.DataFrame({
        "feature":   feature_cols,
        "importance": rf.feature_importances_,
    }).sort_values("importance", ascending=False)
    fi_path = os.path.join(MODEL_DIR, "feature_importance.csv")
    fi_df.to_csv(fi_path, index=False)
    log.info(f"\nTop 10 features:\n{fi_df.head(10).to_string(index=False)}")

    # ── Metrics JSON ─────────────────────────────────────────────────────────
    metrics = {
        "auc_roc":           round(float(auc_roc),    4),
        "average_precision": round(float(avg_prec),   4),
        "f1_score":          round(float(f1),          4),
        "precision":         round(float(precision),   4),
        "recall":            round(float(recall),      4),
        "cv_auc_mean":       round(float(cv_scores.mean()), 4),
        "cv_auc_std":        round(float(cv_scores.std()),  4),
        "train_rows":        int(X_train.shape[0]),
        "test_rows":         int(X_test.shape[0]),
        "n_features":        len(feature_cols),
        "positive_rate":     round(float(y.mean()), 4),
        "confusion_matrix":  confusion_matrix(y_test, y_pred).tolist(),
        "feature_columns":   feature_cols,
    }
    metrics_path = os.path.join(MODEL_DIR, "model_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    log.info(f"Metrics saved → {metrics_path}")

    # Save feature column list for inference
    cols_path = os.path.join(MODEL_DIR, "feature_columns.json")
    with open(cols_path, "w") as f:
        json.dump(feature_cols, f)

    log.info("\n✅  Model training complete.")
    return rf, scaler, metrics


if __name__ == "__main__":
    df = load_training_data()
    rf, scaler, metrics = train(df)
    print(f"\nFinal AUC-ROC: {metrics['auc_roc']}")
    print(f"F1 Score     : {metrics['f1_score']}")
