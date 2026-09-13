from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.database_models import Alert


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
)


@router.get("/")
def get_alerts(
    db: Session = Depends(get_db),
):
    alerts = (
        db.query(Alert)
        .order_by(Alert.timestamp.desc())
        .limit(100)
        .all()
    )

    return [
        {
            "id": alert.id,
            "vehicle_id": alert.vehicle_id,
            "alert_type": alert.alert_type,
            "alert_value": alert.alert_value,
            "severity": alert.severity,
            "message": alert.message,
            "status": alert.status,
            "timestamp": alert.timestamp,
            "resolved_at": alert.resolved_at,
        }
        for alert in alerts
    ]


@router.get("/{vehicle_id}")
def get_vehicle_alerts(
    vehicle_id: str,
    db: Session = Depends(get_db),
):
    alerts = (
        db.query(Alert)
        .filter(Alert.vehicle_id == vehicle_id)
        .order_by(Alert.timestamp.desc())
        .limit(100)
        .all()
    )

    return [
        {
            "id": alert.id,
            "vehicle_id": alert.vehicle_id,
            "alert_type": alert.alert_type,
            "alert_value": alert.alert_value,
            "severity": alert.severity,
            "message": alert.message,
            "status": alert.status,
            "timestamp": alert.timestamp,
            "resolved_at": alert.resolved_at,
        }
        for alert in alerts
    ]