"""
EV Fleet Data Platform
Production Kafka Telemetry Producer

Flow:

EV Fleet Simulator
        ↓
Kafka Producer
        ↓
ev.telemetry.v1

Kafka key = vehicle_id

Architecture principles:
- Centralized configuration
- Lazy Kafka producer initialization
- Idempotent publishing
- Acknowledgement from all replicas
- Compression and batching
- Graceful shutdown
- Application-facing send_telemetry() contract
"""

import json
import logging
import random
import signal
import time
import uuid
from datetime import datetime, timezone

from kafka import KafkaProducer
from kafka.errors import KafkaError

from app.core.config import settings
from app.schemas.telemetry import TelemetryEvent


# ============================================================
# CONFIGURATION
# ============================================================

KAFKA_BROKER = settings.kafka_broker
KAFKA_TOPIC = settings.kafka_topic
PRODUCER_NAME = "ev-telemetry-producer"
SCHEMA_VERSION = "1.0"

PRODUCER_INTERVAL_SECONDS = (
    settings.producer_interval_seconds
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)

logger = logging.getLogger(
    "ev-telemetry-producer"
)


# ============================================================
# FLEET CONFIGURATION
# ============================================================

VEHICLES = [
    "EV001",
    "EV002",
    "EV003",
    "EV004",
    "EV005",
]

LOCATIONS = [
    "Bangalore",
    "Hyderabad",
    "Chennai",
    "Mumbai",
    "Delhi",
]


# ============================================================
# KAFKA PRODUCER LIFECYCLE
# ============================================================

_producer = None


def get_producer() -> KafkaProducer:
    """
    Lazily create and return the Kafka producer.

    The producer is intentionally NOT created when this
    module is imported.

    This keeps application imports independent from Kafka
    availability.
    """

    global _producer

    if _producer is None:

        _producer = KafkaProducer(

            bootstrap_servers=KAFKA_BROKER,

            value_serializer=lambda value:
                json.dumps(
                    value,
                    separators=(",", ":"),
                ).encode("utf-8"),

            key_serializer=lambda key:
                key.encode("utf-8"),

            # ------------------------------------------------
            # Reliability
            # ------------------------------------------------

            acks="all",

            retries=10,

            retry_backoff_ms=500,

            request_timeout_ms=30000,

            delivery_timeout_ms=120000,

            enable_idempotence=True,
            max_in_flight_requests_per_connection=1,
            # Ordering
            # ------------------------------------------------

            # ------------------------------------------------
            # Batching
            # ------------------------------------------------

            linger_ms=10,

            batch_size=32768,

            compression_type="gzip",
        )

        logger.info(
            "Kafka producer initialized | "
            "broker=%s | topic=%s",
            KAFKA_BROKER,
            KAFKA_TOPIC,
        )

    return _producer


def close_producer() -> None:
    """
    Flush pending messages and close the Kafka producer
    gracefully.
    """

    global _producer

    if _producer is None:
        return

    try:

        logger.info(
            "Flushing Kafka producer..."
        )

        _producer.flush(
            timeout=30
        )

    except Exception:

        logger.exception(
            "Kafka producer flush failed."
        )

    finally:

        try:

            _producer.close(
                timeout=30
            )

        except Exception:

            logger.exception(
                "Kafka producer close failed."
            )

        finally:

            _producer = None

            logger.info(
                "Kafka producer closed."
            )


# ============================================================
# EVENT CREATION
# ============================================================

def create_telemetry_event(
    vehicle_id: str,
) -> dict:
    """
    Create one canonical EV telemetry event.
    """

    event_timestamp = datetime.now(
        timezone.utc
    )

    ingestion_timestamp = datetime.now(
        timezone.utc
    )

    battery = random.randint(
        5,
        100,
    )

    temperature = random.randint(
        20,
        80,
    )

    speed = random.randint(
        0,
        120,
    )

    charging = (
        random.random()
        < 0.20
    )

    charging_status = (
        "CHARGING"
        if charging
        else "NOT_CHARGING"
    )

    return {

        # ----------------------------------------------------
        # Event identity
        # ----------------------------------------------------

        "event_id": str(
            uuid.uuid4()
        ),

        "event_type": "EV_TELEMETRY",

        "schema_version": SCHEMA_VERSION,

        # ----------------------------------------------------
        # Producer metadata
        # ----------------------------------------------------

        "producer": PRODUCER_NAME,

        # ----------------------------------------------------
        # Vehicle telemetry
        # ----------------------------------------------------

        "vehicle_id": vehicle_id,

        "battery": battery,

        "temp": temperature,

        "speed": speed,

        "location": random.choice(
            LOCATIONS
        ),

        "charging_status": charging_status,

        # ----------------------------------------------------
        # Event timestamps
        # ----------------------------------------------------

        "event_timestamp": (
            event_timestamp.isoformat()
        ),

        "ingestion_timestamp": (
            ingestion_timestamp.isoformat()
        ),
    }


# ============================================================
# PUBLISH EVENT
# ============================================================

def publish_event(
    event: dict,
) -> None:
    """
    Publish one telemetry event to Kafka.

    Kafka key = vehicle_id.

    Using vehicle_id as the key guarantees that events for
    the same vehicle are routed consistently to the same
    partition under normal Kafka partitioning behavior.
    """

    # --------------------------------------------------------
    # Schema governance
    # --------------------------------------------------------
    # Validate every event before publishing to Kafka.
    # The canonical model also normalizes legacy
    # event_timestamp input into timestamp.
    validated_event = TelemetryEvent.model_validate(event)
    canonical_event = validated_event.model_dump(mode="json")

    vehicle_id = validated_event.vehicle_id

    try:

        kafka_producer = get_producer()

        future = kafka_producer.send(

            KAFKA_TOPIC,

            key=vehicle_id,

            value=canonical_event,
        )

        metadata = future.get(
            timeout=30
        )

        logger.info(
            "EVENT_PUBLISHED | "
            "event_id=%s | "
            "vehicle_id=%s | "
            "topic=%s | "
            "partition=%s | "
            "offset=%s",
            event["event_id"],
            vehicle_id,
            metadata.topic,
            metadata.partition,
            metadata.offset,
        )

    except KafkaError:

        logger.exception(
            "KAFKA_PUBLISH_FAILED | "
            "event_id=%s | "
            "vehicle_id=%s | "
            "topic=%s",
            event.get("event_id"),
            vehicle_id,
            KAFKA_TOPIC,
        )

        raise

    except Exception:

        logger.exception(
            "TELEMETRY_PUBLISH_FAILED | "
            "event_id=%s | "
            "vehicle_id=%s",
            event.get("event_id"),
            vehicle_id,
        )

        raise


# ============================================================
# APPLICATION-FACING PRODUCER CONTRACT
# ============================================================

def send_telemetry(
    event: dict,
) -> None:
    """
    Application-facing Kafka producer contract.

    API/services should call this function instead of
    directly interacting with KafkaProducer.
    """

    publish_event(event)


# ============================================================
# GRACEFUL SHUTDOWN
# ============================================================

running = True


def shutdown(
    signum,
    frame,
) -> None:

    global running

    logger.info(
        "Shutdown signal received."
    )

    running = False


signal.signal(
    signal.SIGINT,
    shutdown,
)

signal.signal(
    signal.SIGTERM,
    shutdown,
)


# ============================================================
# MAIN
# ============================================================

def main():

    logger.info("=" * 70)

    logger.info(
        "EV FLEET KAFKA PRODUCER STARTED"
    )

    logger.info(
        "Broker: %s",
        KAFKA_BROKER,
    )

    logger.info(
        "Topic: %s",
        KAFKA_TOPIC,
    )

    logger.info(
        "Schema Version: %s",
        SCHEMA_VERSION,
    )

    logger.info(
        "Producer: %s",
        PRODUCER_NAME,
    )

    logger.info(
        "Interval: %s seconds",
        PRODUCER_INTERVAL_SECONDS,
    )

    logger.info("=" * 70)

    try:

        while running:

            vehicle_id = random.choice(
                VEHICLES
            )

            event = create_telemetry_event(
                vehicle_id
            )

            publish_event(
                event
            )

            time.sleep(
                PRODUCER_INTERVAL_SECONDS
            )

    except KeyboardInterrupt:

        logger.info(
            "Producer interrupted."
        )

    finally:

        close_producer()

        logger.info(
            "EV Fleet Kafka Producer stopped."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()