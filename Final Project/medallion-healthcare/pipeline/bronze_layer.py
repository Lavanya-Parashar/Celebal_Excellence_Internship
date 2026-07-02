"""
Bronze Layer — Raw Data Ingestion
==================================
Reads source CSV files and writes them as Parquet files (simulating Delta Lake
tables). No transformations are applied — data lands exactly as received.

Key Bronze principles:
  • Full audit trail — every record stamped with ingest_ts
  • No cleaning, no filtering, no type coercion
  • ACID-safe writes via atomic rename (simulates Delta ACID transactions)
  • Supports full historical replay if downstream logic changes

Usage:
    from pipeline.bronze_layer import BronzeLayer
    bl = BronzeLayer()
    bl.run()
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    RAW_DATA_DIR, BRONZE_DIR,
    BRONZE_VITALS_PATH, BRONZE_REGISTRY_PATH,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [BRONZE] %(levelname)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


class BronzeLayer:
    """Ingests raw source datasets into the Bronze Delta-Lake-equivalent layer."""

    def __init__(self):
        os.makedirs(BRONZE_DIR, exist_ok=True)
        self.ingest_timestamp = datetime.utcnow().isoformat()

    # ── Public API ───────────────────────────────────────────────────────────

    def run(self) -> dict:
        """Run full Bronze ingestion. Returns row counts per table."""
        log.info("Starting Bronze layer ingestion …")
        counts = {}
        counts["vitals"]       = self._ingest_vitals()
        counts["registry"]     = self._ingest_registry()
        counts["alerts"]       = self._ingest_raw_table("alert_events.csv",   "alert_events_raw")
        counts["icu"]          = self._ingest_raw_table("icu_capacity.csv",    "icu_capacity_raw")
        counts["interventions"]= self._ingest_raw_table("interventions.csv",   "interventions_raw")
        total = sum(counts.values())
        log.info(f"Bronze ingestion complete — {total:,} total rows across {len(counts)} tables")
        return counts

    # ── Private helpers ──────────────────────────────────────────────────────

    def _add_audit_cols(self, df: pd.DataFrame) -> pd.DataFrame:
        """Stamp every row with Bronze ingestion metadata."""
        df = df.copy()
        df["_bronze_ingest_ts"]  = self.ingest_timestamp
        df["_bronze_source"]     = "csv_raw"
        df["_bronze_layer"]      = "BRONZE"
        return df

    def _safe_write(self, df: pd.DataFrame, out_path: str, table_name: str) -> int:
        """Write Parquet atomically (temp file → rename) to simulate Delta write."""
        tmp_path = out_path + ".tmp"
        df.to_parquet(tmp_path, index=False, engine="pyarrow")
        os.replace(tmp_path, out_path)
        log.info(f"  ✔ {table_name}: {len(df):,} rows → {os.path.basename(out_path)}")
        return len(df)

    def _ingest_vitals(self) -> int:
        """Load vitals_stream.csv and persist as Bronze Parquet."""
        path = os.path.join(RAW_DATA_DIR, "vitals_stream.csv")
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"vitals_stream.csv not found in {RAW_DATA_DIR}. "
                "Run `python data/prepare_datasets.py` first."
            )
        df = pd.read_csv(path, parse_dates=["timestamp", "ingest_ts"])
        df = self._add_audit_cols(df)
        return self._safe_write(df, BRONZE_VITALS_PATH, "vitals_raw")

    def _ingest_registry(self) -> int:
        """Load patient_registry.csv and persist as Bronze Parquet."""
        path = os.path.join(RAW_DATA_DIR, "patient_registry.csv")
        df = pd.read_csv(path, parse_dates=["admission_date"])
        df = self._add_audit_cols(df)
        return self._safe_write(df, BRONZE_REGISTRY_PATH, "patient_registry_raw")

    def _ingest_raw_table(self, csv_name: str, table_name: str) -> int:
        """Generic ingestion for ancillary CSV tables."""
        path = os.path.join(RAW_DATA_DIR, csv_name)
        df = pd.read_csv(path)
        df = self._add_audit_cols(df)
        out_path = os.path.join(BRONZE_DIR, f"{table_name}.parquet")
        return self._safe_write(df, out_path, table_name)

    # ── Utility / reporting ──────────────────────────────────────────────────

    @staticmethod
    def get_stats() -> pd.DataFrame:
        """Return a summary of all Bronze Parquet files (row counts, sizes)."""
        rows = []
        for fname in os.listdir(BRONZE_DIR):
            if fname.endswith(".parquet"):
                fpath = os.path.join(BRONZE_DIR, fname)
                df = pd.read_parquet(fpath)
                rows.append({
                    "table":     fname.replace(".parquet", ""),
                    "rows":      len(df),
                    "columns":   len(df.columns),
                    "size_kb":   round(os.path.getsize(fpath) / 1024, 1),
                })
        return pd.DataFrame(rows)


if __name__ == "__main__":
    bl = BronzeLayer()
    counts = bl.run()
    print("\nBronze layer stats:")
    print(BronzeLayer.get_stats().to_string(index=False))
