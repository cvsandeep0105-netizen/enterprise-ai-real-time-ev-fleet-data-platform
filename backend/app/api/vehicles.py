from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.database import get_db
from app.schemas.vehicle import VehicleCreate, VehicleUpdate

router = APIRouter()


# ============================================================
# GET ALL CURRENT VEHICLES
# ============================================================

@router.get("/vehicles")
def get_vehicles(db: Session = Depends(get_db)):

    query = text("""
        SELECT DISTINCT ON (vehicle_id)
            vehicle_id,
            battery,
            speed,
            charging_status,
            vehicle_status,
            temperature_status,
            location,
            timestamp
        FROM ev_data
        ORDER BY vehicle_id, timestamp DESC
    """)

    result = db.execute(query).mappings().all()

    return [dict(row) for row in result]


# ============================================================
# GET CURRENT VEHICLE BY VEHICLE ID
# ============================================================

@router.get("/vehicles/{vehicle_id}")
def get_vehicle(
    vehicle_id: str,
    db: Session = Depends(get_db),
):
    normalized_vehicle_id = vehicle_id.strip().upper()

    if not normalized_vehicle_id:
        raise HTTPException(
            status_code=400,
            detail="vehicle_id must not be empty",
        )

    query = text("""
        SELECT DISTINCT ON (vehicle_id)
            vehicle_id,
            battery,
            speed,
            charging_status,
            vehicle_status,
            temperature_status,
            location,
            timestamp
        FROM ev_data
        WHERE UPPER(vehicle_id) = :vehicle_id
        ORDER BY vehicle_id, timestamp DESC
    """)

    result = db.execute(
        query,
        {"vehicle_id": normalized_vehicle_id},
    ).mappings().first()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found",
        )

    return dict(result)

# ============================================================
# CREATE VEHICLE
# ============================================================

@router.post("/vehicles")
def create_vehicle(
    vehicle: VehicleCreate,
    db: Session = Depends(get_db)
):

    query = text("""
        INSERT INTO vehicles (
            vehicle_id,
            battery,
            speed,
            status
        )
        VALUES (
            :vehicle_id,
            :battery,
            :speed,
            :status
        )
        RETURNING id, vehicle_id, battery, speed, status
    """)

    result = db.execute(
        query,
        {
            "vehicle_id": vehicle.vehicle_id,
            "battery": vehicle.battery,
            "speed": vehicle.speed,
            "status": vehicle.status,
        },
    )

    db.commit()

    return dict(result.mappings().one())


# ============================================================
# DELETE VEHICLE
# ============================================================

@router.delete("/vehicles/{vehicle_id}")
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db)
):

    query = text("""
        DELETE FROM vehicles
        WHERE id = :vehicle_id
        RETURNING id
    """)

    result = db.execute(
        query,
        {"vehicle_id": vehicle_id}
    )

    deleted = result.fetchone()

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )

    db.commit()

    return {
        "message": "Vehicle deleted successfully"
    }


# ============================================================
# UPDATE VEHICLE
# ============================================================

@router.put("/vehicles/{vehicle_id}")
def update_vehicle(
    vehicle_id: int,
    updated_vehicle: VehicleUpdate,
    db: Session = Depends(get_db)
):

    query = text("""
        UPDATE vehicles
        SET
            battery = :battery,
            speed = :speed,
            status = :status
        WHERE id = :vehicle_id
        RETURNING id, vehicle_id, battery, speed, status
    """)

    result = db.execute(
        query,
        {
            "vehicle_id": vehicle_id,
            "battery": updated_vehicle.battery,
            "speed": updated_vehicle.speed,
            "status": updated_vehicle.status,
        },
    )

    updated = result.mappings().first()

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )

    db.commit()

    return dict(updated)
