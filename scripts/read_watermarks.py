from sqlalchemy import create_engine, text
import os

engine = create_engine(os.environ["DATABASE_URL"])

with engine.connect() as conn:
    rows = conn.execute(
        text("""
            SELECT vehicle_id, MAX(timestamp)
            FROM ev_data
            WHERE vehicle_id IN (
                'CUP1','CUP2','CUP3','CUP4','CUP5','ID1','ID2'
            )
            GROUP BY vehicle_id
            ORDER BY vehicle_id
        """)
    ).fetchall()

print("===== CURRENT REAL DATA WATERMARKS =====")

for vehicle_id, max_timestamp in rows:
    print(f"{vehicle_id} = {max_timestamp}")

print("===== WATERMARK QUERY = PASS =====")
