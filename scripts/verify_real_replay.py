import os
import psycopg2

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
    SELECT
        COUNT(*),
        COUNT(DISTINCT vehicle_id),
        MIN(timestamp),
        MAX(timestamp)
    FROM ev_data
    WHERE producer = %s
    """,
    ("tumftm-real-replay",),
)

rows, vehicles, first_ts, last_ts = cur.fetchone()

print("REAL_REPLAY_DB_ROWS =", rows)
print("REAL_REPLAY_DB_VEHICLES =", vehicles)
print("REAL_REPLAY_FIRST =", first_ts)
print("REAL_REPLAY_LAST =", last_ts)

cur.close()
conn.close()

if rows >= 56 and vehicles == 7:
    print("REAL KAFKA -> CONSUMER -> POSTGRES = PASS")
else:
    print("REAL KAFKA -> CONSUMER -> POSTGRES = FAIL")
    raise SystemExit(1)
