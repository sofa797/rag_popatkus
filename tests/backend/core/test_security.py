from backend.app.core.security import verify_password, get_password_hash, create_access_token, _hash_password
from backend.app.core.config import settings
from jose import jwt
import pytest
from datetime import timedelta

def test_password_hashing():
    password = "MySecurePass123!"
    hashed = get_password_hash(password)
    assert hashed == _hash_password(password)
    assert len(hashed) == 64

def test_verify_password_correct():
    password = "TestPass!"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True

def test_verify_password_incorrect():
    password = "TestPass!"
    hashed = get_password_hash(password)
    assert verify_password("WrongPass", hashed) is False

def test_create_access_token():
    data = {"sub": "123"}
    token = create_access_token(data, expires_delta=timedelta(minutes=15))
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == "123"
    assert "exp" in decoded
    assert isinstance(decoded["exp"], (int, float))

def test_access_token_expiration():
    data = {"sub": "123"}
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))
    with pytest.raises(Exception):
        jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
