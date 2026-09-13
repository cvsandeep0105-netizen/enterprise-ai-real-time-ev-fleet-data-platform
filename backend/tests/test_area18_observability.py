from app.observability.health import HealthStatus
from app.observability.service import (
    collect_health,
    health_response,
    readiness_response,
)


def healthy():
    return True, "ok"


def degraded():
    return False, "dependency degraded"


def broken():
    raise RuntimeError("boom")


def test_collect_health_all_healthy():
    result = collect_health(
        {
            "database": healthy,
            "kafka": healthy,
        }
    )

    assert result.status == HealthStatus.HEALTHY
    assert len(result.components) == 2


def test_collect_health_degraded():
    result = collect_health(
        {
            "database": healthy,
            "kafka": degraded,
        }
    )

    assert result.status == HealthStatus.DEGRADED


def test_collect_health_not_ready():
    result = collect_health(
        {
            "database": broken,
            "kafka": healthy,
        }
    )

    assert result.status == HealthStatus.NOT_READY
    assert result.components[0].status == HealthStatus.NOT_READY


def test_health_response_contract():
    result = health_response(
        {
            "application": healthy,
            "database": healthy,
        }
    )

    assert result["status"] == "HEALTHY"
    assert result["service"] == "EV Fleet Data Platform API"
    assert result["version"] == "1.0.0"
    assert set(result["components"]) == {
        "application",
        "database",
    }


def test_readiness_healthy():
    result, status = readiness_response(
        {
            "database": healthy,
        }
    )

    assert status == 200
    assert result["status"] == "READY"


def test_readiness_degraded():
    result, status = readiness_response(
        {
            "database": degraded,
        }
    )

    assert status == 200
    assert result["status"] == "READY"


def test_readiness_not_ready():
    result, status = readiness_response(
        {
            "database": broken,
        }
    )

    assert status == 503
    assert result["status"] == "NOT_READY"


def test_component_exception_is_captured():
    result = collect_health(
        {
            "database": broken,
        }
    )

    assert result.status == HealthStatus.NOT_READY
    assert "boom" in result.components[0].message


def test_existing_root_still_available():
    from app.main import app

    paths = {
        route.path.rstrip("/") or "/"
        for route in app.routes
        if hasattr(route, "path")
    }

    assert "/" in paths


def test_observability_routes_available():
    from app.main import app

    paths = {
        route.path.rstrip("/") or "/"
        for route in app.routes
        if hasattr(route, "path")
    }

    assert "/health" in paths
    assert "/ready" in paths


def test_health_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] in {
        "HEALTHY",
        "DEGRADED",
        "NOT_READY",
    }


def test_ready_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/ready")

    assert response.status_code in {200, 503}
    assert response.json()["status"] in {
        "READY",
        "NOT_READY",
    }


def test_health_is_read_only():
    first = health_response({"database": healthy})
    second = health_response({"database": healthy})

    assert first["components"]["database"]["status"] == "HEALTHY"
    assert second["components"]["database"]["status"] == "HEALTHY"
