import os
from datetime import datetime, timedelta
import psycopg2

ROWS_PER_VEHICLE = 1000
VEHICLES = 20

conn = psycopg2.connect(
    host=os.environ["POSTGRES_HOST"],
    port=os.environ["POSTGRES_PORT"],
    dbname=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
)
conn.autocommit = False
cur = conn.cursor()

cur.execute("""
SELECT column_name
FROM information_schema.columns
WHERE table_schema='public'
AND table_name='ev_data'
ORDER BY ordinal_position
""")
columns = [r[0] for r in cur.fetchall()]
print("Actual ev_data columns:", columns)

required = {"event_id", "vehicle_id", "timestamp"}
missing = required - set(columns)
if missing:
    raise RuntimeError(f"Required ev_data columns missing: {sorted(missing)}")

base = datetime.utcnow() - timedelta(hours=24)

all_rows = []
for v in range(1, VEHICLES + 1):
    vehicle_id = f"EV-{v:03d}"
    for i in range(ROWS_PER_VEHICLE):
        ts = base + timedelta(seconds=i * 86)
        event_id = f"area28-{v:03d}-{i:06d}"

        values = {
            "event_id": event_id,
            "event_type": "telemetry",
            "schema_version": "v1",
            "producer": "area28-load",
            "vehicle_id": vehicle_id,
            "battery": 80.0 - (i % 30) * 0.1,
            "temp": 25.0 + (i % 15) * 0.2,
            "speed": float(i % 90),
            "location": f"ZONE-{v:02d}",
            "charging_status": "NOT_CHARGING",
            "timestamp": ts,
            "status": "NORMAL",
            "battery_status": "NORMAL",
            "vehicle_status": "NORMAL",
            "temperature_status": "NORMAL",
            "is_charging": False,
        }

        row = tuple(values[c] for c in columns if c in values)
        all_rows.append((tuple(c for c in columns if c in values), row))

insert_columns = list(all_rows[0][0])
placeholders = ",".join(["%s"] * len(insert_columns))
column_sql = ",".join(f'"{c}"' for c in insert_columns)

sql = f"""
INSERT INTO ev_data ({column_sql})
VALUES ({placeholders})
ON CONFLICT DO NOTHING
"""

cur.executemany(sql, [r[1] for r in all_rows])
conn.commit()

cur.execute("SELECT count(*) FROM ev_data")
count = cur.fetchone()[0]

print(f"Telemetry rows now available: {count:,}")

cur.close()
conn.close()