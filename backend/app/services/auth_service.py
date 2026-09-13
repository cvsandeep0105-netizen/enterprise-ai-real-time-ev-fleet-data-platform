"""Authentication service."""

from sqlalchemy.orm import Session

from app.models.database_models import User
from app.security import create_access_token, hash_password, verify_password


def authenticate_user(
    db: Session,
    username: str,
    password: str,
):
    user = (
        db.query(User)
        .filter(User.username == username.strip())
        .first()
    )

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def create_user(
    db: Session,
    username: str,
    password: str,
    role: str = "user",
):
    username = username.strip()
    role = role.strip().lower()

    if not username:
        raise ValueError("username must not be empty")

    if not password:
        raise ValueError("password must not be empty")

    if not role:
        raise ValueError("role must not be empty")

    existing = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if existing is not None:
        raise ValueError("username already exists")

    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def issue_user_token(user: User) -> str:
    return create_access_token(
        username=user.username,
        role=user.role,
    )
