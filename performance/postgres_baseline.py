import json
import os
import time
from pathlib import Path
import psycopg2

conn = psycopg2.connect(
    host=os.environ["POSTGRES_HOST"],
    port=os.environ["POSTGRES_PORT"],
    dbname=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
)
conn.autocommit = True
cur = conn.cursor()

cur.execute("""
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('ev_data','alerts','vehicles')
ORDER BY table_name
""")
tables = [r[0] for r in cur.fetchall()]

row_counts = {}
for table in tables:
    cur.execute(f"SELECT count(*) FROM {table}")
    row_counts[table] = cur.fetchone()[0]

cur.execute("""
SELECT tablename,indexname,indexdef
FROM pg_indexes
WHERE schemaname='public'
AND tablename IN ('ev_data','alerts','vehicles')
ORDER BY tablename,indexname
""")

indexes = {}
for table,name,definition in cur.fetchall():
    indexes.setdefault(table, []).append({
        "name": name,
        "definition": definition,
    })

queries = {
    "telemetry_count": "SELECT count(*) FROM ev_data",
    "vehicle_lookup": """
        SELECT event_id,vehicle_id,timestamp,battery,speed
        FROM ev_data
        WHERE vehicle_id='EV-001'
        ORDER BY timestamp DESC
        LIMIT 50
    """,
    "vehicle_time_range": """
        SELECT count(*)
        FROM ev_data
        WHERE vehicle_id='EV-001'
        AND timestamp >= NOW() - INTERVAL '24 hours'
    """,
    "active_alerts": """
        SELECT count(*)
        FROM alerts
        WHERE status='ACTIVE'
    """,
}

timings = {}
for name,sql in queries.items():
    start = time.perf_counter()
    cur.execute(sql)
    cur.fetchall()
    timings[name] = round((time.perf_counter() - start) * 1000, 3)

cur.execute("""
EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON)
SELECT event_id,vehicle_id,timestamp,battery,speed
FROM ev_data
WHERE vehicle_id='EV-001'
ORDER BY timestamp DESC
LIMIT 50
""")
plan = cur.fetchone()[0][0]

result = {
    "database": os.environ["POSTGRES_DB"],
    "tables": tables,
    "row_counts": row_counts,
    "indexes": indexes,
    "query_timings_ms": timings,
    "vehicle_lookup_plan": plan,
}

out = Path(os.environ["AREA28_OUTPUT"])
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")

print(json.dumps({
    "tables": tables,
    "row_counts": row_counts,
    "query_timings_ms": timings,
    "index_counts": {k: len(v) for k,v in indexes.items()},
}, indent=2))

cur.close()
conn.close()