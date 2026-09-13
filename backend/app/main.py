from fastapi import FastAPI

from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware

from app.api.vehicles import router as vehicles_router
from app.api.dashboard import router as dashboard_router
from app.api.analytics import router as analytics_router
from app.api.telemetry import router as telemetry_router
from app.api.alerts import router as alerts_router
from app.api.auth import router as auth_router
from app.observability.api import router as observability_router
from app.api.ai import router as ai_router


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(vehicles_router)
    application.include_router(dashboard_router)
    application.include_router(analytics_router)
    application.include_router(telemetry_router)
    application.include_router(alerts_router)
    application.include_router(auth_router)
    application.include_router(observability_router)
    application.include_router(ai_router)

    @application.get("/")
    def home():
        return {"message": "Welcome to EV Fleet Data Platform API"}

    return application


app = create_application()

