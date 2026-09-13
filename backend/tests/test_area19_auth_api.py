import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.auth import router


def test_auth_router_exists():
    assert router is not None
    assert any(
        getattr(route, "path", "") == "/auth/login"
        for route in router.routes
    )


def test_login_route_contract():
    paths = {
        route.path.rstrip("/") or "/"
        for route in router.routes
        if hasattr(route, "path")
    }

    assert "/auth/login" in paths


def test_login_schema_rejects_empty_username():
    client_app = FastAPI()
    client_app.include_router(router)

    response = TestClient(client_app).post(
        "/auth/login",
        json={"username": "", "password": "password"},
    )

    assert response.status_code == 422


def test_login_schema_rejects_empty_password():
    client_app = FastAPI()
    client_app.include_router(router)

    response = TestClient(client_app).post(
        "/auth/login",
        json={"username": "admin", "password": ""},
    )

    assert response.status_code == 422


def test_user_model_has_authentication_fields():
    from app.models.database_models import User

    assert User.__tablename__ == "users"
    assert hasattr(User, "username")
    assert hasattr(User, "password_hash")
    assert hasattr(User, "role")
    assert hasattr(User, "is_active")


def test_auth_service_exports():
    from app.services.auth_service import (
        authenticate_user,
        create_user,
        issue_user_token,
    )

    assert callable(authenticate_user)
    assert callable(create_user)
    assert callable(issue_user_token)
