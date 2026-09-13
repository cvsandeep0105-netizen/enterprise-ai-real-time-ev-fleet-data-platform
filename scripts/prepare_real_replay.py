import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone

import pandas as pd
from kafka import KafkaProducer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--events-per-vehicle", type=int, default=8)
    args = parser.parse_args()

    vehicles = ["CUP1", "CUP2", "CUP3", "CUP4", "CUP5", "ID1", "ID2"]

    if not os.path.exists(args.parquet):
        raise FileNotFoundError(args.parquet)

    df = pd.read_parquet(args.parquet)

    required = [
        "vehicle_id",
        "window_start",
        "speed",
        "battery_soc",
        "battery_temp_min",
        "battery_temp_max",
    ]

    missing = [x for x in required if x not in df.columns]
    if missing:
        raise RuntimeError(f"Missing columns: {missing}")

    df = df[required].copy()
    df["window_start"] = pd.to_datetime(df["window_start"], utc=True)
    df = df[df["vehicle_id"].isin(vehicles)]
    df = df.dropna(subset=required)

    rows = []

    for vehicle in vehicles:
        vehicle_df = (
            df[df["vehicle_id"] == vehicle]
            .sort_values("window_start")
            .tail(args.events_per_vehicle)
        )

        if len(vehicle_df) < args.events_per_vehicle:
            raise RuntimeError(
                f"Insufficient real rows for {vehicle}: {len(vehicle_df)}"
            )

        for _, r in vehicle_df.iterrows():
            rows.append({
                "vehicle_id": str(r["vehicle_id"]),
                "timestamp": r["window_start"].isoformat(),
                "battery": float(r["battery_soc"]),
                "temp": (
                    float(r["battery_temp_min"])
                    + float(r["battery_temp_max"])
                ) / 2.0,
                "speed": float(r["speed"]),
            })

    rows.sort(key=lambda x: (x["timestamp"], x["vehicle_id"]))

    with open(args.output, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    print("REAL_REPLAY_ROWS =", len(rows))
    print("REAL_REPLAY_VEHICLES =", sorted(set(x["vehicle_id"] for x in rows)))
    print("REAL_REPLAY_OUTPUT =", args.output)


if __name__ == "__main__":
    main()
