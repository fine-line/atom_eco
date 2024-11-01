import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from ..main import app
from ..config import get_settings
from ..database import get_session, create_admin, get_fake_db_session
from ..models.location import Location
from ..models.road import Road
from .routes_test_data import generate_fake_db, generate_companies_and_storages


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


@pytest.fixture(name="fake_db_session")
def fake_db_session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False},
        poolclass=StaticPool
        )
    Location.__table__.create(engine)
    Road.__table__.create(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session, fake_db_session: Session):
    def get_session_override():
        return session

    def get_fake_db_session_override():
        return fake_db_session

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_fake_db_session] \
        = get_fake_db_session_override

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


def test_create_company(client, admin_auth_header):
    name = "company"
    email = "company@example.com"
    password = "company"
    response = client.post(
        url="api/v1/companies/create/",
        json={"name": name, "email": email, "password": password},
        headers=admin_auth_header
        )
    data = response.json()
    assert response.status_code == 200
    assert data["name"] == name
    assert data["id"] is not None
    assert data["email"] == email
    # Try again with the same email
    response = client.post(
        url="api/v1/companies/create/",
        json={"name": "company2", "email": email, "password": "company2"},
        headers=admin_auth_header
        )
    assert response.status_code == 400


def test_get_company(client, admin_auth_header):
    # Create company
    name = "company"
    email = "company@example.com"
    password = "company"
    response = client.post(
        url="api/v1/companies/create/",
        json={"name": name, "email": email, "password": password},
        headers=admin_auth_header
        )
    company_id = response.json()["id"]
    # Get company
    response = client.get(
        url=f"api/v1/companies/{company_id}/", headers=admin_auth_header)
    data = response.json()
    assert response.status_code == 200
    assert data["id"] == company_id
    assert data["email"] == email
    # Get nonexisted company
    response = client.get(
        url=f"api/v1/companies/{company_id + 1}/", headers=admin_auth_header)
    assert response.status_code == 404


def test_get_companies(client, admin_auth_header):
    # Create companies
    for i in range(1, 5 + 1):
        name = f"company{i}"
        email = f"company{i}@example.com"
        password = f"company{i}"
        client.post(
            url="api/v1/companies/create/",
            json={"name": name, "email": email, "password": password},
            headers=admin_auth_header
            )
    # Get companies
    response = client.get(
        url="api/v1/companies/", headers=admin_auth_header)
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 5


def test_delete_company(client, admin_auth_header):
    # Create company
    name = "company"
    email = "company@example.com"
    password = "company"
    response = client.post(
        url="api/v1/companies/create/",
        json={"name": name, "email": email, "password": password},
        headers=admin_auth_header
        )
    company_id = response.json()["id"]
    # Delete company
    response = client.delete(
        url=f"api/v1/companies/{company_id}/", headers=admin_auth_header)
    data = response.json()
    assert response.status_code == 200
    assert data["ok"] is True
    # Delete it again
    response = client.delete(
        url=f"api/v1/companies/{company_id}/", headers=admin_auth_header)
    assert response.status_code == 404


def test_update_company(client, admin_auth_header):
    # Create companies
    for i in range(1, 5 + 1):
        name = f"company{i}"
        email = f"company{i}@example.com"
        password = f"company{i}"
        client.post(
            url="api/v1/companies/create/",
            json={"name": name, "email": email, "password": password},
            headers=admin_auth_header
            )
    # Update company
    response = client.patch(
        url="api/v1/companies/1/",
        json={"email": "new_company@example.com"},
        headers=admin_auth_header
        )
    data = response.json()
    assert response.status_code == 200
    assert data["email"] == "new_company@example.com"
    # Try existing email
    response = client.patch(
        url="api/v1/companies/2/",
        json={"email": "new_company@example.com"},
        headers=admin_auth_header
        )
    data = response.json()
    assert response.status_code == 400


def test_assign_waste_to_company(client, admin_auth_header):
    # Create waste
    response = client.post(
        "api/v1/wastes/create/", headers=admin_auth_header,
        json={"name": "Bio"}
        )
    waste_id = response.json()["id"]
    # Create company
    name = "company"
    email = "company@example.com"
    password = "company"
    response = client.post(
        url="api/v1/companies/create/",
        json={"name": name, "email": email, "password": password},
        headers=admin_auth_header
        )
    company_id = response.json()["id"]
    # Assign waste to company
    response = client.post(
        url=f"api/v1/companies/{company_id}/waste-types/assign/",
        json={"waste_id": waste_id, "max_amount": 100},
        headers=admin_auth_header
        )
    data = response.json()
    assert response.status_code == 200
    assert data["waste_links"][0]["waste_id"] == waste_id
    assert data["waste_links"][0]["amount"] == 0
    assert data["waste_links"][0]["max_amount"] == 100


def test_update_company_waste_link(client, admin_auth_header):
    # Create waste
    response = client.post(
        "api/v1/wastes/create/", headers=admin_auth_header,
        json={"name": "Bio"}
        )
    waste_id = response.json()["id"]
    # Create company
    name = "company"
    email = "company@example.com"
    password = "company"
    response = client.post(
        url="api/v1/companies/create/",
        json={"name": name, "email": email, "password": password},
        headers=admin_auth_header
        )
    company_id = response.json()["id"]
    # Assign waste to company
    response = client.post(
        url=f"api/v1/companies/{company_id}/waste-types/assign/",
        json={"waste_id": waste_id, "max_amount": 100},
        headers=admin_auth_header
        )
    # Try to decrease waste amount without unloading
    response = client.patch(
        url=f"api/v1/companies/{company_id}/waste-types/{waste_id}/",
        json={"amount": 50},
        headers=admin_auth_header
        )
    assert response.status_code == 200
    response = client.patch(
        url=f"api/v1/companies/{company_id}/waste-types/{waste_id}/",
        json={"amount": 49},
        headers=admin_auth_header
        )
    assert response.status_code == 400
    # Try to make max_amount lower than amount
    response = client.patch(
        url=f"api/v1/companies/{company_id}/waste-types/{waste_id}/",
        json={"max_amount": 49},
        headers=admin_auth_header
        )
    assert response.status_code == 400


def test_unload(fake_db_session, client, admin_auth_header):
    generate_fake_db(session=fake_db_session)
    generate_companies_and_storages(
        client=client, admin_auth_header=admin_auth_header)
    # Look for test data in routes_test_data.py

    # Create waste types
    client.post(
        "api/v1/wastes/create/", headers=admin_auth_header,
        json={"name": "Bio"}
        )
    client.post(
        "api/v1/wastes/create/", headers=admin_auth_header,
        json={"name": "Glass"}
        )
    client.post(
        "api/v1/wastes/create/", headers=admin_auth_header,
        json={"name": "Plastic"}
        )

    # Assign waste types to company C1
    client.post(
        url="api/v1/companies/1/waste-types/assign/",
        json={"waste_id": 1, "max_amount": 100},
        headers=admin_auth_header
        )
    client.post(
        url="api/v1/companies/1/waste-types/assign/",
        json={"waste_id": 2, "max_amount": 100},
        headers=admin_auth_header
        )
    client.post(
        url="api/v1/companies/1/waste-types/assign/",
        json={"waste_id": 3, "max_amount": 100},
        headers=admin_auth_header
        )

    # Assign waste type 1 to storage S4
    client.post(
        url="api/v1/storages/4/waste-types/assign/",
        json={"waste_id": 1, "max_amount": 20},
        headers=admin_auth_header
        )
    # Assign waste type 2 to storage S7
    client.post(
        url="api/v1/storages/7/waste-types/assign/",
        json={"waste_id": 2, "max_amount": 20},
        headers=admin_auth_header
        )
    # Assign waste types 1, 2 to storage S6
    client.post(
        url="api/v1/storages/6/waste-types/assign/",
        json={"waste_id": 1, "max_amount": 20},
        headers=admin_auth_header
        )
    client.post(
        url="api/v1/storages/6/waste-types/assign/",
        json={"waste_id": 2, "max_amount": 20},
        headers=admin_auth_header
        )
    # Assign waste type 1 to storage S2
    client.post(
        url="api/v1/storages/2/waste-types/assign/",
        json={"waste_id": 1, "max_amount": 4},
        headers=admin_auth_header
        )
    # Assign waste type 1 to storage S5
    client.post(
        url="api/v1/storages/5/waste-types/assign/",
        json={"waste_id": 1, "max_amount": 4},
        headers=admin_auth_header
        )
    # Assign waste type 1 to storage S8
    client.post(
        url="api/v1/storages/8/waste-types/assign/",
        json={"waste_id": 1, "max_amount": 4},
        headers=admin_auth_header
        )
    # Update company waste amounts
    client.patch(
        url="api/v1/companies/1/waste-types/1/",
        json={"amount": 10},
        headers=admin_auth_header
        )
    client.patch(
        url="api/v1/companies/1/waste-types/2/",
        json={"amount": 10},
        headers=admin_auth_header
        )

    # Unload waste type 1 (partial unload)
    response = client.post(
        url="api/v1/companies/1/waste-types/1/unload/",
        headers=admin_auth_header
        )
    assert response.status_code == 200

    response = client.get(
        url="api/v1/companies/1",
        headers=admin_auth_header
        )
    assert response.json()["waste_links"][0]["waste_id"] == 1
    assert response.json()["waste_links"][0]["amount"] == 0

    response = client.get(
        url="api/v1/storages/2",
        headers=admin_auth_header
        )
    assert response.json()["name"] == "S2"
    assert response.json()["waste_links"][0]["waste_id"] == 1
    assert response.json()["waste_links"][0]["amount"] == 4

    response = client.get(
        url="api/v1/storages/5",
        headers=admin_auth_header
        )
    assert response.json()["name"] == "S5"
    assert response.json()["waste_links"][0]["waste_id"] == 1
    assert response.json()["waste_links"][0]["amount"] == 4

    response = client.get(
        url="api/v1/storages/8",
        headers=admin_auth_header
        )
    assert response.json()["name"] == "S8"
    assert response.json()["waste_links"][0]["waste_id"] == 1
    assert response.json()["waste_links"][0]["amount"] == 2

    # Update company waste amount
    client.patch(
        url="api/v1/companies/1/waste-types/1/",
        json={"amount": 10},
        headers=admin_auth_header
        )
    # Unload waste type 1 (again)
    response = client.post(
        url="api/v1/companies/1/waste-types/1/unload/",
        headers=admin_auth_header
        )
    assert response.status_code == 200

    response = client.get(
        url="api/v1/companies/1",
        headers=admin_auth_header
        )
    assert response.json()["waste_links"][0]["waste_id"] == 1
    assert response.json()["waste_links"][0]["amount"] == 0

    response = client.get(
        url="api/v1/storages/4",
        headers=admin_auth_header
        )
    assert response.json()["name"] == "S4"
    assert response.json()["waste_links"][0]["waste_id"] == 1
    assert response.json()["waste_links"][0]["amount"] == 10

    # Update company waste amount
    client.patch(
        url="api/v1/companies/1/waste-types/1/",
        json={"amount": 2},
        headers=admin_auth_header
        )
    # Update storage waste amount
    client.patch(
        url="api/v1/storages/4/waste-types/1/",
        json={"amount": 0},
        headers=admin_auth_header
        )
    # Unload all waste types
    response = client.post(
        url="api/v1/companies/1/waste-types/unload/",
        headers=admin_auth_header
        )
    assert response.status_code == 200

    response = client.get(
        url="api/v1/companies/1",
        headers=admin_auth_header
        )
    assert response.json()["waste_links"][0]["waste_id"] == 1
    assert response.json()["waste_links"][0]["amount"] == 0
    assert response.json()["waste_links"][1]["waste_id"] == 2
    assert response.json()["waste_links"][1]["amount"] == 0

    response = client.get(
        url="api/v1/storages/6",
        headers=admin_auth_header
        )
    assert response.json()["name"] == "S6"
    assert response.json()["waste_links"][0]["waste_id"] == 1
    assert response.json()["waste_links"][0]["amount"] == 2
    assert response.json()["waste_links"][1]["waste_id"] == 2
    assert response.json()["waste_links"][1]["amount"] == 10

    response = client.get(
        url="api/v1/storages/4",
        headers=admin_auth_header
        )
    assert response.json()["name"] == "S4"
    assert response.json()["waste_links"][0]["waste_id"] == 1
    assert response.json()["waste_links"][0]["amount"] == 0

    response = client.get(
        url="api/v1/storages/7",
        headers=admin_auth_header
        )
    assert response.json()["name"] == "S7"
    assert response.json()["waste_links"][0]["waste_id"] == 2
    assert response.json()["waste_links"][0]["amount"] == 0

    response = client.get(
        url="api/v1/storages/8",
        headers=admin_auth_header
        )
    assert response.json()["name"] == "S8"
    assert response.json()["waste_links"][0]["waste_id"] == 1
    assert response.json()["waste_links"][0]["amount"] == 2
