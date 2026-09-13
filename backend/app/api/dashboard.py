from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.database import get_db


router = APIRouter()


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):

    query = text("""
        WITH latest AS (
            SELECT DISTINCT ON (vehicle_id)
                vehicle_id,
                battery,
                speed,
                charging_status,
                vehicle_status,
                timestamp
            FROM ev_data
            ORDER BY vehicle_id, timestamp DESC
        )
        SELECT
            COUNT(*) AS total_vehicles,

            COUNT(*) FILTER (
                WHERE vehicle_status = 'MOVING'
            ) AS running,

            COUNT(*) FILTER (
                WHERE charging_status = 'CHARGING'
            ) AS charging,

            COUNT(*) FILTER (
                WHERE battery < 20
            ) AS low_battery,

            (SELECT COUNT(*) FROM alerts WHERE status = 'ACTIVE') AS active_alerts,

            COALESCE(AVG(battery), 0) AS average_battery,

            COALESCE(AVG(speed), 0) AS average_speed

        FROM latest
    """)

    result = db.execute(query).mappings().one()

    return {
        "total_vehicles": result["total_vehicles"],
        "running": result["running"],
        "charging": result["charging"],
        "low_battery": result["low_battery"],
        "active_alerts": result["active_alerts"],
        "average_battery": round(float(result["average_battery"]), 2),
        "average_speed": round(float(result["average_speed"]), 2)
    }
