import json
import os
from sqlalchemy import create_engine, text

vehicles = ["CUP1","CUP2","CUP3","CUP4","CUP5","ID1","ID2"]

engine = create_engine(os.environ["DATABASE_URL"])

with engine.connect() as conn:
    rows = conn.execute(
        text("""
            SELECT vehicle_id, MAX(timestamp)
            FROM ev_data
            WHERE vehicle_id = ANY(:vehicles)
            GROUP BY vehicle_id
            ORDER BY vehicle_id
        """),
        {"vehicles": vehicles}
    ).fetchall()

    result = {
        str(vehicle): timestamp.isoformat()
        for vehicle, timestamp in rows
    }

print(json.dumps(result))
