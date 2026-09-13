"""
Area 18 - Platform Observability & Health.

Foundation module for production-grade application health,
readiness, and component status reporting.
"""
from dataclasses import dataclass
from enum import Enum


class HealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    NOT_READY = "NOT_READY"


@dataclass(frozen=True)
class ComponentHealth:
    name: str
    status: HealthStatus
    message: str


@dataclass(frozen=True)
class PlatformHealth:
    status: HealthStatus
    service: str
    version: str
    components: tuple[ComponentHealth, ...]


__all__ = [
    "HealthStatus",
    "ComponentHealth",
    "PlatformHealth",
]
