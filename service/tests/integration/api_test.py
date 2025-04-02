import pytest
from fastapi.testclient import TestClient

from service.source import api
from service.source.api import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.asyncio
async def test_post_message(message_repository, client):
    api.message_repository = message_repository
    payload = {"username": "john.doe", "content": "Hello, world!"}

    response = client.post("/message/", json=payload)
    data = response.json()

    assert response.status_code is 201
    assert data["username"] == "john.doe"
    assert data["content"] == "Hello, world!"
    assert "is_read" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_post_message_invalid_request(message_repository, client):
    api.message_repository = message_repository
    payload = {"username": "john.doe"}

    response = client.post("/message/", json=payload)
    assert response.status_code == 422
