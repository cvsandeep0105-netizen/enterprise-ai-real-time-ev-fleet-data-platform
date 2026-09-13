from datetime import datetime, timezone, timedelta
from sqlalchemy import text

from app.database.database import SessionLocal
from app.models.database_models import Alert
from app.schemas.telemetry import TelemetryEvent
from app.services.alert_service import process_telemetry_alerts


def make_event(**overrides):
    data = {
        "event_id": "area10-postgres-test",
        "event_type": "EV_TELEMETRY",
        "schema_version": "1.0",
        "producer": "area10-integration-test",
        "vehicle_id": "AREA10-TEST",
        "battery": 5.0,
        "temp": 30.0,
        "speed": 40.0,
        "location": "TEST",
        "charging_status": "NOT_CHARGING",
        "timestamp": datetime.now(timezone.utc).replace(tzinfo=None),
        "ingestion_timestamp": datetime.now(timezone.utc).replace(tzinfo=None),
        "vehicle_status": "MOVING",
        "is_charging": False,
    }
    data.update(overrides)
    return TelemetryEvent(**data)


db = SessionLocal()

try:
    print("=" * 60)
    print("AREA 10 POSTGRESQL ALERT LIFECYCLE INTEGRATION")
    print("=" * 60)

    # ---------------------------------------------------------
    # STEP 1 - DATABASE CONNECTIVITY
    # ---------------------------------------------------------
    print("STEP 1 - POSTGRESQL CONNECTIVITY")

    db.execute(text("SELECT 1"))
    print("DATABASE_CONNECTION=PASS")

    # ---------------------------------------------------------
    # CLEAN TEST DATA
    # ---------------------------------------------------------
    db.query(Alert).filter(
        Alert.vehicle_id == "AREA10-TEST"
    ).delete(synchronize_session=False)

    db.commit()

    # ---------------------------------------------------------
    # STEP 2 - CREATE ACTIVE ALERT
    # ---------------------------------------------------------
    print("STEP 2 - CREATE ACTIVE ALERT")

    event = make_event(battery=5.0)

    process_telemetry_alerts(db, event)
    db.commit()

    alerts = (
        db.query(Alert)
        .filter(
            Alert.vehicle_id == "AREA10-TEST",
            Alert.alert_type == "BATTERY_EMERGENCY",
        )
        .all()
    )

    assert len(alerts) == 1, (
        f"Expected 1 alert, found {len(alerts)}"
    )

    assert alerts[0].status == "ACTIVE"

    print("ALERT_CREATED=PASS")
    print(f"ALERT_ID={alerts[0].id}")
    print(f"STATUS={alerts[0].status}")

    # ---------------------------------------------------------
    # STEP 3 - DEDUPLICATION
    # ---------------------------------------------------------
    print("STEP 3 - ACTIVE ALERT DEDUPLICATION")

    process_telemetry_alerts(db, event)
    db.commit()

    duplicate_check = (
        db.query(Alert)
        .filter(
            Alert.vehicle_id == "AREA10-TEST",
            Alert.alert_type == "BATTERY_EMERGENCY",
            Alert.status == "ACTIVE",
        )
        .count()
    )

    assert duplicate_check == 1, (
        f"Expected exactly 1 ACTIVE alert, found {duplicate_check}"
    )

    print("ACTIVE_ALERT_DEDUP=PASS")

    # ---------------------------------------------------------
    # STEP 4 - RECOVERY
    # ---------------------------------------------------------
    print("STEP 4 - ALERT RECOVERY")

    recovery_event = make_event(
        battery=80.0,
        timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(seconds=1),
    )

    process_telemetry_alerts(db, recovery_event)
    db.commit()

    recovered = (
        db.query(Alert)
        .filter(
            Alert.vehicle_id == "AREA10-TEST",
            Alert.alert_type == "BATTERY_EMERGENCY",
        )
        .all()
    )

    assert len(recovered) == 1
    assert recovered[0].status == "RESOLVED"
    assert recovered[0].resolved_at is not None

    print("ALERT_RECOVERY=PASS")
    print(f"FINAL_STATUS={recovered[0].status}")
    print("RESOLVED_AT=SET")

    # ---------------------------------------------------------
    # STEP 5 - DATABASE PERSISTENCE CONTRACT
    # ---------------------------------------------------------
    print("STEP 5 - DATABASE PERSISTENCE CONTRACT")

    persisted = db.execute(
        text("""
            SELECT
                vehicle_id,
                alert_type,
                severity,
                status,
                resolved_at
            FROM alerts
            WHERE vehicle_id = :vehicle_id
              AND alert_type = :alert_type
        """),
        {
            "vehicle_id": "AREA10-TEST",
            "alert_type": "BATTERY_EMERGENCY",
        },
    ).mappings().one()

    assert persisted["vehicle_id"] == "AREA10-TEST"
    assert persisted["alert_type"] == "BATTERY_EMERGENCY"
    assert persisted["status"] == "RESOLVED"
    assert persisted["resolved_at"] is not None

    print("POSTGRES_PERSISTENCE=PASS")
    print("ALERT_LIFECYCLE=ACTIVE -> RESOLVED")

    print("=" * 60)
    print("AREA 10 POSTGRESQL INTEGRATION = PASS")
    print("=" * 60)

finally:
    try:
        db.query(Alert).filter(
            Alert.vehicle_id == "AREA10-TEST"
        ).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
    db.close()
