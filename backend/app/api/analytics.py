from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.database import get_db

router = APIRouter()


# ============================================================
# BATTERY ANALYTICS
# ============================================================

@router.get("/analytics/battery")
def battery_analytics(
    db: Session = Depends(get_db)
):

    query = text("""
        SELECT DISTINCT ON (vehicle_id)
            vehicle_id,
            battery
        FROM ev_data
        ORDER BY vehicle_id, timestamp DESC
    """)

    result = db.execute(query).mappings().all()

    return [dict(row) for row in result]


# ============================================================
# VEHICLE STATUS ANALYTICS
# ============================================================

@router.get("/analytics/status")
def status_analytics(
    db: Session = Depends(get_db)
):

    query = text("""
        WITH latest AS (
            SELECT DISTINCT ON (vehicle_id)
                vehicle_id,
                vehicle_status
            FROM ev_data
            ORDER BY vehicle_id, timestamp DESC
        )

        SELECT
            vehicle_status AS status,
            COUNT(*) AS count
        FROM latest
        GROUP BY vehicle_status
        ORDER BY vehicle_status
    """)

    result = db.execute(query).mappings().all()

    return [dict(row) for row in result]