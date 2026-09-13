import pytest

from app.security import (
    ALGORITHM,
    AuthenticatedUser,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_is_not_plaintext():
    password = "EnterprisePassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword!", hashed)


def test_password_hash_is_unique():
    password = "EnterprisePassword123!"

    assert hash_password(password) != hash_password(password)


def test_access_token_contains_identity():
    token = create_access_token("admin", "admin")
    user = decode_access_token(token)

    assert isinstance(user, AuthenticatedUser)
    assert user.username == "admin"
    assert user.role == "admin"


def test_access_token_default_role():
    token = create_access_token("operator")
    user = decode_access_token(token)

    assert user.username == "operator"
    assert user.role == "user"


def test_access_token_rejects_empty_username():
    with pytest.raises(ValueError):
        create_access_token("")


def test_access_token_rejects_empty_role():
    with pytest.raises(ValueError):
        create_access_token("admin", "")


def test_access_token_rejects_invalid_token():
    with pytest.raises(Exception):
        decode_access_token("not-a-valid-token")


def test_access_token_rejects_empty_token():
    with pytest.raises(ValueError):
        decode_access_token("")


def test_algorithm_contract():
    assert ALGORITHM == "HS256"
