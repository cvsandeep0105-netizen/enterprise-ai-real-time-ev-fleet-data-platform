from pydantic import BaseModel

class VehicleCreate(BaseModel):
    vehicle_id: str
    battery: int
    speed: int
    status: str


class VehicleUpdate(BaseModel):
    battery: int
    speed: int
    status: str