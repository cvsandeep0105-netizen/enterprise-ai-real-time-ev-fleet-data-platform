from pathlib import Path
import hashlib
import json
import joblib
import numpy as np

ROOT = Path("/models")
MODEL = ROOT / "real_world_ev_anomaly_isolation_forest.joblib"
META = ROOT / "real_world_model_metadata.json"

EXPECTED_FEATURES = [
    "battery_soc",
    "battery_voltage",
    "speed",
    "battery_temp",
]

print("=" * 70)
print("AREA 30 - REAL-WORLD AI CANDIDATE VALIDATION")
print("=" * 70)

assert MODEL.exists()
assert META.exists()

model_bytes = MODEL.read_bytes()
sha256 = hashlib.sha256(model_bytes).hexdigest()
metadata = json.loads(META.read_text(encoding="utf-8"))

print("MODEL_EXISTS = PASS")
print("METADATA_EXISTS = PASS")
print("ARTIFACT_SIZE =", len(model_bytes))
print("ARTIFACT_SHA256 =", sha256)

assert metadata.get("artifact_sha256") == sha256
print("SHA256_INTEGRITY = PASS")

assert metadata.get("features") == EXPECTED_FEATURES
print("FEATURE_CONTRACT = PASS")

model = joblib.load(MODEL)
assert type(model).__name__ == "IsolationForest"
print("MODEL_LOAD = PASS")
print("MODEL_TYPE =", type(model).__name__)

X = np.array([
    [70.0, 360.0, 50.0, 30.0],
    [45.0, 350.0, 80.0, 35.0],
    [90.0, 370.0, 20.0, 25.0],
], dtype=float)

predictions = model.predict(X)
scores = model.decision_function(X)

assert len(predictions) == 3
assert len(scores) == 3
assert np.isfinite(predictions).all()
assert np.isfinite(scores).all()

print("INFERENCE = PASS")
print("PREDICTIONS =", predictions.tolist())
print("SCORES =", [round(float(x), 6) for x in scores])

print("TRAINING_ROWS =", metadata.get("training_rows"))
print("MODEL_METADATA_KEYS =", sorted(metadata.keys()))

print()
print("=" * 70)
print("REAL_WORLD_AI_CANDIDATE_VALIDATION = PASS")
print("=" * 70)
