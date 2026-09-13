from app.ai.anomaly import EVAnomalyModel
from app.database.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    rows = db.execute(text("""
        SELECT battery, temp, speed
        FROM ev_data
        WHERE battery IS NOT NULL
          AND temp IS NOT NULL
          AND speed IS NOT NULL
        ORDER BY timestamp
    """)).mappings().all()

    print("Telemetry rows available:", len(rows))
    assert len(rows) >= 50, "Insufficient telemetry"

    model = EVAnomalyModel()
    result = model.train([dict(row) for row in rows])

    print("Training result:", result)
    print("Artifact exists:", model.model_path.exists())

    prediction = model.predict(dict(rows[0]))
    print("Sample prediction:", prediction)

    assert model.model_path.exists(), "Artifact missing"
    print("=== AREA 29 REAL TELEMETRY AI TRAINING: PASS ===")

finally:
    db.close()
