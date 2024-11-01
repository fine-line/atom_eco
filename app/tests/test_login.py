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


def test_login_for_access_token(client):
    settings = get_settings()
    credentials = {"username": settings.admin_email,
                   "password": settings.admin_password}
    response = client.post(url="api/v1/login/token", data=credentials)
    assert response.status_code == 200
    access_token = response.json()["access_token"]
    assert access_token is not None


def test_authorization_valid(client, admin_auth_header):
    response = client.get(url="api/v1/companies/", headers=admin_auth_header)
    assert response.status_code == 200


def test_authorization_invalid(client, admin_auth_header):
    # Create data
    name = "company"
    email = "company@example.com"
    password = "company"
    response = client.post(
        url="api/v1/companies/create/",
        json={"name": name, "email": email, "password": password},
        headers=admin_auth_header
        )
    # Get token
    credentials = {"username": email,
                   "password": password}
    response = client.post(url="api/v1/login/token", data=credentials)
    access_token = response.json()["access_token"]
    # Access restricted resource
    response = client.get(
        url="api/v1/companies/",
        headers={"Authorization": f"Bearer {access_token}"}
        )
    assert response.status_code == 403


def test_get_self_id(client, admin_auth_header):
    # Create data
    name = "company"
    email = "company@example.com"
    password = "company"
    response = client.post(
        url="api/v1/companies/create/",
        json={"name": name, "email": email, "password": password},
        headers=admin_auth_header
        )
    company_id = response.json()["id"]
    # Get token
    credentials = {"username": email,
                   "password": password}
    response = client.post(url="api/v1/login/token", data=credentials)
    access_token = response.json()["access_token"]
    # Get self id
    response = client.get(
        url="api/v1/login/self-id/",
        headers={"Authorization": f"Bearer {access_token}"}
        )
    assert response.status_code == 200
    assert response.json() == company_id
