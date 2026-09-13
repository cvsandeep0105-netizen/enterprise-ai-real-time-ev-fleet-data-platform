"""
Area 18 - Platform Observability Service.

Production-oriented health/readiness evaluation with injectable
component checks so API health endpoints remain deterministic
and testable.
"""

from collections.abc import Callable

from app.core.config import settings
from app.observability.health import (
    ComponentHealth,
    HealthStatus,
    PlatformHealth,
)


Check = Callable[[], tuple[bool, str]]


def _run_check(name: str, check: Check) -> ComponentHealth:
    try:
        healthy, message = check()

        if healthy:
            return ComponentHealth(
                name=name,
                status=HealthStatus.HEALTHY,
                message=message,
            )

        return ComponentHealth(
            name=name,
            status=HealthStatus.DEGRADED,
            message=message,
        )

    except Exception as exc:
        return ComponentHealth(
            name=name,
            status=HealthStatus.NOT_READY,
            message=f"Component check failed: {exc}",
        )


def check_application() -> tuple[bool, str]:
    return True, "Application process is running"


def check_database_configuration() -> tuple[bool, str]:
    required = (
        settings.postgres_user,
        settings.postgres_password,
        settings.postgres_host,
        settings.postgres_db,
    )

    if all(str(value).strip() for value in required):
        return True, "Database configuration is available"

    return False, "Database configuration is incomplete"


def check_kafka_configuration() -> tuple[bool, str]:
    if str(settings.kafka_broker).strip() and str(settings.kafka_topic).strip():
        return True, "Kafka configuration is available"

    return False, "Kafka configuration is incomplete"


def check_spark_configuration() -> tuple[bool, str]:
    try:
        import pyspark

        version = getattr(pyspark, "__version__", "unknown")
        return True, f"PySpark available ({version})"
    except Exception as exc:
        return False, f"PySpark unavailable: {exc}"


def collect_health(
    checks: dict[str, Check] | None = None,
) -> PlatformHealth:
    selected = checks or {
        "application": check_application,
        "database": check_database_configuration,
        "kafka": check_kafka_configuration,
        "spark": check_spark_configuration,
    }

    components = tuple(
        _run_check(name, check)
        for name, check in selected.items()
    )

    if any(
        component.status == HealthStatus.NOT_READY
        for component in components
    ):
        overall = HealthStatus.NOT_READY
    elif any(
        component.status == HealthStatus.DEGRADED
        for component in components
    ):
        overall = HealthStatus.DEGRADED
    else:
        overall = HealthStatus.HEALTHY

    return PlatformHealth(
        status=overall,
        service=settings.app_name,
        version=settings.app_version,
        components=components,
    )


def health_response(
    checks: dict[str, Check] | None = None,
) -> dict:
    result = collect_health(checks)

    return {
        "status": result.status.value,
        "service": result.service,
        "version": result.version,
        "components": {
            component.name: {
                "status": component.status.value,
                "message": component.message,
            }
            for component in result.components
        },
    }


def readiness_response(
    checks: dict[str, Check] | None = None,
) -> tuple[dict, int]:
    result = collect_health(checks)

    ready = result.status != HealthStatus.NOT_READY

    response = {
        "status": "READY" if ready else "NOT_READY",
        "service": result.service,
        "version": result.version,
        "components": {
            component.name: {
                "status": component.status.value,
                "message": component.message,
            }
            for component in result.components
        },
    }

    return response, 200 if ready else 503


__all__ = [
    "check_application",
    "check_database_configuration",
    "check_kafka_configuration",
    "check_spark_configuration",
    "collect_health",
    "health_response",
    "readiness_response",
]
