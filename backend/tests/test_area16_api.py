from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_endpoint_exists():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in {
        "HEALTHY",
        "DEGRADED",
        "NOT_READY",
    }


def test_readiness_endpoint_exists():
    response = client.get("/ready")
    assert response.status_code in {200, 503}


def test_openapi_available():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "paths" in data


def test_api_has_vehicle_routes():
    response = client.get("/openapi.json")
    paths = response.json()["paths"]
    assert any("/vehicles" in path for path in paths)


def test_api_has_analytics_routes():
    response = client.get("/openapi.json")
    paths = response.json()["paths"]
    assert any("/analytics" in path for path in paths)


def test_api_has_dashboard_routes():
    response = client.get("/openapi.json")
    paths = response.json()["paths"]
    assert any("/dashboard" in path for path in paths)


def test_api_has_alert_routes():
    response = client.get("/openapi.json")
    paths = response.json()["paths"]
    assert any("/alerts" in path for path in paths)


def test_api_has_telemetry_route():
    response = client.get("/openapi.json")
    paths = response.json()["paths"]
    assert any("/telemetry" in path for path in paths)


def test_invalid_vehicle_id_returns_client_error():
    response = client.get("/vehicles/not-a-real-id")
    assert response.status_code in {400, 404, 422, 500}


def test_docs_available():
    response = client.get("/docs")
    assert response.status_code == 200

