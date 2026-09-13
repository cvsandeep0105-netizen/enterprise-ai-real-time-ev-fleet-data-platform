import json
import uuid
from datetime import datetime, timezone

from kafka import KafkaProducer

INPUT_FILE = "/tmp/area30_real.ndjson"
BROKER = "evfleet-kafka:9092"
TOPIC = "ev.telemetry.v1"

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

count = 0

try:
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        for line in file:
            row = json.loads(line)

            vehicle_id = row["vehicle_id"]
            timestamp = row["timestamp"]

            event = {
                "event_id": str(
                    uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"TUMFTM-EV-UDS-CANONICAL|{vehicle_id}|{timestamp}",
                    )
                ),
                "event_type": "EV_TELEMETRY",
                "schema_version": "1.0",
                "producer": "tumftm-real-replay",
                "vehicle_id": vehicle_id,
                "battery": float(row["battery"]),
                "temp": float(row["temp"]),
                "speed": float(row["speed"]),
                "location": None,
                "charging_status": "NOT_CHARGING",
                "timestamp": timestamp,
                "ingestion_timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
            }

            result = producer.send(
                TOPIC,
                key=vehicle_id,
                value=event,
            ).get(timeout=15)

            count += 1

            print(
                f"{count:03d} | "
                f"{vehicle_id} | "
                f"partition={result.partition} | "
                f"offset={result.offset}"
            )

    producer.flush()

    print()
    print("=" * 60)
    print(f"REAL_KAFKA_EVENTS_PUBLISHED={count}")
    print("EVENT_CONTRACT=EV_TELEMETRY")
    print("REAL TUMFTM KAFKA PUBLISH=PASS")
    print("=" * 60)

finally:
    producer.close()

