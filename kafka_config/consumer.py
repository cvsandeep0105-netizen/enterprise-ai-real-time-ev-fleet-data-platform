from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    "telemetry",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="earliest",
    group_id="ev-fleet-group",
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)

print("Kafka Consumer Started...")

for message in consumer:
    telemetry = message.value

    print("=" * 50)
    print("Received from Kafka")
    print(telemetry)