from datetime import datetime, timedelta, timezone

from app.models.database_models import Alert
from app.schemas.telemetry import TelemetryEvent
from app.services.alert_service import process_telemetry_alerts


def make_event(
    battery=80,
    temp=30,
    speed=50,
    vehicle_status="MOVING",
    charging_status="NOT_CHARGING",
):
    return TelemetryEvent(
        event_id="alert-test-event",
        event_type="EV_TELEMETRY",
        schema_version="1.0",
        producer="alert-test",
        vehicle_id="EV-TEST-001",
        battery=battery,
        temp=temp,
        speed=speed,
        location="Bangalore",
        charging_status=charging_status,
        timestamp=datetime.now(timezone.utc),
        ingestion_timestamp=datetime.now(timezone.utc),
        vehicle_status=vehicle_status,
        is_charging=charging_status == "CHARGING",
    )


class FakeQuery:
    def __init__(self, alerts):
        self.alerts = alerts

    def filter(self, *conditions):
        result = self.alerts
        for condition in conditions:
            if hasattr(condition, "left") and hasattr(condition, "right"):
                field = getattr(condition.left, "name", None)
                expected = condition.right.value if hasattr(condition.right, "value") else condition.right
                if field:
                    result = [a for a in result if getattr(a, field, None) == expected]
        return FakeQuery(result)

    def first(self):
        return self.alerts[0] if self.alerts else None

    def all(self):
        return list(self.alerts)


class FakeDB:
    def __init__(self):
        self.alerts = []
        self.commits = 0

    def query(self, model):
        return FakeQuery(self.alerts)

    def add(self, alert):
        self.alerts.append(alert)

    def flush(self):
        return None

    def refresh(self, alert):
        return alert

    def commit(self):

        self.commits += 1

class FakeDB:
    def __init__(self):
        self.alerts = []
        self.flushed = 0
        self.commits = 0

    def query(self, model):
        return FakeQuery(self.alerts)

    def add(self, alert):
        self.alerts.append(alert)

    def flush(self):
        self.flushed += 1

    def refresh(self, alert):

        return alert


    def commit(self):


        self.commits += 1


def test_critical_battery_creates_active_alert():
    db = FakeDB()

    process_telemetry_alerts(
        db,
        make_event(battery=5),
    )

    assert any(
        a.alert_type == "BATTERY_EMERGENCY"
        and a.status == "ACTIVE"
        for a in db.alerts
    )


def test_recovery_resolves_battery_alert():
    db = FakeDB()

    process_telemetry_alerts(
        db,
        make_event(battery=5),
    )

    process_telemetry_alerts(
        db,
        make_event(battery=80),
    )

    alerts = [
        a for a in db.alerts
        if a.alert_type == "BATTERY_EMERGENCY"
    ]

    assert alerts
    assert any(a.status == "RESOLVED" for a in alerts)


def test_active_alert_is_not_duplicated():
    db = FakeDB()

    process_telemetry_alerts(
        db,
        make_event(battery=5),
    )

    first_count = len(db.alerts)

    process_telemetry_alerts(
        db,
        make_event(battery=5),
    )

    assert len(db.alerts) == first_count


def test_overspeed_alert_created():
    db = FakeDB()

    process_telemetry_alerts(
        db,
        make_event(speed=120),
    )

    assert any(
        a.alert_type == "OVERSPEED"
        and a.status == "ACTIVE"
        for a in db.alerts
    )


def test_high_temperature_alert_created():
    db = FakeDB()

    process_telemetry_alerts(
        db,
        make_event(temp=90),
    )

    assert any(
        a.alert_type == "HIGH_TEMPERATURE_CRITICAL"
        and a.status == "ACTIVE"
        for a in db.alerts
    )


def test_charging_alert_created():
    db = FakeDB()

    process_telemetry_alerts(
        db,
        make_event(
            charging_status="CHARGING",
        ),
    )

    assert any(
        a.alert_type == "CHARGING"
        and a.status == "ACTIVE"
        for a in db.alerts
    )


def test_alert_service_does_not_commit_transaction():
    db = FakeDB()

    process_telemetry_alerts(
        db,
        make_event(battery=5),
    )

    assert db.commits == 0
    assert db.flushed > 0



