import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from ..main import app
from ..config import get_settings
from ..database import get_session, create_admin


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False},
        poolclass=StaticPool
        )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        create_admin(engine)
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="admin_token")
def access_token_fixture(client):
    settings = get_settings()
    credentials = {"username": settings.admin_email,
                   "password": settings.admin_password}
    response = client.post(url="api/v1/login/token", data=credentials)
    access_token = response.json()["access_token"]
    return access_token


@pytest.fixture(name="admin_auth_header")
def authorization_headers_fixture(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


def test_create_waste(client, admin_auth_header):
    response = client.post(
        url="api/v1/wastes/create/", headers=admin_auth_header,
        json={"name": "Bio"}
        )
    data = response.json()
    assert response.status_code == 200
    assert data["name"] == "Bio"
    assert data["id"] is not None


def test_get_waste(client, admin_auth_header):
    # Create waste
    response = client.post(
        url="api/v1/wastes/create/", headers=admin_auth_header,
        json={"name": "Bio"}
        )
    waste_id = response.json()["id"]
    # Get waste
    response = client.get(
        url=f"api/v1/wastes/{waste_id}/", headers=admin_auth_header)
    data = response.json()
    assert response.status_code == 200
    assert data["id"] == waste_id
    # Get nonexisted waste
    response = client.get(
        url=f"api/v1/wastes/{waste_id + 1}/", headers=admin_auth_header)
    assert response.status_code == 404


def test_get_wastes(client, admin_auth_header):
    # Create wastes
    client.post(
        url="api/v1/wastes/create/", headers=admin_auth_header,
        json={"name": "Bio"}
        )
    client.post(
        url="api/v1/wastes/create/", headers=admin_auth_header,
        json={"name": "Plastic"}
        )
    # Get wastes
    response = client.get(
        url="api/v1/wastes/", headers=admin_auth_header)
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2


def test_delete_waste(client, admin_auth_header):
    # Create waste
    response = client.post(
        url="api/v1/wastes/create/", headers=admin_auth_header,
        json={"name": "Bio"}
        )
    waste_id = response.json()["id"]
    # Delete waste
    response = client.delete(
        url=f"api/v1/wastes/{waste_id}/", headers=admin_auth_header)
    data = response.json()
    assert response.status_code == 200
    assert data["ok"] is True
    # Delete it again
    response = client.delete(
        url=f"api/v1/wastes/{waste_id}/", headers=admin_auth_header)
    assert response.status_code == 404
