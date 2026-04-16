import pytest


async def test_login_success(client, test_user):
    resp = await client.post("/api/v1/auth/login", json={
        "employee_id": "testuser",
        "password": "testpass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client, test_user):
    resp = await client.post("/api/v1/auth/login", json={
        "employee_id": "testuser",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


async def test_login_unknown_user(client):
    resp = await client.post("/api/v1/auth/login", json={
        "employee_id": "nobody",
        "password": "anything",
    })
    assert resp.status_code == 401


async def test_me(client, test_user, auth_headers):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["employee_id"] == "testuser"
    assert data["display_name"] == "Test User"
    assert data["is_admin"] is False


async def test_me_no_token(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_refresh_token(client, test_user):
    login = await client.post("/api/v1/auth/login", json={
        "employee_id": "testuser",
        "password": "testpass123",
    })
    refresh_token = login.json()["refresh_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_refresh_with_access_token_fails(client, auth_headers):
    access_token = auth_headers["Authorization"].split(" ")[1]
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401
