from kafka import KafkaProducer
import json
import time
import random
from datetime import datetime

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

while True:
    telemetry = {
        "vehicle_id": f"EV-{random.randint(1,20):03}",
        "battery": random.randint(5,100),
        "speed": random.randint(0,120),
        "temperature": random.randint(20,55),
        "latitude": 17.3850,
        "longitude": 78.4867,
        "status": "Running",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    producer.send("telemetry", telemetry)
    producer.flush()

    print("Sent:", telemetry)

    time.sleep(2)