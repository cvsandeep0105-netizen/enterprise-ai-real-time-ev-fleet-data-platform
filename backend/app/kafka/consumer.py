import json
import time
from datetime import datetime

from kafka import KafkaConsumer
from kafka.errors import KafkaError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.database.database import SessionLocal
from app.schemas.telemetry import TelemetryEvent
from app.services.telemetry_service import save_telemetry
from app.services.alert_service import process_telemetry_alerts


KAFKA_BROKER = settings.kafka_broker
TOPIC = settings.kafka_topic
CONSUMER_GROUP = "ev-fleet-consumer-v1"

MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1

# Area 7 ? Kafka Reliability Configuration
MAX_POLL_RECORDS = 100
SESSION_TIMEOUT_MS = 30000
HEARTBEAT_INTERVAL_MS = 10000
MAX_POLL_INTERVAL_MS = 300000
REQUEST_TIMEOUT_MS = 60000
RECONNECT_BACKOFF_MS = 1000


def parse_timestamp(value):
    if isinstance(value, datetime):
        return value

    value = str(value).strip()

    if value.endswith("Z"):
        value = value[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.strptime(
            value,
            "%Y-%m-%d %H:%M:%S",
        )


def normalize_telemetry(data):
    event_timestamp = data.get(
        "event_timestamp",
        data.get("timestamp"),
    )

    temperature = data.get(
        "temp",
        data.get("temperature"),
    )

    if temperature is None:
        raise ValueError(
            "Telemetry requires temp or temperature"
        )

    speed = float(data["speed"])
    battery = float(data["battery"])

    vehicle_status = data.get(
        "vehicle_status",
        data.get("status"),
    )

    if vehicle_status is None:
        vehicle_status = (
            "STOPPED"
            if speed == 0
            else "MOVING"
        )

    vehicle_status = str(
        vehicle_status
    ).strip().upper()

    vehicle_status = {
        "RUNNING": "MOVING",
        "MOVING": "MOVING",
        "IDLE": "STOPPED",
        "STOPPED": "STOPPED",
        "MAINTENANCE": "MAINTENANCE",
    }.get(
        vehicle_status,
        vehicle_status,
    )

    charging_status = data.get(
        "charging_status"
    )

    if charging_status is None:
        charging_status = "NOT_CHARGING"
    elif isinstance(charging_status, bool):
        charging_status = (
            "CHARGING"
            if charging_status
            else "NOT_CHARGING"
        )
    else:
        charging_status = str(
            charging_status
        ).strip().upper()

        charging_status = (
            "CHARGING"
            if charging_status in {
                "TRUE",
                "YES",
                "1",
                "CHARGING",
            }
            else "NOT_CHARGING"
        )

    event = TelemetryEvent(
        event_id=data["event_id"],
        event_type=data.get(
            "event_type",
            "EV_TELEMETRY",
        ),
        schema_version=data.get(
            "schema_version",
            "1.0",
        ),
        producer=data.get(
            "producer",
            "ev-telemetry-producer",
        ),
        vehicle_id=data["vehicle_id"],
        battery=battery,
        temp=float(temperature),
        speed=speed,
        location=data.get(
            "location",
            data.get("city"),
        ),
        charging_status=charging_status,
        timestamp=parse_timestamp(
            event_timestamp
        ),
        ingestion_timestamp=(
            parse_timestamp(
                data["ingestion_timestamp"]
            )
            if data.get("ingestion_timestamp")
            else None
        ),
        vehicle_status=vehicle_status,
        is_charging=(
            charging_status == "CHARGING"
        ),
    )

    return event


def create_consumer() -> KafkaConsumer:
    """
    Create the Kafka consumer only when the
    consumer application explicitly starts.

    Importing this module does NOT connect to Kafka.
    """

    return KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        enable_auto_commit=False,
        auto_offset_reset="latest",
        group_id=CONSUMER_GROUP,
        max_poll_records=MAX_POLL_RECORDS,
        session_timeout_ms=SESSION_TIMEOUT_MS,
        heartbeat_interval_ms=HEARTBEAT_INTERVAL_MS,
        max_poll_interval_ms=MAX_POLL_INTERVAL_MS,
        request_timeout_ms=REQUEST_TIMEOUT_MS,
        reconnect_backoff_ms=RECONNECT_BACKOFF_MS,
        reconnect_backoff_max_ms=10000,
        value_deserializer=lambda value:
            json.loads(
                value.decode("utf-8")
            ),
        key_deserializer=lambda key:
            key.decode("utf-8")
            if key is not None
            else None,
    )


def process_message(
    consumer,
    message,
):
    raw_data = message.value

    vehicle_id = raw_data.get(
        "vehicle_id",
        "UNKNOWN",
    )

    event_id = raw_data.get(
        "event_id",
        "UNKNOWN",
    )

    print(
        f"Processing -> "
        f"{vehicle_id} | "
        f"Event: {event_id} | "
        f"Partition: {message.partition} | "
        f"Offset: {message.offset}"
    )

    try:
        event = normalize_telemetry(
            raw_data
        )
    except Exception as error:
        print(
            f"Invalid telemetry -> "
            f"{vehicle_id} | {error}"
        )

        consumer.commit()
        return

    stored = False

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):
        db = None

        try:
            print(
                f"Database attempt "
                f"{attempt}/{MAX_RETRIES} -> "
                f"{vehicle_id}"
            )

            db = SessionLocal()

            save_telemetry(
                db,
                event.model_dump(),
            )

            process_telemetry_alerts(
                db,
                event,
            )

            # Commit telemetry + alert changes as one
            # database transaction before acknowledging
            # the Kafka message.
            db.commit()

            stored = True
            break

        except SQLAlchemyError as error:
            error_text = str(error)

            # Area 6.6 â€” Idempotent duplicate-event handling.
            # A previously committed event is already successfully persisted.
            if (
                "UniqueViolation" in error_text
                or "duplicate key value violates unique constraint" in error_text
                or "ix_ev_data_event_id" in error_text
            ):
                print(
                    f"Duplicate event already persisted -> "
                    f"{vehicle_id} | Event: {event_id}"
                )

                if db:
                    db.rollback()

                stored = True
                break

            print(
                f"Database failure -> "
                f"{vehicle_id} | "
                f"Attempt {attempt}/{MAX_RETRIES} | "
                f"{error}"
            )

            if db:
                db.rollback()

            if attempt < MAX_RETRIES:
                delay = (
                    INITIAL_RETRY_DELAY
                    * (2 ** (attempt - 1))
                )

                print(
                    f"Retrying in "
                    f"{delay} second(s)..."
                )

                time.sleep(delay)
        except Exception as error:
            print(
                f"Processing failure -> "
                f"{vehicle_id} | "
                f"{error}"
            )

            if db:
                db.rollback()

            break

        finally:
            if db:
                db.close()

    if stored:
        consumer.commit()

        print(
            f"Kafka commit successful -> "
            f"{vehicle_id} | "
            f"Event: {event_id} | "
            f"Offset: {message.offset}"
        )

    else:
        print(
            f"Message not committed -> "
            f"{vehicle_id} | "
            f"Offset: {message.offset}"
        )


def run_consumer():
    print("=" * 70)
    print("EV FLEET KAFKA CONSUMER")
    print("=" * 70)
    print(f"Kafka Broker   : {KAFKA_BROKER}")
    print(f"Kafka Topic    : {TOPIC}")
    print(f"Consumer Group : {CONSUMER_GROUP}")
    print("Pipeline       : Kafka -> PostgreSQL -> Alerts")
    print("Offset Mode    : Manual")
    print("Reliability    : Retry + Reconnect + Manual Commit")
    print("=" * 70)

    consumer = None
    reconnect_delay = INITIAL_RETRY_DELAY

    try:
        while True:
            try:
                if consumer is None:
                    print("Kafka connection -> establishing...")

                    consumer = create_consumer()

                    print("Kafka connection -> established")

                    reconnect_delay = INITIAL_RETRY_DELAY

                for message in consumer:
                    process_message(
                        consumer,
                        message,
                    )

            except KeyboardInterrupt:
                print("\nConsumer shutdown requested.")
                break

            except KafkaError as error:
                print(
                    f"Kafka transport failure -> {error}"
                )

            except Exception as error:
                print(
                    f"Unexpected consumer failure -> {error}"
                )

            finally:
                if consumer is not None:
                    try:
                        consumer.close(
                            autocommit=False
                        )
                    except Exception as close_error:
                        print(
                            f"Kafka consumer close warning -> "
                            f"{close_error}"
                        )

                    consumer = None

            if consumer is None:
                print(
                    f"Kafka reconnecting in "
                    f"{reconnect_delay} second(s)..."
                )

                time.sleep(reconnect_delay)

                reconnect_delay = min(
                    reconnect_delay * 2,
                    30,
                )

    finally:
        if consumer is not None:
            try:
                consumer.close(
                    autocommit=False
                )
            except Exception:
                pass

        print("Kafka consumer closed.")


if __name__ == "__main__":
    run_consumer()


