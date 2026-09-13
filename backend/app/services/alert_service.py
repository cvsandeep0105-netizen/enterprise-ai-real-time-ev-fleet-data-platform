from sqlalchemy.orm import Session

from app.models.database_models import Alert
from app.schemas.telemetry import TelemetryEvent


def create_alert(
    db: Session,
    vehicle_id: str,
    alert_type: str,
    alert_value: float,
    severity: str,
    message: str,
    timestamp,
):
    """
    Create an ACTIVE alert only when an equivalent ACTIVE
    alert does not already exist.
    """

    existing = (
        db.query(Alert)
        .filter(
            Alert.vehicle_id == vehicle_id,
            Alert.alert_type == alert_type,
            Alert.status == "ACTIVE",
        )
        .first()
    )

    if existing:
        return existing

    alert = Alert(
        vehicle_id=vehicle_id,
        alert_type=alert_type,
        alert_value=alert_value,
        severity=severity,
        message=message,
        status="ACTIVE",
        timestamp=timestamp,
    )

    db.add(alert)
    db.flush()
    db.refresh(alert)

    return alert


def resolve_alert(
    db: Session,
    vehicle_id: str,
    alert_type: str,
    timestamp,
):
    """
    Resolve all currently ACTIVE alerts of the specified
    type for a vehicle.
    """

    alerts = (
        db.query(Alert)
        .filter(
            Alert.vehicle_id == vehicle_id,
            Alert.alert_type == alert_type,
            Alert.status == "ACTIVE",
        )
        .all()
    )

    for alert in alerts:
        alert.status = "RESOLVED"
        alert.resolved_at = timestamp

    if alerts:
        db.flush()

    return alerts


def process_telemetry_alerts(
    db: Session,
    event: TelemetryEvent,
):
    """
    Central alert decision engine.

    Alert lifecycle:

        telemetry condition becomes true
                    ↓
              ACTIVE alert
                    ↓
        telemetry condition clears
                    ↓
             RESOLVED alert
    """

    vehicle_id = event.vehicle_id
    battery = event.battery
    temperature = event.temp
    speed = event.speed
    timestamp = event.timestamp

    vehicle_status = (
        event.vehicle_status or
        ("STOPPED" if speed == 0 else "MOVING")
    )

    charging_status = (
        event.charging_status or
        "NOT_CHARGING"
    )

    battery_critical = battery < 10
    battery_low = 10 <= battery < 20
    temperature_critical = temperature > 80
    overspeed = speed > 100
    stopped = vehicle_status == "STOPPED"
    charging = charging_status == "CHARGING"

    # --------------------------------------------------------
    # CREATE ACTIVE ALERTS
    # --------------------------------------------------------

    if battery_critical:
        create_alert(
            db,
            vehicle_id,
            "BATTERY_EMERGENCY",
            battery,
            "Critical",
            f"{vehicle_id} battery is critically low ({battery}%)",
            timestamp,
        )

    elif battery_low:
        create_alert(
            db,
            vehicle_id,
            "LOW_BATTERY_CRITICAL",
            battery,
            "High",
            f"{vehicle_id} battery is low ({battery}%)",
            timestamp,
        )

    if temperature_critical:
        create_alert(
            db,
            vehicle_id,
            "HIGH_TEMPERATURE_CRITICAL",
            temperature,
            "Critical",
            f"{vehicle_id} temperature is critically high ({temperature} C)",
            timestamp,
        )

    if overspeed:
        create_alert(
            db,
            vehicle_id,
            "OVERSPEED",
            speed,
            "Medium",
            f"{vehicle_id} exceeded safe speed ({speed} km/h)",
            timestamp,
        )

    if stopped:
        create_alert(
            db,
            vehicle_id,
            "VEHICLE_STOPPED",
            speed,
            "Medium",
            f"{vehicle_id} is currently stopped",
            timestamp,
        )

    if charging:
        create_alert(
            db,
            vehicle_id,
            "CHARGING",
            battery,
            "Info",
            f"{vehicle_id} is currently charging ({battery}% battery)",
            timestamp,
        )

    # --------------------------------------------------------
    # RESOLVE RECOVERED ALERTS
    # --------------------------------------------------------

    if not battery_critical:
        resolve_alert(
            db,
            vehicle_id,
            "BATTERY_EMERGENCY",
            timestamp,
        )

    if not battery_low:
        resolve_alert(
            db,
            vehicle_id,
            "LOW_BATTERY_CRITICAL",
            timestamp,
        )

    if not temperature_critical:
        resolve_alert(
            db,
            vehicle_id,
            "HIGH_TEMPERATURE_CRITICAL",
            timestamp,
        )

    if not overspeed:
        resolve_alert(
            db,
            vehicle_id,
            "OVERSPEED",
            timestamp,
        )

    if not stopped:
        resolve_alert(
            db,
            vehicle_id,
            "VEHICLE_STOPPED",
            timestamp,
        )

    if not charging:
        resolve_alert(
            db,
            vehicle_id,
            "CHARGING",
            timestamp,
        )

