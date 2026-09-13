import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import psycopg2


FEATURES = Path(
    r"/workspace/data_lake/real_world/features/real_world_ev_features.parquet"
)

# Fallback locations are checked because the local project mount can differ.
FEATURE_CANDIDATES = [
    Path(r"/workspace/data_lake/real_world/features/real_world_ev_features.parquet"),
    Path(r"/app/data_lake/real_world/features/real_world_ev_features.parquet"),
    Path(r"/data_lake/real_world/features/real_world_ev_features.parquet"),
]

OUTPUT = Path("/tmp/evfleet_area30_real_replay_new.ndjson")

VEHICLES = ["CUP1", "CUP2", "CUP3", "CUP4", "CUP5", "ID1", "ID2"]

# Number of NEW real observations per vehicle.
ROWS_PER_VEHICLE = 8


def normalize_ts(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    text = str(value).strip()

    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    dt = datetime.fromisoformat(text)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


feature_path = next((p for p in FEATURE_CANDIDATES if p.exists()), None)

if feature_path is None:
    raise FileNotFoundError(
        "Could not locate real TUMFTM feature Parquet. Checked:\n"
        + "\n".join(str(p) for p in FEATURE_CANDIDATES)
    )

print("REAL_FEATURE_SOURCE =", feature_path)

conn = psycopg2.connect(
    host=os.environ["POSTGRES_HOST"],
    port=os.environ["POSTGRES_PORT"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    dbname=os.environ["POSTGRES_DB"],
)

cur = conn.cursor()

# Read the actual operational watermark from PostgreSQL.
cur.execute("""
    SELECT vehicle_id, MAX(timestamp)
    FROM ev_data
    WHERE vehicle_id = ANY(%s)
    GROUP BY vehicle_id
    ORDER BY vehicle_id
""", (VEHICLES,))

watermarks = {
    str(vehicle): normalize_ts(timestamp)
    for vehicle, timestamp in cur.fetchall()
}

print("\nCURRENT_POSTGRES_WATERMARKS")

for vehicle in VEHICLES:
    print(
        vehicle,
        "=",
        watermarks.get(vehicle).isoformat()
        if vehicle in watermarks else "NONE"
    )

# Read only the columns needed for canonical replay.
df = pd.read_parquet(
    feature_path,
    columns=[
        "vehicle_id",
        "window_start",
        "speed",
        "battery_soc",
        "battery_voltage",
        "battery_temp_min",
        "battery_temp_max",
    ],
)

df["vehicle_id"] = df["vehicle_id"].astype(str)
df["window_start"] = pd.to_datetime(
    df["window_start"],
    utc=True,
)

df = df[df["vehicle_id"].isin(VEHICLES)].copy()

df = df.sort_values(
    ["vehicle_id", "window_start"]
).reset_index(drop=True)

selected = []

print("\nSELECTING NEW REAL OBSERVATIONS")

for vehicle in VEHICLES:

    vehicle_df = df[df["vehicle_id"] == vehicle].copy()

    watermark = watermarks.get(vehicle)

    if watermark is not None:
        vehicle_df = vehicle_df[
            vehicle_df["window_start"] > pd.Timestamp(watermark)
        ]

    vehicle_df = vehicle_df.head(ROWS_PER_VEHICLE)

    if len(vehicle_df) < ROWS_PER_VEHICLE:
        raise RuntimeError(
            f"{vehicle}: only {len(vehicle_df)} new real rows available; "
            f"required {ROWS_PER_VEHICLE}"
        )

    selected.append(vehicle_df)

    print(
        vehicle,
        "NEW_ROWS =", len(vehicle_df),
        "FIRST =", vehicle_df["window_start"].iloc[0].isoformat(),
        "LAST =", vehicle_df["window_start"].iloc[-1].isoformat(),
    )

selected_df = pd.concat(
    selected,
    ignore_index=True,
).sort_values(
    ["window_start", "vehicle_id"]
).reset_index(drop=True)

# Convert selected rows into the exact canonical replay payload.
payloads = []

for _, row in selected_df.iterrows():

    vehicle = str(row["vehicle_id"])
    timestamp = normalize_ts(row["window_start"])

    payload = {
        "vehicle_id": vehicle,
        "timestamp": timestamp.isoformat(),
        "battery": float(row["battery_soc"]),
        "temp": float(
            (
                float(row["battery_temp_min"])
                + float(row["battery_temp_max"])
            ) / 2.0
        ),
        "speed": float(row["speed"]),
        "location": None,
        "charging_status": None,
        "battery_status": None,
        "vehicle_status": None,
        "temperature_status": None,
        "is_charging": None,
    }

    payloads.append(payload)

# Final safety validation against the SAME PostgreSQL state.
existing_pairs = set()

cur.execute("""
    SELECT vehicle_id, timestamp
    FROM ev_data
    WHERE vehicle_id = ANY(%s)
""", (VEHICLES,))

for vehicle, timestamp in cur.fetchall():
    existing_pairs.add(
        (str(vehicle), normalize_ts(timestamp))
    )

conflicts = []

for payload in payloads:
    pair = (
        payload["vehicle_id"],
        normalize_ts(payload["timestamp"])
    )

    if pair in existing_pairs:
        conflicts.append(pair)

if conflicts:
    raise RuntimeError(
        "SAFETY CHECK FAILED: selected rows already exist in PostgreSQL:\n"
        + "\n".join(
            f"{vehicle} {timestamp.isoformat()}"
            for vehicle, timestamp in conflicts
        )
    )

# Ensure no duplicates inside the new batch.
batch_pairs = [
    (
        p["vehicle_id"],
        normalize_ts(p["timestamp"])
    )
    for p in payloads
]

if len(batch_pairs) != len(set(batch_pairs)):
    raise RuntimeError(
        "SAFETY CHECK FAILED: duplicate vehicle/timestamp inside replay batch."
    )

with OUTPUT.open("w", encoding="utf-8") as f:
    for payload in payloads:
        f.write(
            json.dumps(
                payload,
                separators=(",", ":"),
            )
            + "\n"
        )

print("\n===== PREPARATION RESULT =====")
print("REAL_REPLAY_ROWS =", len(payloads))
print("REAL_REPLAY_VEHICLES =", sorted(set(p["vehicle_id"] for p in payloads)))
print("POSTGRES_TIMESTAMP_CONFLICTS =", len(conflicts))
print("INTERNAL_BATCH_DUPLICATES =", len(batch_pairs) - len(set(batch_pairs)))
print("SAFE_NEW_ROWS =", len(payloads))
print("REAL_REPLAY_OUTPUT =", OUTPUT)
print("REAL_REPLAY_PREPARATION = PASS")

cur.close()
conn.close()
