from sqlalchemy.orm import Session

from app.models.database_models import Telemetry


def save_telemetry(
    db: Session,
    data: dict,
) -> Telemetry:
    """
    Persist a normalized canonical telemetry event.

    The Kafka consumer is responsible for validation and
    normalization. This service maps the canonical event
    contract directly into the canonical ORM model.

    Transaction ownership remains with the caller.
    """

    telemetry = Telemetry(
        event_id=data["event_id"],
        event_type=data["event_type"],
        schema_version=data["schema_version"],
        producer=data["producer"],
        vehicle_id=data["vehicle_id"],
        battery=float(data["battery"]),
        temp=float(data["temp"]),
        speed=float(data["speed"]),
        location=data.get("location"),
        charging_status=data.get("charging_status"),
        timestamp=data["timestamp"],
        ingestion_timestamp=data.get(
            "ingestion_timestamp"
        ),
        battery_status=data.get(
            "battery_status"
        ),
        vehicle_status=data.get(
            "vehicle_status"
        ),
        temperature_status=data.get(
            "temperature_status"
        ),
        is_charging=data.get(
            "is_charging"
        ),
    )

    db.add(telemetry)
    db.flush()

    return telemetry
