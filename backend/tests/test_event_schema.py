import unittest
from datetime import datetime, timezone

from pydantic import ValidationError

from app.schemas.telemetry import TelemetryEvent


def valid_event():
    now = datetime.now(timezone.utc).isoformat()

    return {
        "event_id": "schema-test-001",
        "event_type": "EV_TELEMETRY",
        "schema_version": "1.0",
        "producer": "ev-telemetry-producer",
        "vehicle_id": "EV001",
        "battery": 80,
        "temp": 32,
        "speed": 60,
        "location": "Bangalore",
        "charging_status": "NOT_CHARGING",
        "event_timestamp": now,
        "ingestion_timestamp": now,
    }


class TestTelemetrySchema(unittest.TestCase):

    def test_valid_event(self):
        event = TelemetryEvent.model_validate(valid_event())

        self.assertEqual(event.event_id, "schema-test-001")
        self.assertEqual(event.vehicle_id, "EV001")
        self.assertEqual(event.schema_version, "1.0")
        self.assertIsNotNone(event.timestamp)

    def test_legacy_timestamp_alias(self):
        event = TelemetryEvent.model_validate(valid_event())
        dumped = event.model_dump()

        self.assertIn("timestamp", dumped)
        self.assertNotIn("event_timestamp", dumped)

    def test_unknown_fields_rejected(self):
        data = valid_event()
        data["unexpected_field"] = "must_fail"

        with self.assertRaises(ValidationError):
            TelemetryEvent.model_validate(data)

    def test_unsupported_schema_version_rejected(self):
        data = valid_event()
        data["schema_version"] = "99.0"

        with self.assertRaises(ValidationError):
            TelemetryEvent.model_validate(data)

    def test_unsupported_event_type_rejected(self):
        data = valid_event()
        data["event_type"] = "UNKNOWN_EVENT"

        with self.assertRaises(ValidationError):
            TelemetryEvent.model_validate(data)

    def test_invalid_battery_rejected(self):
        data = valid_event()
        data["battery"] = 150

        with self.assertRaises(ValidationError):
            TelemetryEvent.model_validate(data)

    def test_missing_vehicle_id_rejected(self):
        data = valid_event()
        del data["vehicle_id"]

        with self.assertRaises(ValidationError):
            TelemetryEvent.model_validate(data)


if __name__ == "__main__":
    unittest.main()
