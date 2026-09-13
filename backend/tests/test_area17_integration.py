from fastapi.testclient import TestClient

from app.integration import (
    application_routes,
    has_route,
    inspect_application,
    integration_summary,
)
from app.main import app


client = TestClient(app)


def test_integration_status():
    result = inspect_application(app)
    assert result.status == "READY"
    assert result.service
    assert result.version


def test_application_routes():
    routes = application_routes(app)

    assert "/" in routes
    assert "/health" in routes
    assert "/ready" in routes
    assert has_route(app, "/vehicles")
    assert has_route(app, "/dashboard/summary")


def test_has_route():
    assert has_route(app, "/")
    assert has_route(app, "/health")
    assert has_route(app, "/ready")
    assert has_route(app, "/vehicles/")
    assert has_route(app, "/dashboard/summary/")


def test_invalid_application_rejected():
    try:
        inspect_application(None)
        assert False
    except TypeError:
        assert True


def test_empty_route_rejected():
    try:
        has_route(app, "")
        assert False
    except ValueError:
        assert True


def test_integration_summary():
    result = integration_summary(app)

    assert result["status"] == "READY"
    assert result["route_count"] > 0


def test_api_still_available():
    response = client.get("/openapi.json")
    assert response.status_code == 200


def test_api_root_still_available():
    response = client.get("/")
    assert response.status_code == 200


def test_area17_required_api_surface():
    paths = set(application_routes(app))

    required = {
        "/",
        "/health",
        "/ready",
        "/vehicles",
        "/analytics/battery",
        "/analytics/status",
        "/dashboard/summary",
        "/telemetry",
        "/alerts",
    }

    missing = sorted(required - paths)
    assert not missing, f"Missing API routes: {missing}"
