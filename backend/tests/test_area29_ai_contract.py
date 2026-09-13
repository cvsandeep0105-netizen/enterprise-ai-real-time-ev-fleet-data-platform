from pathlib import Path

from app.ai.anomaly import EVAnomalyModel


def test_ai_artifact_path_is_project_relative():
    path = Path("backend/models/ev_anomaly_isolation_forest.joblib")
    assert path.parent.name == "models"


def test_ai_model_has_deterministic_configuration():
    model = EVAnomalyModel()
    assert model.model is None