"""
Area 18 observability API.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.observability.service import (
    health_response,
    readiness_response,
)


router = APIRouter(tags=["Observability"])


@router.get("/health")
def health():
    return health_response()


@router.get("/ready")
def readiness():
    payload, status_code = readiness_response()
    return JSONResponse(
        content=payload,
        status_code=status_code,
    )


__all__ = ["router"]
