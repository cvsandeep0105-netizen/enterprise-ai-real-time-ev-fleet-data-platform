import sys
import uuid
import time

sys.path.insert(0, ".")

from kafka import KafkaConsumer, KafkaProducer
from app.core.config import settings
from app.schemas.telemetry import TelemetryEvent


BROKER = settings.kafka_broker
TOPIC = settings.kafka_topic
TEST_EVENT_ID = str(uuid.uuid4())
TEST_VEHICLE_ID = "AREA8-TEST-001"


def make_consumer():
    return KafkaConsumer(
        TOPIC,
        bootstrap_servers=BROKER,
        group_id=f"area8-final-{uuid.uuid4()}",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        consumer_timeout_ms=15000,
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        value_deserializer=lambda v: __import__("json").loads(v.decode("utf-8")),
    )


def make_producer():
    import json
    return KafkaProducer(
        bootstrap_servers=BROKER,
        acks="all",
        key_serializer=lambda k: k.encode("utf-8"),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )


print("=" * 60)
print("AREA 8 FINAL KAFKA INTEGRATION")
print("=" * 60)

print("STEP 1 - CANONICAL SCHEMA")

event = TelemetryEvent(
    event_id=TEST_EVENT_ID,
    event_type="EV_TELEMETRY",
    schema_version="1.0",
    producer="area8-final-test",
    vehicle_id=TEST_VEHICLE_ID,
    battery=80,
    temp=30,
    speed=50,
    location="Bangalore",
    charging_status="NOT_CHARGING",
    timestamp="2026-08-29T00:00:00+00:00",
    ingestion_timestamp="2026-08-29T00:00:01+00:00",
)

canonical = event.model_dump(mode="json")

assert canonical["event_id"] == TEST_EVENT_ID
assert canonical["event_type"] == "EV_TELEMETRY"
assert canonical["schema_version"] == "1.0"

print("SCHEMA_VALIDATION=PASS")
print("CANONICALIZATION=PASS")

print("STEP 2 - KAFKA CONSUMER ASSIGNMENT")

consumer = make_consumer()

deadline = time.time() + 10
while not consumer.assignment() and time.time() < deadline:
    consumer.poll(timeout_ms=500)

assert consumer.assignment(), "Consumer partition assignment failed"

print("CONSUMER_CREATED=PASS")
print("CONSUMER_ASSIGNMENT=PASS")

print("STEP 3 - KAFKA PUBLISH")

producer = make_producer()

metadata = producer.send(
    TOPIC,
    key=TEST_VEHICLE_ID,
    value=canonical,
).get(timeout=30)

producer.flush(timeout=30)
producer.close()

print("KAFKA_PUBLISH=PASS")
print(f"TOPIC={metadata.topic}")
print(f"PARTITION={metadata.partition}")
print(f"OFFSET={metadata.offset}")

print("STEP 4 - KAFKA CONSUME")

received = None
deadline = time.time() + 20

while time.time() < deadline:
    records = consumer.poll(timeout_ms=2000)

    for _, messages in records.items():
        for message in messages:
            if message.value.get("event_id") == TEST_EVENT_ID:
                received = message
                break

        if received:
            break

    if received:
        break

if not received:
    consumer.close()
    raise RuntimeError("AREA 8 test event was not received from Kafka")

assert received.value["event_id"] == TEST_EVENT_ID
assert received.value["vehicle_id"] == TEST_VEHICLE_ID
assert received.value["schema_version"] == "1.0"
assert received.value["event_type"] == "EV_TELEMETRY"

print("KAFKA_CONSUME=PASS")
print(f"RECEIVED_EVENT_ID={received.value['event_id']}")
print(f"RECEIVED_PARTITION={received.partition}")
print(f"RECEIVED_OFFSET={received.offset}")

consumer.close()

print("STEP 5 - FINAL CONTRACT")

assert canonical == received.value

print("END_TO_END_SCHEMA_CONTRACT=PASS")
print("CANONICAL_EVENT_PRESERVED=PASS")
print("KAFKA_ROUND_TRIP=PASS")

print("=" * 60)
print("AREA 8 FINAL INTEGRATION = PASS")
print("AREA 8 = 100% COMPLETE")
print("=" * 60)
