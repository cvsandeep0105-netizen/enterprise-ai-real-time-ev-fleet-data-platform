from pathlib import Path

from app.ai.anomaly import EVAnomalyModel, FEATURES


def test_ai_feature_contract():
    assert FEATURES == ["battery", "temp", "speed"]


def test_ai_model_trains_and_predicts(tmp_path):
    rows = [
        {
            "battery": 70 + (i % 10) * 0.1,
            "temp": 25 + (i % 5) * 0.1,
            "speed": 40 + (i % 8) * 0.2,
        }
        for i in range(100)
    ]

    model_path = tmp_path / "model.joblib"
    model = EVAnomalyModel(model_path)

    result = model.train(rows)

    assert result["algorithm"] == "IsolationForest"
    assert result["training_rows"] == 100
    assert Path(model_path).exists()

    prediction = model.predict(rows[0])

    assert prediction["algorithm"] == "IsolationForest"
    assert isinstance(prediction["is_anomaly"], bool)
    assert isinstance(prediction["anomaly_score"], float)


def test_ai_model_rejects_small_dataset(tmp_path):
    model = EVAnomalyModel(tmp_path / "model.joblib")

    try:
        model.train(
            [
                {"battery": 70, "temp": 25, "speed": 40}
                for _ in range(10)
            ]
        )
    except ValueError as exc:
        assert "50" in str(exc)
    else:
        raise AssertionError("Small training dataset was accepted")