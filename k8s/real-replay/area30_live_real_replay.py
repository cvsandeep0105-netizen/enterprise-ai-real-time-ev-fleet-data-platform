import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from kafka import KafkaProducer

INPUT_FILE = Path("/tmp/area30_real.ndjson")
BROKER = "evfleet-kafka:9092"
TOPIC = "ev.telemetry.v1"

rows = []
with INPUT_FILE.open("r", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if line:
            rows.append(json.loads(line))

if not rows:
    raise RuntimeError("Real replay payload is empty")

producer = KafkaProducer(
    bootstrap_servers=[BROKER],
    acks="all",
    retries=10,
    max_in_flight_requests_per_connection=1,
    enable_idempotence=True,
    compression_type="gzip",
    value_serializer=lambda value: json.dumps(
        value, separators=(",", ":")
    ).encode("utf-8"),
    key_serializer=lambda value: value.encode("utf-8"),
)

cycle = 0

while True:
    cycle_start = datetime.now(timezone.utc)

    for index, row in enumerate(rows):
        source_ts = datetime.fromisoformat(
            str(row["timestamp"]).replace("Z", "+00:00")
        )

        # Preserve the real observation values while advancing the
        # demonstration timeline. This makes each observation a
        # genuinely new telemetry event without fabricating sensor
        # values.
        demo_ts = cycle_start + timedelta(seconds=index)

        event = {
            "event_id": str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"TUMFTM-EV-UDS-LIVE|{cycle}|{index}|{row['vehicle_id']}|{source_ts.isoformat()}",
                )
            ),
            "event_type": "EV_TELEMETRY",
            "schema_version": "1.0",
            "producer": "tumftm-real-live-replay",
            "vehicle_id": row["vehicle_id"],
            "battery": float(row["battery"]),
            "temp": float(row["temp"]),
            "speed": float(row["speed"]),
            "location": None,
            "charging_status": "NOT_CHARGING",
            "timestamp": demo_ts.replace(tzinfo=None).isoformat(),
            "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        producer.send(
            TOPIC,
            key=event["vehicle_id"],
            value=event,
        ).get(timeout=15)

        time.sleep(1)

    producer.flush()
    cycle += 1
