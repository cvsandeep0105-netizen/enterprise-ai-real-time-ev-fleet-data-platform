"""Area 20 API governance tests."""

from app.governance import (
    API_PREFIX,
    API_VERSION,
    APIError,
    error_response,
    governance_metadata,
)


def test_api_version_contract():
    assert API_VERSION == "v1"
    assert API_PREFIX == "/api/v1"


def test_error_contract():
    result = error_response(
        "VALIDATION_ERROR",
        "Invalid request",
    )

    assert result["error"]["code"] == "VALIDATION_ERROR"
    assert result["error"]["message"] == "Invalid request"


def test_error_contract_with_details():
    result = error_response(
        "VALIDATION_ERROR",
        "Invalid request",
        {"field": "vehicle_id"},
    )

    assert result["error"]["details"]["field"] == "vehicle_id"


def test_error_rejects_empty_code():
    import pytest

    with pytest.raises(ValueError):
        error_response("", "Invalid request")


def test_error_rejects_empty_message():
    import pytest

    with pytest.raises(ValueError):
        error_response("VALIDATION_ERROR", "")


def test_api_error_dataclass():
    error = APIError(
        code="NOT_FOUND",
        message="Vehicle not found",
    )

    assert error.to_dict()["error"]["code"] == "NOT_FOUND"


def test_governance_metadata():
    metadata = governance_metadata()

    assert metadata["api_version"] == "v1"
    assert metadata["api_prefix"] == "/api/v1"
    assert metadata["contract"] == "enterprise"
    assert metadata["error_format"] == "standardized"
