"""Production authentication primitives for the EV Fleet Data Platform."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash

from app.core.config import settings

ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_access_token_expire_minutes
password_hasher = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    username: str
    role: str


def hash_password(password: str) -> str:
    if not isinstance(password, str) or not password:
        raise ValueError("password must not be empty")
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if not isinstance(password, str) or not password:
        return False
    if not isinstance(password_hash, str) or not password_hash:
        return False
    return password_hasher.verify(password, password_hash)


def _secret_key() -> str:
    value = settings.jwt_secret_key
    if not value or len(value) < 32:
        raise ValueError("JWT secret key must contain at least 32 characters")
    return value


def create_access_token(
    username: str,
    role: str = "user",
    expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    if not isinstance(username, str) or not username.strip():
        raise ValueError("username must not be empty")
    if not isinstance(role, str) or not role.strip():
        raise ValueError("role must not be empty")
    if expires_minutes <= 0:
        raise ValueError("expires_minutes must be positive")

    now = datetime.now(timezone.utc)
    payload = {
        "sub": username.strip(),
        "role": role.strip().lower(),
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, _secret_key(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> AuthenticatedUser:
    if not isinstance(token, str) or not token.strip():
        raise ValueError("token must not be empty")

    try:
        payload = jwt.decode(token, _secret_key(), algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise ValueError("invalid access token") from exc

    username = payload.get("sub")
    role = payload.get("role")

    if not username or not role:
        raise ValueError("token missing required claims")

    return AuthenticatedUser(username=str(username), role=str(role))


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return decode_access_token(credentials.credentials)
    except (ValueError, jwt.PyJWTError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_roles(*allowed_roles: str):
    normalized = {role.strip().lower() for role in allowed_roles if isinstance(role, str) and role.strip()}
    if not normalized:
        raise ValueError("at least one role is required")

    def dependency(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if user.role not in normalized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency
