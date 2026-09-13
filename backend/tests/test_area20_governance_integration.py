"""Area 20 governance integration tests."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.governance import API_VERSION
from app.governance.middleware import install_governance


def make_application():
    application = FastAPI(
        title="Area 20 Test API",
        version="1.0.0",
    )

    @application.get("/")
    def root():
        return {"status": "ok"}

    return application


def test_governance_state():
    application = make_application()

    install_governance(application)

    assert application.state.api_version == API_VERSION
    assert application.state.governance["contract"] == "enterprise"


def test_request_id_is_preserved():
    application = make_application()
    install_governance(application)

    client = TestClient(application)

    response = client.get(
        "/",
        headers={"X-Request-ID": "area20-test-request"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "area20-test-request"


def test_request_id_is_generated():
    application = make_application()
    install_governance(application)

    client = TestClient(application)

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")


def test_api_version_header():
    application = make_application()
    install_governance(application)

    client = TestClient(application)

    response = client.get("/")

    assert response.headers["X-API-Version"] == API_VERSION


def test_governance_installation_is_idempotent():
    application = make_application()

    first = install_governance(application)
    second = install_governance(application)

    assert first is application
    assert second is application
    assert application.state.api_version == "v1"


def test_openapi_remains_available():
    application = make_application()
    install_governance(application)

    response = TestClient(application).get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Area 20 Test API"


def test_governance_metadata_contract():
    application = make_application()
    install_governance(application)

    metadata = application.state.governance

    assert metadata["api_version"] == "v1"
    assert metadata["api_prefix"] == "/api/v1"
    assert metadata["contract"] == "enterprise"
    assert metadata["error_format"] == "standardized"
