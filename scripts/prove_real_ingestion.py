import json
import os
import uuid
import psycopg2

INPUT = "/tmp/evfleet_area30_real_replay.ndjson"

expected = []

with open(INPUT, "r", encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        event_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"TUMFTM-EV-UDS-CANONICAL|{row['vehicle_id']}|{row['timestamp']}",
            )
        )
        expected.append(event_id)

conn = psycopg2.connect(
    host=os.environ["POSTGRES_HOST"],
    port=os.environ["POSTGRES_PORT"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    dbname=os.environ["POSTGRES_DB"],
)

cur = conn.cursor()

cur.execute(
    """
    SELECT event_id
    FROM ev_data
    WHERE event_id = ANY(%s)
    """,
    (expected,),
)

found = {row[0] for row in cur.fetchall()}
missing = [x for x in expected if x not in found]

print("EXPECTED_CANONICAL_EVENTS =", len(expected))
print("EVENTS_PRESENT_IN_POSTGRES =", len(found))
print("MISSING_EVENTS =", len(missing))

if missing:
    print("MISSING_EVENT_IDS:")
    for event_id in missing:
        print(event_id)

cur.close()
conn.close()

if len(found) == len(expected):
    print("REAL TUMFTM END-TO-END INGESTION = PASS")
else:
    print("REAL TUMFTM END-TO-END INGESTION = FAIL")
    raise SystemExit(1)
