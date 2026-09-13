from pathlib import Path

from app.ai.anomaly import (
    DEFAULT_MODEL_PATH,
    EVAnomalyModel,
    FEATURES,
)


def test_ai_feature_contract():
    assert FEATURES == ["battery", "temp", "speed"]


def test_ai_default_model_path_is_configurable():
    assert "models" in str(DEFAULT_MODEL_PATH)


def test_ai_model_trains_and_persists(tmp_path):
    rows = [
        {
            "battery": 70 + (i % 10) * 0.1,
            "temp": 25 + (i % 5) * 0.1,
            "speed": 40 + (i % 8) * 0.2,
        }
        for i in range(100)
    ]

    model_path = tmp_path / "model.joblib"

    model = EVAnomalyModel(
        model_path=model_path,
        model_version="test-1.0.0",
    )

    result = model.train(rows)

    assert result["algorithm"] == "IsolationForest"
    assert result["training_rows"] == 100
    assert result["model_version"] == "test-1.0.0"
    assert result["model_id"]
    assert result["trained_at"]
    assert result["artifact_size_bytes"] > 0
    assert result["artifact_sha256"]
    assert Path(model_path).exists()

    prediction = model.predict(rows[0])

    assert isinstance(prediction["is_anomaly"], bool)
    assert isinstance(prediction["anomaly_score"], float)
    assert prediction["model_version"] == "test-1.0.0"
    assert prediction["model_id"] == result["model_id"]


def test_ai_model_rejects_small_dataset(tmp_path):
    model = EVAnomalyModel(tmp_path / "model.joblib")

    try:
        model.train(
            [
                {
                    "battery": 70,
                    "temp": 25,
                    "speed": 40,
                }
                for _ in range(10)
            ]
        )
    except ValueError as exc:
        assert "50" in str(exc)
    else:
        raise AssertionError(
            "Small training dataset was accepted"
        )


def test_ai_status_contains_artifact_metadata(tmp_path):
    rows = [
        {
            "battery": 70 + (i % 10) * 0.1,
            "temp": 25 + (i % 5) * 0.1,
            "speed": 40 + (i % 8) * 0.2,
        }
        for i in range(100)
    ]

    model = EVAnomalyModel(
        tmp_path / "model.joblib",
        model_version="2.0.0",
    )

    trained = model.train(rows)

    loaded = EVAnomalyModel(
        tmp_path / "model.joblib",
        model_version="2.0.0",
    )

    status = loaded.status()

    assert status["artifact_exists"] is True
    assert status["model_version"] == "2.0.0"
    assert status["model_id"] == trained["model_id"]
    assert status["artifact_size_bytes"] > 0
    assert len(status["artifact_sha256"]) == 64
