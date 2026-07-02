"""
Kafka Consumer Simulation
=========================
Simulates a Kafka consumer that reads messages from the shared in-memory
queue (published by the producer) and writes micro-batches to the Bronze
layer in near-real-time.

In production this would use confluent-kafka or kafka-python to consume
from a real Kafka topic. Here we read from the local queue/JSONL log.

Usage (standalone demo):
    # Terminal 1:
    python kafka_simulation/producer.py --speed fast --limit 2000

    # Terminal 2:
    python kafka_simulation/consumer.py

Usage (combined demo):
    python kafka_simulation/consumer.py --demo
    # This launches both producer + consumer and shows live stats
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
from queue import Empty

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    BRONZE_DIR, KAFKA_TOPIC,
)
from kafka_simulation.producer import KAFKA_QUEUE, STREAM_LOG, run_producer_thread

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [KAFKA-CONSUMER] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

MICRO_BATCH_SIZE   = 100     # Rows per micro-batch write to Bronze
MICRO_BATCH_WAIT_S = 1.0     # Max wait before flushing a partial batch
CONSUMER_OUTPUT    = os.path.join(BRONZE_DIR, "streaming_ingest.parquet")


class VitalsConsumer:
    """Consumes from Kafka queue and writes micro-batches to Bronze."""

    def __init__(self, batch_size: int = MICRO_BATCH_SIZE):
        os.makedirs(BRONZE_DIR, exist_ok=True)
        self.batch_size   = batch_size
        self._stop        = threading.Event()
        self._total_read  = 0
        self._batches     = 0
        self._buffer: list = []
        self._all_rows: list = []

    def consume(self, max_messages: int = 0):
        """Poll the queue, accumulate micro-batches, flush to Parquet."""
        log.info(f"Consumer started — topic={KAFKA_TOPIC} "
                 f"batch_size={self.batch_size}")
        last_flush = time.time()

        while not self._stop.is_set():
            try:
                msg = KAFKA_QUEUE.get(timeout=0.5)
            except Empty:
                # Flush whatever we have if queue is empty
                if self._buffer and (time.time() - last_flush) > MICRO_BATCH_WAIT_S:
                    self._flush()
                    last_flush = time.time()
                # Check for termination
                if max_messages and self._total_read >= max_messages:
                    break
                continue

            # Extract vitals payload from envelope
            vitals_row = msg.get("value", {})
            vitals_row["_kafka_offset"]    = msg.get("offset")
            vitals_row["_kafka_partition"] = msg.get("partition")
            vitals_row["_consumed_at"]     = datetime.utcnow().isoformat()

            self._buffer.append(vitals_row)
            self._total_read += 1

            # Flush on batch size or time
            if (len(self._buffer) >= self.batch_size or
                    (time.time() - last_flush) > MICRO_BATCH_WAIT_S):
                self._flush()
                last_flush = time.time()

            if max_messages and self._total_read >= max_messages:
                break

        # Final flush
        if self._buffer:
            self._flush()

        log.info(f"Consumer finished — "
                 f"{self._total_read:,} messages, {self._batches} batches")
        self._save_final()

    def _flush(self):
        """Write current buffer as a micro-batch to Bronze."""
        if not self._buffer:
            return
        batch_df = pd.DataFrame(self._buffer)
        self._all_rows.extend(self._buffer)
        self._buffer.clear()
        self._batches += 1
        log.info(f"  Micro-batch {self._batches}: {len(batch_df)} rows "
                 f"(total: {self._total_read:,})")

    def _save_final(self):
        """Persist all consumed rows as a Bronze Parquet file."""
        if not self._all_rows:
            return
        df = pd.DataFrame(self._all_rows)
        df.to_parquet(CONSUMER_OUTPUT, index=False, engine="pyarrow")
        log.info(f"Saved {len(df):,} rows → {CONSUMER_OUTPUT}")

    def stop(self):
        self._stop.set()

    def get_stats(self) -> dict:
        return {
            "messages_consumed": self._total_read,
            "micro_batches":     self._batches,
            "queue_depth":       KAFKA_QUEUE.qsize(),
        }


def demo_mode(n_records: int = 2000):
    """Launch producer + consumer together for a live demonstration."""
    log.info(f"=== KAFKA SIMULATION DEMO — {n_records} records ===")

    # Start producer in background
    producer = run_producer_thread(speed="fast", limit=n_records)
    time.sleep(0.5)   # give producer a head start

    # Start consumer in foreground
    consumer = VitalsConsumer(batch_size=100)
    t = threading.Thread(target=consumer.consume, args=(n_records,), daemon=True)
    t.start()

    # Print live stats
    while t.is_alive():
        stats = consumer.get_stats()
        print(f"\r  Consumed: {stats['messages_consumed']:>6,} | "
              f"Batches: {stats['micro_batches']:>3} | "
              f"Queue: {stats['queue_depth']:>5}", end="", flush=True)
        time.sleep(0.25)

    t.join()
    print()
    log.info(f"Demo complete — see {CONSUMER_OUTPUT}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kafka Vitals Consumer Simulation")
    parser.add_argument("--demo",    action="store_true",
                        help="Run producer + consumer together")
    parser.add_argument("--records", type=int, default=2000,
                        help="Records to consume in demo mode")
    parser.add_argument("--batch",   type=int, default=MICRO_BATCH_SIZE,
                        help="Micro-batch size")
    args = parser.parse_args()

    if args.demo:
        demo_mode(n_records=args.records)
    else:
        consumer = VitalsConsumer(batch_size=args.batch)
        try:
            consumer.consume()
        except KeyboardInterrupt:
            consumer.stop()
            log.info(f"Stopped. Stats: {consumer.get_stats()}")
