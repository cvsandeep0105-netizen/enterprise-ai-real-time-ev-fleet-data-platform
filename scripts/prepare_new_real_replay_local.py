import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


PROJECT = Path(r"C:\Users\sandeep\Desktop\EV Fleet Data Platform")

FEATURES = PROJECT / "data_lake" / "real_world" / "features" / "real_world_ev_features.parquet"
OUTPUT = PROJECT / "scripts" / "evfleet_area30_real_replay_new.ndjson"

VEHICLES = ["CUP1", "CUP2", "CUP3", "CUP4", "CUP5", "ID1", "ID2"]
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


print("FEATURE_SOURCE =", FEATURES)

if not FEATURES.exists():
    raise FileNotFoundError(FEATURES)

print("\n===== GET CURRENT POSTGRES WATERMARKS =====")

# Use kubectl exec + PostgreSQL's own psql client.
# This is READ-ONLY. No application data is changed.
pods = subprocess.check_output(
    [
        "kubectl",
        "get",
        "pods",
        "-n",
        "ev-fleet",
        "-l",
        "app=evfleet-postgres",
        "-o",
        "jsonpath={.items[0].metadata.name}",
    ],
    text=True,
).strip()

if not pods:
    raise RuntimeError("PostgreSQL pod not found.")

print("POSTGRES_POD =", pods)

sql = """
SELECT vehicle_id || '|' || to_char(MAX(timestamp), 'YYYY-MM-DD"T"HH24:MI:SS.US')
FROM ev_data
WHERE vehicle_id IN ('CUP1','CUP2','CUP3','CUP4','CUP5','ID1','ID2')
GROUP BY vehicle_id
ORDER BY vehicle_id;
"""

raw = subprocess.check_output(
    [
        "kubectl",
        "exec",
        "-n",
        "ev-fleet",
        pods,
        "--",
        "psql",
        "-U",
        "postgres",
        "-d",
        "ev_fleet",
        "-At",
        "-c",
        sql,
    ],
    text=True,
)

watermarks = {}

for line in raw.splitlines():
    line = line.strip()

    if not line or "|" not in line:
        continue

    vehicle, timestamp = line.split("|", 1)
    watermarks[vehicle] = normalize_ts(timestamp)

print("\nCURRENT_POSTGRES_WATERMARKS")

for vehicle in VEHICLES:
    if vehicle in watermarks:
        print(vehicle, "=", watermarks[vehicle].isoformat())
    else:
        print(vehicle, "= NONE")

print("\n===== READ REAL TUMFTM FEATURES =====")

df = pd.read_parquet(
    FEATURES,
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

print("\n===== SELECT NEW REAL OBSERVATIONS =====")

for vehicle in VEHICLES:

    vehicle_df = df[df["vehicle_id"] == vehicle].copy()

    watermark = watermarks.get(vehicle)

    if watermark is not None:
        vehicle_df = vehicle_df[
            vehicle_df["window_start"] > pd.Timestamp(watermark)
        ]

    chosen = vehicle_df.head(ROWS_PER_VEHICLE)

    if len(chosen) < ROWS_PER_VEHICLE:
        raise RuntimeError(
            f"{vehicle}: only {len(chosen)} new real rows available."
        )

    selected.append(chosen)

    print(
        vehicle,
        "NEW_ROWS =", len(chosen),
        "FIRST =", chosen["window_start"].iloc[0].isoformat(),
        "LAST =", chosen["window_start"].iloc[-1].isoformat(),
    )

selected_df = pd.concat(
    selected,
    ignore_index=True,
).sort_values(
    ["window_start", "vehicle_id"]
).reset_index(drop=True)

payloads = []

for _, row in selected_df.iterrows():

    timestamp = normalize_ts(row["window_start"])

    payloads.append(
        {
            "vehicle_id": str(row["vehicle_id"]),
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
    )

print("\n===== FINAL SAFETY CHECK =====")

# Verify no duplicate vehicle/timestamp combinations in the batch.
pairs = [
    (
        p["vehicle_id"],
        normalize_ts(p["timestamp"]),
    )
    for p in payloads
]

if len(pairs) != len(set(pairs)):
    raise RuntimeError(
        "Duplicate vehicle/timestamp found inside new replay batch."
    )

# Verify every selected row is strictly after its PostgreSQL watermark.
watermark_violations = []

for p in payloads:
    vehicle = p["vehicle_id"]
    ts = normalize_ts(p["timestamp"])

    if vehicle in watermarks and ts <= watermarks[vehicle]:
        watermark_violations.append(
            (vehicle, ts.isoformat(), watermarks[vehicle].isoformat())
        )

if watermark_violations:
    raise RuntimeError(
        "Watermark validation failed:\n"
        + "\n".join(str(x) for x in watermark_violations)
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

print("\n===== RESULT =====")
print("REAL_REPLAY_ROWS =", len(payloads))
print("REAL_REPLAY_VEHICLES =", sorted(set(p["vehicle_id"] for p in payloads)))
print("BATCH_DUPLICATES =", len(pairs) - len(set(pairs)))
print("WATERMARK_VIOLATIONS =", len(watermark_violations))
print("SAFE_NEW_ROWS =", len(payloads))
print("REAL_REPLAY_OUTPUT =", OUTPUT)
print("REAL_REPLAY_PREPARATION = PASS")
