import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone

import pandas as pd
from kafka import KafkaProducer


PROJECT_ROOT = r"C:\Users\sandeep\Desktop\EV Fleet Data Platform"
PARQUET = os.path.join(
    PROJECT_ROOT,
    "data_lake",
    "real_world",
    "features",
    "real_world_ev_features.parquet",
)

KAFKA_BOOTSTRAP = "127.0.0.1:19092"
KAFKA_TOPIC = "ev.telemetry.v1"

# Vehicles already represented in the real-world operational dataset.
VEHICLES = ["CUP1", "CUP2", "CUP3", "CUP4", "CUP5", "ID1", "ID2"]

# Keep the demo short while still visibly demonstrating a real streaming flow.
EVENTS_PER_VEHICLE = 12
INTERVAL_SECONDS = 1.0


def deterministic_event_id(vehicle_id: str, timestamp: str) -> str:
    return str(uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"TUMFTM-EV-UDS|{vehicle_id}|{timestamp}"
    ))


def main():
    if not os.path.exists(PARQUET):
        raise FileNotFoundError(f"Real TUMFTM feature artifact not found: {PARQUET}")

    print("=" * 72)
    print("TUMFTM REAL-WORLD KAFKA REPLAY")
    print("=" * 72)
    print(f"Source : {PARQUET}")
    print(f"Topic  : {KAFKA_TOPIC}")
    print(f"Events : {EVENTS_PER_VEHICLE} per vehicle")
    print()

    df = pd.read_parquet(PARQUET)

    required = [
        "vehicle_id",
        "window_start",
        "speed",
        "battery_soc",
        "battery_temp_min",
        "battery_temp_max",
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"Missing required real-data columns: {missing}")

    df = df[required].copy()
    df["window_start"] = pd.to_datetime(df["window_start"], utc=True)

    # Only legitimate real vehicles.
    df = df[df["vehicle_id"].isin(VEHICLES)].copy()

    # Remove unusable records. No synthetic replacement is performed.
    df = df.dropna(
        subset=[
            "vehicle_id",
            "window_start",
            "speed",
            "battery_soc",
            "battery_temp_min",
            "battery_temp_max",
        ]
    )

    # Use the latest chronological real observations so the dashboard
    # visibly advances from the currently loaded historical state.
    selected = []

    for vehicle in VEHICLES:
        vehicle_df = (
            df[df["vehicle_id"] == vehicle]
            .sort_values("window_start")
            .tail(EVENTS_PER_VEHICLE)
        )

        if len(vehicle_df) < EVENTS_PER_VEHICLE:
            raise RuntimeError(
                f"Not enough real TUMFTM rows for {vehicle}: {len(vehicle_df)}"
            )

        selected.append(vehicle_df)

    replay = (
        pd.concat(selected)
        .sort_values(["window_start", "vehicle_id"])
        .reset_index(drop=True)
    )

    print(f"REAL ROWS SELECTED = {len(replay)}")
    print(f"REAL VEHICLES      = {sorted(replay.vehicle_id.unique())}")
    print(
        f"TIME RANGE         = "
        f"{replay.window_start.min()} -> {replay.window_start.max()}"
    )
    print()

    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BOOTSTRAP],
        acks="all",
        retries=10,
        max_in_flight_requests_per_connection=1,
        enable_idempotence=True,
        compression_type="gzip",
        value_serializer=lambda value: json.dumps(
            value, separators=(",", ":")
        ).encode("utf-8"),
        key_serializer=lambda value: value.encode("utf-8"),
    )

    sent = 0

    try:
        for _, row in replay.iterrows():
            vehicle_id = str(row["vehicle_id"])
            event_time = row["window_start"].to_pydatetime()

            # Canonical telemetry contract used by the existing consumer.
            # Temperature is derived from the real battery min/max values.
            temperature = (
                float(row["battery_temp_min"])
                + float(row["battery_temp_max"])
            ) / 2.0

            speed = float(row["speed"])
            battery = float(row["battery_soc"])

            event = {
                "event_id": deterministic_event_id(
                    vehicle_id,
                    event_time.isoformat(),
                ),
                "event_type": "telemetry",
                "schema_version": "1.0",
                "producer": "tumftm-real-replay",
                "vehicle_id": vehicle_id,
                "battery": battery,
                "temp": temperature,
                "speed": speed,
                "location": None,
                "charging_status": "NOT_CHARGING",
                "timestamp": event_time.isoformat(),
                "ingestion_timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
            }

            producer.send(
                KAFKA_TOPIC,
                key=vehicle_id,
                value=event,
            )

            sent += 1

            print(
                f"[{sent:03d}/{len(replay):03d}] "
                f"{vehicle_id:<5} "
                f"timestamp={event_time.isoformat()} "
                f"battery={battery:6.2f} "
                f"temp={temperature:6.2f} "
                f"speed={speed:6.2f}"
            )

            if INTERVAL_SECONDS > 0:
                time.sleep(INTERVAL_SECONDS)

        producer.flush()

        print()
        print("=" * 72)
        print(f"REAL EVENTS PUBLISHED = {sent}")
        print(f"KAFKA TOPIC           = {KAFKA_TOPIC}")
        print("REPLAY                 = PASS")
        print("=" * 72)

    finally:
        producer.close()


if __name__ == "__main__":
    main()
