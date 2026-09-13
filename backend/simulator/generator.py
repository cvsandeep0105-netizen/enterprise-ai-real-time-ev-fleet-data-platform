import random
from datetime import datetime

from simulator.config import (
    MAX_SPEED,
    MAX_TEMPERATURE,
    MIN_SPEED,
    MIN_TEMPERATURE,
)

from simulator.vehicle_state import get_vehicle_state


def generate_vehicle_data(vehicle_id):
    vehicle_key = f"EV-{vehicle_id:03}"

    state = get_vehicle_state(vehicle_key)

    # Battery slowly drains
    state["battery"] = max(0, state["battery"] - random.randint(0, 2))

    # Speed changes gradually
    state["speed"] += random.randint(-10, 10)
    state["speed"] = max(MIN_SPEED, min(MAX_SPEED, state["speed"]))

    # Temperature changes gradually
    temperature = random.randint(MIN_TEMPERATURE, MAX_TEMPERATURE)

    # Automatic Status
    if state["battery"] <= 20:
        state["status"] = "Low Battery"
    elif state["speed"] == 0:
        state["status"] = "Idle"
    else:
        state["status"] = "Running"

    return {
        "vehicle_id": vehicle_key,
        "battery": state["battery"],
        "speed": state["speed"],
        "temperature": temperature,
        "status": state["status"],
        "city": state["city"],
        "latitude": state["latitude"],
        "longitude": state["longitude"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }