"""
Kafka Producer Simulation
=========================
Simulates a Kafka producer that reads patient vitals from CSV files and
publishes them to a local queue (JSON file) at a configurable rate.

In production this would connect to a real Apache Kafka broker.
Here we simulate the streaming behavior using a thread-safe queue and
a JSON log file — so you can demonstrate real-time ingestion without
needing a running Kafka cluster.

Usage:
    python kafka_simulation/producer.py           # streams all records
    python kafka_simulation/producer.py --limit 500   # stream first 500
    python kafka_simulation/producer.py --speed fast  # no delay
"""

import os
import sys
import json
import time
import argparse
import logging
import threading
import pandas as pd
from datetime import datetime
from queue import Queue

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    RAW_DATA_DIR, KAFKA_TOPIC, KAFKA_STREAM_DELAY,
    NUM_SOURCE_FILES,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [KAFKA-PRODUCER] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Shared in-memory queue (replaces actual Kafka broker in simulation)
KAFKA_QUEUE: Queue = Queue(maxsize=10_000)

# Output log for visualising stream (written to kafka_simulation/)
STREAM_LOG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "stream_log.jsonl"
)


class VitalsProducer:
    """Simulates a Kafka producer publishing patient vitals."""

    def __init__(self, speed: str = "normal", limit: int = 0):
        self.speed  = speed
        self.limit  = limit           # 0 = no limit
        self.delay  = self._calc_delay(speed)
        self._stop  = threading.Event()
        self._count = 0

    @staticmethod
    def _calc_delay(speed: str) -> float:
        return {"fast": 0.0, "normal": 0.05, "slow": 0.2}.get(speed, 0.05)

    def _load_source(self) -> pd.DataFrame:
        frames = []
        for idx in range(NUM_SOURCE_FILES):
            path = os.path.join(RAW_DATA_DIR, f"hospital_deterioration_ml_ready_{idx}.csv")
            if os.path.exists(path):
                df = pd.read_csv(path)
                df["patient_id"] = f"P{idx:04d}"
                frames.append(df)
        if not frames:
            # Fallback: try vitals_stream.csv
            vs = os.path.join(RAW_DATA_DIR, "vitals_stream.csv")
            if os.path.exists(vs):
                return pd.read_csv(vs, nrows=self.limit or None)
            raise FileNotFoundError(f"No source data in {RAW_DATA_DIR}")
        combined = pd.concat(frames, ignore_index=True)
        if self.limit:
            combined = combined.head(self.limit)
        return combined

    def _make_message(self, row: dict, seq: int) -> dict:
        """Wrap a raw vitals row in a Kafka-style message envelope."""
        return {
            "topic":     KAFKA_TOPIC,
            "partition": seq % 4,           # simulate 4 partitions
            "offset":    seq,
            "timestamp": datetime.utcnow().isoformat(),
            "key":       row.get("patient_id", "unknown"),
            "value":     row,
        }

    def produce(self):
        """Stream vitals records into the shared queue and JSONL log."""
        log.info(f"Producer starting — topic={KAFKA_TOPIC} speed={self.speed}")
        df = self._load_source()
        log.info(f"Loaded {len(df):,} records to stream")

        open(STREAM_LOG, "w").close()    # truncate log

        with open(STREAM_LOG, "a") as logf:
            for i, (_, row) in enumerate(df.iterrows()):
                if self._stop.is_set():
                    break
                msg = self._make_message(row.to_dict(), i)
                KAFKA_QUEUE.put(msg)
                logf.write(json.dumps(msg) + "\n")
                self._count += 1

                if self._count % 500 == 0:
                    log.info(f"  Published {self._count:,} messages | "
                             f"Queue depth: {KAFKA_QUEUE.qsize()}")

                if self.delay:
                    time.sleep(self.delay)

        log.info(f"Producer finished — {self._count:,} messages published")

    def stop(self):
        self._stop.set()

    @property
    def messages_sent(self) -> int:
        return self._count


def run_producer_thread(speed: str = "normal", limit: int = 1000) -> VitalsProducer:
    """Start producer in a background thread (for use with consumer demo)."""
    producer = VitalsProducer(speed=speed, limit=limit)
    t = threading.Thread(target=producer.produce, daemon=True)
    t.start()
    return producer


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kafka Vitals Producer Simulation")
    parser.add_argument("--speed", choices=["fast","normal","slow"], default="normal")
    parser.add_argument("--limit", type=int, default=0, help="Max records to publish (0=all)")
    args = parser.parse_args()

    producer = VitalsProducer(speed=args.speed, limit=args.limit)
    try:
        producer.produce()
    except KeyboardInterrupt:
        log.info(f"Stopped. Published {producer.messages_sent:,} messages.")
