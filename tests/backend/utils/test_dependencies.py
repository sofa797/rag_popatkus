import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from backend.app.utils.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.core.security import create_access_token
from datetime import timedelta

def test_get_current_user_valid_token(db_session, test_user_data):
    user = User(email=test_user_data["email"], hashed_password="dummy_hash", id=999)
    db_session.add(user)
    db_session.commit()
    token = create_access_token(data={"sub": "999"}, expires_delta=timedelta(minutes=30))
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    result = get_current_user(credentials=credentials, db=db_session)
    assert result.id == 999
    assert result.email == test_user_data["email"]

def test_get_current_user_invalid_token(db_session):
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token.here")
    with pytest.raises(HTTPException) as exc:
        get_current_user(credentials=credentials, db=db_session)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_current_user_expired_token(db_session, test_user_data):
    user = User(email=test_user_data["email"], hashed_password="dummy", id=888)
    db_session.add(user)
    db_session.commit()
    token = create_access_token(data={"sub": "888"}, expires_delta=timedelta(seconds=-10))
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as exc:
        get_current_user(credentials=credentials, db=db_session)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_current_user_nonexistent_user(db_session):
    token = create_access_token(data={"sub": "99999"}, expires_delta=timedelta(minutes=30))
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as exc:
        get_current_user(credentials=credentials, db=db_session)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
