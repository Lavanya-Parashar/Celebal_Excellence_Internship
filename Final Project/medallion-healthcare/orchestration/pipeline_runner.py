"""
Pipeline Orchestrator — Full End-to-End Run
============================================
Simulates Azure Data Factory (ADF) orchestration by running the full
Medallion pipeline in sequence:

  Step 1 → Data Preparation   (data/prepare_datasets.py)
  Step 2 → Bronze Ingestion   (pipeline/bronze_layer.py)
  Step 3 → Silver Transform   (pipeline/silver_layer.py)
  Step 4 → ML Model Training  (ml/train_model.py)         [optional]
  Step 5 → Gold Reporting     (pipeline/gold_layer.py)

Each step is timed, logged, and its output is validated before the next
step begins — just as a real ADF pipeline would use activity dependencies.

Usage:
    python orchestration/pipeline_runner.py
    python orchestration/pipeline_runner.py --skip-train   # skip ML retraining
    python orchestration/pipeline_runner.py --step bronze  # run one step only
"""

import os
import sys
import json
import time
import logging
import argparse
import traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    RAW_DATA_DIR, BRONZE_DIR, SILVER_DIR, GOLD_DIR,
    BRONZE_VITALS_PATH, SILVER_VITALS_PATH,
    GOLD_RISK_SCORES_PATH, MODEL_DIR,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ORCHESTRATOR] %(levelname)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

RUN_LOG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "pipeline_run_log.json"
)


class PipelineOrchestrator:
    """
    Simulates Azure Data Factory orchestration of the Medallion pipeline.
    Each activity is timed and its status logged to pipeline_run_log.json.
    """

    def __init__(self, skip_train: bool = False):
        self.skip_train = skip_train
        self.run_id     = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.activities: list = []
        self.start_time = None

    # ── Public API ────────────────────────────────────────────────────────────

    def run(self, step: str = "all") -> bool:
        self.start_time = time.time()
        log.info("=" * 65)
        log.info(f"  MEDALLION HEALTHCARE PIPELINE  |  Run ID: {self.run_id}")
        log.info("=" * 65)

        success = True
        try:
            if step in ("all", "prepare"):
                success = self._run_activity("Data Preparation",    self._prepare_data)
            if success and step in ("all", "bronze"):
                success = self._run_activity("Bronze Ingestion",    self._bronze)
            if success and step in ("all", "silver"):
                success = self._run_activity("Silver Transform",    self._silver)
            if success and not self.skip_train and step in ("all", "train"):
                success = self._run_activity("ML Model Training",   self._train_model)
            if success and step in ("all", "gold"):
                success = self._run_activity("Gold Reporting",      self._gold)
        except Exception as e:
            log.error(f"Pipeline failed: {e}")
            traceback.print_exc()
            success = False

        self._print_summary(success)
        self._save_run_log(success)
        return success

    # ── Activity Wrappers ─────────────────────────────────────────────────────

    def _run_activity(self, name: str, fn) -> bool:
        log.info(f"\n{'─'*55}")
        log.info(f"  Activity: {name}")
        log.info(f"{'─'*55}")
        t0 = time.time()
        status = "SUCCESS"
        error  = None
        try:
            fn()
        except Exception as e:
            status = "FAILED"
            error  = str(e)
            log.error(f"  ✖ {name} FAILED: {e}")
            traceback.print_exc()
        elapsed = round(time.time() - t0, 2)
        log.info(f"  ⏱  {name} → {status} ({elapsed}s)")
        self.activities.append({
            "activity": name, "status": status,
            "duration_s": elapsed, "error": error,
        })
        return status == "SUCCESS"

    # ── Pipeline Steps ────────────────────────────────────────────────────────

    def _prepare_data(self):
        """Step 1: Generate all 5 source datasets from raw CSVs."""
        vitals_path = os.path.join(RAW_DATA_DIR, "vitals_stream.csv")
        if os.path.exists(vitals_path):
            import pandas as pd
            n = sum(1 for _ in open(vitals_path)) - 1
            log.info(f"  Source datasets already exist ({n:,} vitals rows) — skipping prep")
            return

        # Run prepare_datasets.py as a module
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
        import importlib.util, pathlib
        spec = importlib.util.spec_from_file_location(
            "prepare_datasets",
            pathlib.Path(__file__).parent.parent / "data" / "prepare_datasets.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()

    def _bronze(self):
        """Step 2: Bronze ingestion."""
        from pipeline.bronze_layer import BronzeLayer
        bl     = BronzeLayer()
        counts = bl.run()
        total  = sum(counts.values())
        log.info(f"  Bronze: {total:,} total rows ingested")
        self._validate_file(BRONZE_VITALS_PATH, "Bronze vitals Parquet")

    def _silver(self):
        """Step 3: Silver transformation."""
        self._validate_file(BRONZE_VITALS_PATH, "Bronze vitals (pre-Silver)")
        from pipeline.silver_layer import SilverLayer
        sl = SilverLayer()
        df = sl.run()
        log.info(f"  Silver: {len(df):,} clean rows")
        self._validate_file(SILVER_VITALS_PATH, "Silver vitals Parquet")

    def _train_model(self):
        """Step 4: ML model training."""
        self._validate_file(SILVER_VITALS_PATH, "Silver vitals (pre-ML)")
        model_path = os.path.join(MODEL_DIR, "deterioration_rf_model.joblib")
        if os.path.exists(model_path):
            log.info("  Trained model already exists — skipping re-train")
            log.info("  (Delete ml/model/ to force re-training)")
            return
        from ml.train_model import load_training_data, train
        df = load_training_data()
        _, _, metrics = train(df)
        log.info(f"  Model trained | AUC-ROC={metrics['auc_roc']} "
                 f"F1={metrics['f1_score']}")

    def _gold(self):
        """Step 5: Gold layer reports."""
        self._validate_file(SILVER_VITALS_PATH, "Silver vitals (pre-Gold)")
        from pipeline.gold_layer import GoldLayer
        gl      = GoldLayer()
        reports = gl.run()
        for name, df in reports.items():
            log.info(f"  Gold report '{name}': {len(df):,} rows")

    # ── Validation ────────────────────────────────────────────────────────────

    @staticmethod
    def _validate_file(path: str, label: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Expected output not found: {label} → {path}")
        size_kb = os.path.getsize(path) / 1024
        log.info(f"  ✔ Validated: {label} ({size_kb:.0f} KB)")

    # ── Reporting ─────────────────────────────────────────────────────────────

    def _print_summary(self, success: bool):
        elapsed = round(time.time() - self.start_time, 2)
        log.info("\n" + "=" * 65)
        log.info(f"  PIPELINE {'COMPLETED' if success else 'FAILED'}  |  "
                 f"Run ID: {self.run_id}  |  Total: {elapsed}s")
        log.info("=" * 65)
        for a in self.activities:
            icon = "✔" if a["status"] == "SUCCESS" else "✖"
            log.info(f"  {icon} {a['activity']:<30} {a['status']:<10} {a['duration_s']}s")
        log.info("=" * 65)

    def _save_run_log(self, success: bool):
        log_entry = {
            "run_id":     self.run_id,
            "status":     "SUCCESS" if success else "FAILED",
            "start_time": datetime.utcnow().isoformat(),
            "duration_s": round(time.time() - self.start_time, 2),
            "activities": self.activities,
        }
        history = []
        if os.path.exists(RUN_LOG_PATH):
            with open(RUN_LOG_PATH) as f:
                history = json.load(f)
        history.append(log_entry)
        with open(RUN_LOG_PATH, "w") as f:
            json.dump(history[-20:], f, indent=2)   # keep last 20 runs
        log.info(f"Run log saved → {RUN_LOG_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Medallion Healthcare Pipeline Runner")
    parser.add_argument(
        "--step",
        choices=["all", "prepare", "bronze", "silver", "train", "gold"],
        default="all",
        help="Which pipeline step to run (default: all)",
    )
    parser.add_argument(
        "--skip-train", action="store_true",
        help="Skip ML model re-training (use existing model if present)",
    )
    args = parser.parse_args()

    orchestrator = PipelineOrchestrator(skip_train=args.skip_train)
    ok = orchestrator.run(step=args.step)
    sys.exit(0 if ok else 1)
