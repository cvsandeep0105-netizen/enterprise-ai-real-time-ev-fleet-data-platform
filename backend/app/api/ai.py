from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ai.anomaly import EVAnomalyModel
from app.database.database import get_db


router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


REAL_WORLD_MODEL_PATH = (
    "/app/backend/models/real_world_ev_anomaly_isolation_forest.joblib"
)

REAL_WORLD_MODEL_VERSION = "real-world-1.0.0"


class RealWorldAIRiskRequest(BaseModel):
    battery_soc: float = Field(..., ge=0, le=100)
    battery_voltage: float = Field(..., gt=0)
    speed: float = Field(..., ge=0)
    battery_temp: float


@router.post("/train")
def train_anomaly_model(
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text("""
            SELECT battery, temp, speed
            FROM ev_data
            WHERE battery IS NOT NULL
              AND temp IS NOT NULL
              AND speed IS NOT NULL
            ORDER BY timestamp
        """)
    ).mappings().all()

    try:
        return EVAnomalyModel().train(
            [dict(row) for row in rows]
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/status")
def ai_status():
    try:
        model = EVAnomalyModel(
            model_path=REAL_WORLD_MODEL_PATH,
            model_version=REAL_WORLD_MODEL_VERSION,
            features=[
                "battery_soc",
                "battery_voltage",
                "speed",
                "battery_temp",
            ],
        )
        return model.status()
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"AI model unavailable: {exc}",
        ) from exc

@router.get("/vehicle/{vehicle_id}/risk")
def vehicle_risk(
    vehicle_id: str,
    db: Session = Depends(get_db),
):
    value = vehicle_id.strip().upper()

    if not value:
        raise HTTPException(
            status_code=400,
            detail="vehicle_id must not be empty",
        )

    row = db.execute(
        text("""
            SELECT
                vehicle_id,
                battery,
                temp,
                speed,
                timestamp
            FROM ev_data
            WHERE vehicle_id = :vehicle_id
            ORDER BY timestamp DESC
            LIMIT 1
        """),
        {"vehicle_id": value},
    ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found",
        )

    try:
        prediction = EVAnomalyModel().predict(
            dict(row)
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"AI model unavailable: {exc}",
        ) from exc

    return {
        "vehicle_id": value,
        "timestamp": row["timestamp"],
        **prediction,
    }


@router.post("/real-world/risk")
def real_world_ai_risk(
    payload: RealWorldAIRiskRequest,
):
    model = EVAnomalyModel(
        model_path=REAL_WORLD_MODEL_PATH,
        model_version=REAL_WORLD_MODEL_VERSION,
        features=[
            "battery_soc",
            "battery_voltage",
            "speed",
            "battery_temp",
        ],
    )

    try:
        result = model.predict(
            {
                "battery_soc": payload.battery_soc,
                "battery_voltage": payload.battery_voltage,
                "speed": payload.speed,
                "battery_temp": payload.battery_temp,
            }
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Real-world AI model unavailable: {exc}",
        ) from exc

    return {
        "model_source": "TUMFTM/electric-vehicle-uds-dataset",
        "model_version": result["model_version"],
        "model_id": result["model_id"],
        "trained_at": result["trained_at"],
        "algorithm": result["algorithm"],
        "is_anomaly": result["is_anomaly"],
        "anomaly_score": result["anomaly_score"],
        "features": result["features"],
    }


