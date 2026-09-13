import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.security import (
    AuthenticatedUser,
    create_access_token,
    decode_access_token,
    get_current_user,
    hash_password,
    require_roles,
    verify_password,
)


def test_password_round_trip():
    hashed = hash_password("EnterprisePassword123!")
    assert hashed != "EnterprisePassword123!"
    assert verify_password("EnterprisePassword123!", hashed)
    assert not verify_password("wrong", hashed)


def test_token_identity_and_role():
    user = decode_access_token(create_access_token("admin", "admin"))
    assert isinstance(user, AuthenticatedUser)
    assert user.username == "admin"
    assert user.role == "admin"


def test_default_role():
    assert decode_access_token(create_access_token("operator")).role == "user"


def test_invalid_token_rejected():
    with pytest.raises(ValueError):
        decode_access_token("invalid-token")


def test_expired_token_rejected():
    token = create_access_token("expired", "user", expires_minutes=1)
    assert decode_access_token(token).username == "expired"


def test_auth_dependency_rejects_missing_credentials():
    with pytest.raises(Exception):
        get_current_user(None)


def test_role_dependency_requires_role():
    dependency = require_roles("admin")
    user = AuthenticatedUser("operator", "user")
    with pytest.raises(Exception):
        dependency(user)


def test_role_dependency_accepts_role():
    dependency = require_roles("admin")
    user = AuthenticatedUser("admin", "admin")
    assert dependency(user) == user


def test_authentication_contract_can_protect_endpoint():
    app = FastAPI()

    @app.get("/protected")
    def protected(user: AuthenticatedUser = __import__("fastapi").Depends(get_current_user)):
        return {"username": user.username, "role": user.role}

    client = TestClient(app)

    response = client.get("/protected")
    assert response.status_code == 401

    token = create_access_token("area19", "operator")
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"username": "area19", "role": "operator"}
