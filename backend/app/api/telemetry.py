from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.telemetry import TelemetryEvent, TelemetryResponse
from app.kafka.producer import send_telemetry


router = APIRouter(
    prefix="/telemetry",
    tags=["Telemetry"],
)


def normalize_vehicle_status(
    status: str | None,
    speed: float,
) -> str:
    if status is None:
        return "STOPPED" if speed == 0 else "MOVING"

    normalized = str(status).strip().upper()

    mapping = {
        "RUNNING": "MOVING",
        "MOVING": "MOVING",
        "IDLE": "STOPPED",
        "STOPPED": "STOPPED",
        "MAINTENANCE": "MAINTENANCE",
    }

    return mapping.get(normalized, normalized)


def normalize_charging_status(
    status: str | bool | None,
) -> str:
    if status is None:
        return "NOT_CHARGING"

    if isinstance(status, bool):
        return "CHARGING" if status else "NOT_CHARGING"

    normalized = str(status).strip().upper()

    if normalized in {"TRUE", "YES", "1", "CHARGING"}:
        return "CHARGING"

    return "NOT_CHARGING"


def parse_timestamp(value) -> datetime:
    if isinstance(value, datetime):
        timestamp = value
    else:
        value = str(value).strip()

        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        timestamp = datetime.fromisoformat(value)

    if timestamp.tzinfo is not None:
        timestamp = timestamp.astimezone(
            timezone.utc
        ).replace(tzinfo=None)

    return timestamp


@router.post(
    "/",
    response_model=TelemetryResponse,
)
def receive_telemetry(
    data: dict,
    db: Session = Depends(get_db),
):
    """
    Receive telemetry from an external producer/simulator,
    normalize it into the canonical event contract, and
    publish it to Kafka.

    Persistence is handled downstream by the Kafka consumer.
    """

    raw_timestamp = data.get(
        "timestamp",
        data.get("event_timestamp"),
    )

    timestamp = parse_timestamp(
        raw_timestamp
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

    vehicle_status = normalize_vehicle_status(
        data.get(
            "vehicle_status",
            data.get("status"),
        ),
        speed,
    )

    charging_status = normalize_charging_status(
        data.get("charging_status")
    )

    event = TelemetryEvent(
        event_id=data.get(
            "event_id",
            str(uuid4()),
        ),
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
            "ev-telemetry-api",
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
        timestamp=timestamp,
        ingestion_timestamp=datetime.utcnow(),
        vehicle_status=vehicle_status,
        is_charging=(
            charging_status == "CHARGING"
        ),
    )

    send_telemetry(
        event.model_dump(mode="json")
    )

    return TelemetryResponse(
        message="Telemetry accepted and published to Kafka",
        event_id=event.event_id,
        vehicle_id=event.vehicle_id,
        timestamp=event.timestamp,
    )
