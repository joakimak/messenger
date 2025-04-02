import pytest

from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from service.source.api import app
from service.source.repository import Message


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@patch("service.source.api.message_repository")
def test_post_message_success(message_repository, client):
    message = Message(username="john.doe", content="Hello, world!")
    message.id = 1

    message_repository.create_message = AsyncMock(return_value=message)

    payload = {"username": "john.doe", "content": "Hello, world!"}

    response = client.post("/message/", json=payload)
    data = response.json()

    assert response.status_code == 201
    assert data["username"] == "john.doe"
    assert data["content"] == "Hello, world!"
    assert "is_read" in data
    assert "created_at" in data


@patch("service.source.api.message_repository")
def test_post_message_server_error(message_repository, client):
    message_repository.create_message.side_effect = Exception("Database error")

    payload = {"username": "john.doe", "content": "Hello, world!"}

    response = client.post("/message/", json=payload)
    data = response.json()

    assert response.status_code == 500
    assert data == {"detail": "Internal server error"}


@patch("service.source.api.message_repository")
def test_post_message_value_error(message_repository, client):
    message_repository.create_message.side_effect = ValueError("Invalid request")

    payload = {"username": "john.doe", "content": "Hello, world!"}

    response = client.post("/message/", json=payload)
    data = response.json()

    assert response.status_code == 400
    assert data == {"detail": "Bad request"}
