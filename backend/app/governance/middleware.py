"""Area 20 API governance integration."""

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.governance import API_VERSION, governance_metadata


_GOVERNANCE_INSTALLED = "_area20_governance_installed"


def install_governance(application: FastAPI) -> FastAPI:
    """Install API governance exactly once on a FastAPI application."""

    if not isinstance(application, FastAPI):
        raise TypeError("application must be a FastAPI instance")

    if getattr(application.state, _GOVERNANCE_INSTALLED, False):
        return application

    application.state.api_version = API_VERSION
    application.state.governance = governance_metadata()
    setattr(application.state, _GOVERNANCE_INSTALLED, True)

    @application.middleware("http")
    async def governance_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())

        try:
            response = await call_next(request)
        except Exception:
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "Internal server error",
                    },
                    "request_id": request_id,
                    "api_version": API_VERSION,
                },
            )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-API-Version"] = API_VERSION

        return response

    return application


__all__ = ["install_governance"]
