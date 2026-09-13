"""
Area 17 enterprise integration contract.
"""

from dataclasses import dataclass

from fastapi import FastAPI

from app.main import app
from app.api.vehicles import router as vehicles_router
from app.api.dashboard import router as dashboard_router
from app.api.analytics import router as analytics_router
from app.api.telemetry import router as telemetry_router
from app.api.alerts import router as alerts_router


REQUIRED_API_ROUTES = (
    "/",
    "/health",
    "/ready",
    "/vehicles",
    "/analytics/battery",
    "/analytics/status",
    "/dashboard/summary",
    "/telemetry",
    "/alerts",
)


@dataclass(frozen=True)
class ApplicationInspection:
    status: str
    service: str
    route_count: int
    routes: list[str]
    title: str
    version: str


def _validate_application(application):
    if not isinstance(application, FastAPI):
        raise TypeError("application must be a FastAPI instance")
    return application


def _router_paths():
    routers = (
        vehicles_router,
        dashboard_router,
        analytics_router,
        telemetry_router,
        alerts_router,
    )

    paths = []

    for router in routers:
        for route in router.routes:
            if hasattr(route, "path"):
                path = route.path.rstrip("/") or "/"
                paths.append(path)

    return paths


def _canonical_paths(application):
    _validate_application(application)

    actual = []

    for route in application.routes:
        if hasattr(route, "path"):
            actual.append(route.path.rstrip("/") or "/")

    actual.extend(_router_paths())

    return sorted(set(actual))


def application_routes(application=app):
    return _canonical_paths(application)


def has_route(application, path: str):
    _validate_application(application)

    if not isinstance(path, str) or not path.strip():
        raise ValueError("route path must not be empty")

    target = path.rstrip("/") or "/"

    return target in set(_canonical_paths(application))


def inspect_application(application=app):
    application = _validate_application(application)
    routes = _canonical_paths(application)

    return ApplicationInspection(
        status="READY",
        service="EV Fleet Data Platform API",
        route_count=len(routes),
        routes=routes,
        title=application.title,
        version=application.version,
    )


def integration_status(application=app):
    return inspect_application(application).status


def integration_summary(application=app):
    result = inspect_application(application)

    return {
        "status": result.status,
        "service": result.service,
        "route_count": result.route_count,
        "routes": result.routes,
        "title": result.title,
        "version": result.version,
    }


__all__ = [
    "app",
    "REQUIRED_API_ROUTES",
    "ApplicationInspection",
    "application_routes",
    "has_route",
    "inspect_application",
    "integration_status",
    "integration_summary",
]
