"""Area 20 - API governance foundation."""

from dataclasses import dataclass
from typing import Any


API_VERSION = "v1"
API_PREFIX = "/api/v1"


@dataclass(frozen=True)
class APIError:
    code: str
    message: str
    details: Any = None

    def to_dict(self) -> dict:
        result = {
            "error": {
                "code": self.code,
                "message": self.message,
            }
        }
        if self.details is not None:
            result["error"]["details"] = self.details
        return result


def error_response(
    code: str,
    message: str,
    details: Any = None,
) -> dict:
    if not isinstance(code, str) or not code.strip():
        raise ValueError("error code must not be empty")

    if not isinstance(message, str) or not message.strip():
        raise ValueError("error message must not be empty")

    return APIError(
        code=code.strip(),
        message=message.strip(),
        details=details,
    ).to_dict()


def governance_metadata() -> dict:
    return {
        "api_version": API_VERSION,
        "api_prefix": API_PREFIX,
        "contract": "enterprise",
        "error_format": "standardized",
    }


__all__ = [
    "API_VERSION",
    "API_PREFIX",
    "APIError",
    "error_response",
    "governance_metadata",
]
