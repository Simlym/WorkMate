import pytest


async def test_list_conversations_empty(client, test_user, auth_headers):
    resp = await client.get("/api/v1/conversations", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_create_conversation(client, test_user, auth_headers):
    resp = await client.post("/api/v1/conversations", headers=auth_headers, json={
        "title": "My first chat",
        "function": None,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "My first chat"
    assert "id" in data


async def test_list_conversations_after_create(client, test_user, auth_headers):
    await client.post("/api/v1/conversations", headers=auth_headers, json={"title": "Chat 1"})
    await client.post("/api/v1/conversations", headers=auth_headers, json={"title": "Chat 2"})

    resp = await client.get("/api/v1/conversations", headers=auth_headers)
    assert resp.status_code == 200
    titles = [c["title"] for c in resp.json()]
    assert "Chat 1" in titles
    assert "Chat 2" in titles


async def test_get_conversation(client, test_user, auth_headers):
    create = await client.post("/api/v1/conversations", headers=auth_headers, json={"title": "Detail chat"})
    conv_id = create.json()["id"]

    resp = await client.get(f"/api/v1/conversations/{conv_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Detail chat"
    assert "messages" in resp.json()


async def test_get_conversation_not_found(client, test_user, auth_headers):
    resp = await client.get("/api/v1/conversations/99999", headers=auth_headers)
    assert resp.status_code == 404


async def test_update_conversation(client, test_user, auth_headers):
    create = await client.post("/api/v1/conversations", headers=auth_headers, json={"title": "Old title"})
    conv_id = create.json()["id"]

    resp = await client.patch(f"/api/v1/conversations/{conv_id}", headers=auth_headers, json={"title": "New title"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "New title"


async def test_delete_conversation(client, test_user, auth_headers):
    create = await client.post("/api/v1/conversations", headers=auth_headers, json={"title": "To delete"})
    conv_id = create.json()["id"]

    resp = await client.delete(f"/api/v1/conversations/{conv_id}", headers=auth_headers)
    assert resp.status_code == 204

    get_resp = await client.get(f"/api/v1/conversations/{conv_id}", headers=auth_headers)
    assert get_resp.status_code == 404


async def test_conversations_isolated_between_users(client, test_user, admin_user, auth_headers, admin_headers):
    # Create a conversation as test_user
    await client.post("/api/v1/conversations", headers=auth_headers, json={"title": "User conv"})

    # admin_user should see an empty list
    resp = await client.get("/api/v1/conversations", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_create_conversation_requires_auth(client):
    resp = await client.post("/api/v1/conversations", json={"title": "No auth"})
    assert resp.status_code == 403
