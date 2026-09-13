import random

# Number of vehicles to simulate
TOTAL_VEHICLES = 20

# Time interval (seconds)
UPDATE_INTERVAL = 2

# Battery Limits
MIN_BATTERY = 10
MAX_BATTERY = 100

# Speed Limits (km/h)
MIN_SPEED = 0
MAX_SPEED = 120

# Temperature Limits (°C)
MIN_TEMPERATURE = 20
MAX_TEMPERATURE = 45

# Vehicle Status
STATUS = [
    "Running",
    "Charging",
    "Idle",
    "Maintenance",
]

# Sample Cities (Latitude, Longitude)
LOCATIONS = [
    ("Bangalore", 12.9716, 77.5946),
    ("Hyderabad", 17.3850, 78.4867),
    ("Chennai", 13.0827, 80.2707),
    ("Mumbai", 19.0760, 72.8777),
    ("Delhi", 28.6139, 77.2090),
]