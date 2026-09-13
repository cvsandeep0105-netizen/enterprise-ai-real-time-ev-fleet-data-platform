from datetime import datetime, timezone
from math import isfinite


ALLOWED_VEHICLE_STATUSES = {
    "MOVING",
    "STOPPED",
    "MAINTENANCE",
}

ALLOWED_CHARGING_STATUSES = {
    "CHARGING",
    "NOT_CHARGING",
}

MIN_TEMPERATURE_C = -50.0
MAX_TEMPERATURE_C = 100.0
MAX_SPEED_KMH = 300.0


class DataQualityError(ValueError):
    """Raised when telemetry fails a data-quality rule."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def _require(value, field: str):
    if value is None:
        raise DataQualityError(
            "MISSING_REQUIRED_FIELD",
            f"{field} is required",
        )


def _finite(value, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise DataQualityError(
            "INVALID_NUMERIC_VALUE",
            f"{field} must be numeric",
        )

    if not isfinite(number):
        raise DataQualityError(
            "NON_FINITE_VALUE",
            f"{field} must be finite",
        )

    return number


def validate_telemetry_quality(
    event,
    *,
    now=None,
):
    """
    Central production data-quality gate.

    Returns the validated event unchanged when all quality
    rules pass. Raises DataQualityError on a hard failure.
    """

    now = now or datetime.now(timezone.utc)

    # --------------------------------------------------------
    # Required identity
    # --------------------------------------------------------

    _require(event.event_id, "event_id")
    _require(event.vehicle_id, "vehicle_id")
    _require(event.timestamp, "timestamp")

    # --------------------------------------------------------
    # Numeric quality
    # --------------------------------------------------------

    battery = _finite(event.battery, "battery")
    temperature = _finite(event.temp, "temp")
    speed = _finite(event.speed, "speed")

    # --------------------------------------------------------
    # Physical/domain ranges
    # --------------------------------------------------------

    if not 0 <= battery <= 100:
        raise DataQualityError(
            "BATTERY_OUT_OF_RANGE",
            "battery must be between 0 and 100",
        )

    if not MIN_TEMPERATURE_C <= temperature <= MAX_TEMPERATURE_C:
        raise DataQualityError(
            "TEMPERATURE_OUT_OF_RANGE",
            f"temp must be between "
            f"{MIN_TEMPERATURE_C} and {MAX_TEMPERATURE_C} C",
        )

    if not 0 <= speed <= MAX_SPEED_KMH:
        raise DataQualityError(
            "SPEED_OUT_OF_RANGE",
            f"speed must be between 0 and {MAX_SPEED_KMH} km/h",
        )

    # --------------------------------------------------------
    # Enum/domain validation
    # --------------------------------------------------------

    vehicle_status = (
        str(event.vehicle_status).strip().upper()
        if event.vehicle_status is not None
        else None
    )

    if vehicle_status is not None:
        if vehicle_status not in ALLOWED_VEHICLE_STATUSES:
            raise DataQualityError(
                "INVALID_VEHICLE_STATUS",
                f"Unsupported vehicle_status: {vehicle_status}",
            )

    charging_status = (
        str(event.charging_status).strip().upper()
        if event.charging_status is not None
        else "NOT_CHARGING"
    )

    if charging_status not in ALLOWED_CHARGING_STATUSES:
        raise DataQualityError(
            "INVALID_CHARGING_STATUS",
            f"Unsupported charging_status: {charging_status}",
        )

    # --------------------------------------------------------
    # Cross-field consistency
    # --------------------------------------------------------

    if event.is_charging is not None:
        expected = charging_status == "CHARGING"

        if bool(event.is_charging) != expected:
            raise DataQualityError(
                "CHARGING_STATUS_CONFLICT",
                "is_charging conflicts with charging_status",
            )

    if charging_status == "CHARGING" and speed > 0:
        raise DataQualityError(
            "CHARGING_MOVEMENT_CONFLICT",
            "A charging vehicle cannot simultaneously have speed > 0",
        )

    if vehicle_status == "STOPPED" and speed > 0:
        raise DataQualityError(
            "VEHICLE_STATUS_CONFLICT",
            "STOPPED vehicle cannot have speed > 0",
        )

    if vehicle_status == "MOVING" and speed == 0:
        raise DataQualityError(
            "VEHICLE_STATUS_CONFLICT",
            "MOVING vehicle cannot have speed = 0",
        )

    # --------------------------------------------------------
    # Timestamp quality
    # --------------------------------------------------------

    timestamp = event.timestamp

    if timestamp.tzinfo is None:
        raise DataQualityError(
            "NAIVE_TIMESTAMP",
            "timestamp must contain timezone information",
        )

    timestamp_utc = timestamp.astimezone(timezone.utc)
    now_utc = (
        now.astimezone(timezone.utc)
        if now.tzinfo
        else now.replace(tzinfo=timezone.utc)
    )

    if timestamp_utc > now_utc:
        raise DataQualityError(
            "FUTURE_TIMESTAMP",
            "event timestamp cannot be in the future",
        )

    if event.ingestion_timestamp is not None:
        ingestion = event.ingestion_timestamp

        if ingestion.tzinfo is None:
            raise DataQualityError(
                "NAIVE_INGESTION_TIMESTAMP",
                "ingestion_timestamp must contain timezone information",
            )

        ingestion_utc = ingestion.astimezone(timezone.utc)

        if ingestion_utc < timestamp_utc:
            raise DataQualityError(
                "TIMESTAMP_ORDER_ERROR",
                "ingestion_timestamp cannot be earlier than event timestamp",
            )

    return event


def quality_result(event, *, now=None):
    """
    Non-throwing quality interface useful for APIs,
    observability, tests, and quarantine handling.
    """

    try:
        validate_telemetry_quality(event, now=now)

        return {
            "valid": True,
            "quality_code": "QUALITY_OK",
            "message": "Telemetry passed all data-quality rules",
        }

    except DataQualityError as error:
        return {
            "valid": False,
            "quality_code": error.code,
            "message": error.message,
        }
