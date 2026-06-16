# import pytest
from fastapi import status

def test_register_success(client, test_user_data):
    resp = client.post("/api/v1/auth/register", json=test_user_data)
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json() == {"message": "User created"}

def test_register_duplicate_email(client, test_user_data):
    client.post("/api/v1/auth/register", json=test_user_data)
    resp = client.post("/api/v1/auth/register", json=test_user_data)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in resp.json()["detail"]

def test_register_invalid_email(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "not-an-email",
        "password": "pass123"
    })
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_login_success(client, test_user_data):
    client.post("/api/v1/auth/register", json=test_user_data)
    resp = client.post("/api/v1/auth/login", json=test_user_data)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client, test_user_data):
    client.post("/api/v1/auth/register", json=test_user_data)
    resp = client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": "wrong_password"
    })
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

def test_login_nonexistent_user(client):
    resp = client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "pass123"
    })
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
