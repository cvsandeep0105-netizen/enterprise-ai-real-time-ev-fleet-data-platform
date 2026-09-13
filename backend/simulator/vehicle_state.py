import random

from simulator.config import (
    TOTAL_VEHICLES,
    MIN_BATTERY,
    MAX_BATTERY,
    MIN_SPEED,
    MAX_SPEED,
    STATUS,
    LOCATIONS,
)

# Stores the current state of every vehicle
vehicle_states = {}

# Create initial state for all vehicles
for vehicle_id in range(1, TOTAL_VEHICLES + 1):
    city, latitude, longitude = random.choice(LOCATIONS)

    vehicle_states[f"EV-{vehicle_id:03}"] = {
        "battery": random.randint(MIN_BATTERY, MAX_BATTERY),
        "speed": random.randint(MIN_SPEED, MAX_SPEED),
        "status": random.choice(STATUS),
        "city": city,
        "latitude": latitude,
        "longitude": longitude,
    }


def get_vehicle_state(vehicle_id):
    """
    Returns the current state of a vehicle.
    """
    return vehicle_states[vehicle_id]