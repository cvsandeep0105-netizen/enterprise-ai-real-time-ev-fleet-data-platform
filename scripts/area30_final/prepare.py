import json
import sys
from pathlib import Path
import pandas as pd

feature_file = Path(sys.argv[1])
output_file = Path(sys.argv[2])
watermarks = json.loads(sys.argv[3])

vehicles = ["CUP1","CUP2","CUP3","CUP4","CUP5","ID1","ID2"]

df = pd.read_parquet(
    feature_file,
    columns=[
        "vehicle_id",
        "window_start",
        "speed",
        "battery_soc",
        "battery_temp_min",
        "battery_temp_max"
    ]
)

df["vehicle_id"] = df["vehicle_id"].astype(str)
df["window_start"] = pd.to_datetime(
    df["window_start"],
    utc=True
)

selected = []

for vehicle in vehicles:

    watermark = pd.Timestamp(watermarks[vehicle])

    part = df[
        (df["vehicle_id"] == vehicle) &
        (df["window_start"] > watermark)
    ].sort_values("window_start")

    if len(part) < 8:
        raise RuntimeError(
            f"{vehicle}: fewer than 8 later real observations."
        )

    chosen = part.head(8)

    print(
        f"{vehicle}: {len(chosen)} NEW REAL ROWS | "
        f"{chosen['window_start'].iloc[0].isoformat()} -> "
        f"{chosen['window_start'].iloc[-1].isoformat()}"
    )

    selected.append(chosen)

df = pd.concat(selected, ignore_index=True)

df = df.sort_values(
    ["window_start","vehicle_id"]
).reset_index(drop=True)

payloads = []

for _, r in df.iterrows():

    payloads.append({
        "vehicle_id": str(r["vehicle_id"]),
        "timestamp": r["window_start"].isoformat(),
        "battery": float(r["battery_soc"]),
        "temp": float(
            (
                float(r["battery_temp_min"]) +
                float(r["battery_temp_max"])
            ) / 2.0
        ),
        "speed": float(r["speed"]),
        "location": None,
        "charging_status": None,
        "battery_status": None,
        "vehicle_status": None,
        "temperature_status": None,
        "is_charging": None
    })

if len(payloads) != 56:
    raise RuntimeError(
        f"Expected 56 rows, got {len(payloads)}."
    )

pairs = [
    (p["vehicle_id"],p["timestamp"])
    for p in payloads
]

if len(pairs) != len(set(pairs)):
    raise RuntimeError(
        "Duplicate vehicle/timestamp detected."
    )

with output_file.open("w",encoding="utf-8") as f:
    for p in payloads:
        f.write(
            json.dumps(p,separators=(",",":"))
            + "\n"
        )

print("REAL_REPLAY_ROWS =",len(payloads))
print("REAL_REPLAY_PREPARATION = PASS")
