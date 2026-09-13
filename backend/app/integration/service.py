from __future__ import annotations

from dataclasses import dataclass
from fastapi import FastAPI


@dataclass(frozen=True)
class IntegrationStatus:
    service: str
    version: str
    status: str


def inspect_application(app: FastAPI) -> IntegrationStatus:
    if not isinstance(app, FastAPI):
        raise TypeError("app must be a FastAPI application")
    return IntegrationStatus(
        service=app.title,
        version=app.version,
        status="READY",
    )


def application_routes(app: FastAPI) -> list[str]:
    if not isinstance(app, FastAPI):
        raise TypeError("app must be a FastAPI application")

    return sorted({
        str(route.path).rstrip("/") or "/"
        for route in app.routes
        if hasattr(route, "path")
    })


def has_route(app: FastAPI, path: str) -> bool:
    if not path or not path.strip():
        raise ValueError("path must not be empty")

    requested = path.rstrip("/") or "/"

    return requested in application_routes(app)


def integration_summary(app: FastAPI) -> dict:
    status = inspect_application(app)
    routes = application_routes(app)

    return {
        "service": status.service,
        "version": status.version,
        "status": status.status,
        "route_count": len(routes),
    }
