import time

import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine, SQLModel, Session
from sqlmodel.pool import StaticPool

from ..main import app, get_password_hash
from ..dependencies import get_session
from ..models import Message


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_sign_up(client: TestClient) -> None:
    resp = client.post("/sign_up", json={"name": "test_user", "password": "test_password"})
    data = resp.json()
    assert resp.status_code == 201
    assert data["name"] == "test_user"


def test_sign_in(client: TestClient) -> None:
    client.post("/sign_up", json={"name": "test_user", "password": "test_password"})
    resp = client.post("/sign_in", data={"username": "test_user", "password": "test_password"})
    data = resp.json()
    assert resp.status_code == 200
    assert data["token_type"] == "bearer"
    assert data["access_token"]


def test_create_new_message(client: TestClient) -> None:
    client.post("/sign_up", json={"name": "test_user", "password": "test_password"})
    token = client.post(
        "/sign_in", data={"username": "test_user", "password": "test_password"}
    ).json()["access_token"]
    resp = client.post(
        "/messages", json={"content": "Test Message"}, headers={"Authorization": f"Bearer {token}"}
    )
    data = resp.json()
    assert resp.status_code == 201
    assert data["content"] == "Test Message"
