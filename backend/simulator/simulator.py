import time
import requests

from simulator.config import (
    TOTAL_VEHICLES,
    UPDATE_INTERVAL,
)

from simulator.generator import generate_vehicle_data

API_URL = "http://127.0.0.1:8000/telemetry/"


def start_simulator():
    print("=" * 60)
    print("EV Telemetry Simulator Started")
    print("=" * 60)

    while True:
        for vehicle_id in range(1, TOTAL_VEHICLES + 1):

            vehicle = generate_vehicle_data(vehicle_id)

            try:
                response = requests.post(API_URL, json=vehicle)

                if response.status_code == 200:
                    print(f"✅ Sent {vehicle['vehicle_id']}")
                else:
                    print(
                        f"❌ Failed {vehicle['vehicle_id']} "
                        f"{response.status_code}"
                    )

            except Exception as e:
                print("Connection Error:", e)

        print("-" * 60)

        time.sleep(UPDATE_INTERVAL)


if __name__ == "__main__":
    start_simulator()