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


def test_distance_to_storage(fake_db_session, client, admin_auth_header):
    generate_fake_db(session=fake_db_session)
    generate_companies_and_storages(
        client=client, admin_auth_header=admin_auth_header)
    # Look for test data in routes_test_data.py

    # Check distances to storages for company C1
    response = client.get(
        url="api/v1/companies/1/storages/1", headers=admin_auth_header)
    assert response.json()["distance"] == 350
    response = client.get(
        url="api/v1/companies/1/storages/2", headers=admin_auth_header)
    assert response.json()["distance"] == 50
    response = client.get(
        url="api/v1/companies/1/storages/3", headers=admin_auth_header)
    assert response.json()["distance"] == 200
    response = client.get(
        url="api/v1/companies/1/storages/4", headers=admin_auth_header)
    assert response.json()["distance"] == 450
    response = client.get(
        url="api/v1/companies/1/storages/5", headers=admin_auth_header)
    assert response.json()["distance"] == 300
    response = client.get(
        url="api/v1/companies/1/storages/6", headers=admin_auth_header)
    assert response.json()["distance"] == 600
    response = client.get(
        url="api/v1/companies/1/storages/7", headers=admin_auth_header)
    assert response.json()["distance"] == 500
    response = client.get(
        url="api/v1/companies/1/storages/8", headers=admin_auth_header)
    assert response.json()["distance"] == 400
    response = client.get(
        url="api/v1/companies/1/storages/9", headers=admin_auth_header)
    assert response.json()["distance"] == 550
    response = client.get(
        url="api/v1/companies/1/storages/10", headers=admin_auth_header)
    assert response.status_code == 404
    response = client.get(
        url="api/v1/companies/1/storages/11", headers=admin_auth_header)
    assert response.status_code == 404

# Check distances to storages for company C2
    response = client.get(
        url="api/v1/companies/2/storages/1", headers=admin_auth_header)
    assert response.json()["distance"] == 50
    response = client.get(
        url="api/v1/companies/2/storages/2", headers=admin_auth_header)
    assert response.json()["distance"] == 350
    response = client.get(
        url="api/v1/companies/2/storages/3", headers=admin_auth_header)
    assert response.json()["distance"] == 500
    response = client.get(
        url="api/v1/companies/2/storages/4", headers=admin_auth_header)
    assert response.json()["distance"] == 200
    response = client.get(
        url="api/v1/companies/2/storages/5", headers=admin_auth_header)
    assert response.json()["distance"] == 350
    response = client.get(
        url="api/v1/companies/2/storages/6", headers=admin_auth_header)
    assert response.json()["distance"] == 600
    response = client.get(
        url="api/v1/companies/2/storages/7", headers=admin_auth_header)
    assert response.json()["distance"] == 300
    response = client.get(
        url="api/v1/companies/2/storages/8", headers=admin_auth_header)
    assert response.json()["distance"] == 400
    response = client.get(
        url="api/v1/companies/2/storages/9", headers=admin_auth_header)
    assert response.json()["distance"] == 550
    response = client.get(
        url="api/v1/companies/2/storages/10", headers=admin_auth_header)
    assert response.status_code == 404
    response = client.get(
        url="api/v1/companies/2/storages/11", headers=admin_auth_header)
    assert response.status_code == 404

    # Check distances to storages for company C3
    response = client.get(
        url="api/v1/companies/3/storages/10", headers=admin_auth_header)
    assert response.json()["distance"] == 50
    response = client.get(
        url="api/v1/companies/3/storages/3", headers=admin_auth_header)
    assert response.json()["distance"] == 100
    response = client.get(
        url="api/v1/companies/3/storages/11", headers=admin_auth_header)
    assert response.status_code == 404

    # Check distances to storages for company C4
    response = client.get(
        url="api/v1/companies/4/storages/9", headers=admin_auth_header)
    assert response.status_code == 404
    response = client.get(
        url="api/v1/companies/4/storages/11", headers=admin_auth_header)
    assert response.status_code == 404


def test_optimal_unload_route(fake_db_session, client, admin_auth_header):
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
        json={"waste_id": 1, "max_amount": 10},
        headers=admin_auth_header
        )
    # Assign waste type 2 to storage S7
    client.post(
        url="api/v1/storages/7/waste-types/assign/",
        json={"waste_id": 2, "max_amount": 10},
        headers=admin_auth_header
        )
    # Assign waste types 1, 2 to storage S6
    client.post(
        url="api/v1/storages/6/waste-types/assign/",
        json={"waste_id": 1, "max_amount": 10},
        headers=admin_auth_header
        )
    client.post(
        url="api/v1/storages/6/waste-types/assign/",
        json={"waste_id": 2, "max_amount": 10},
        headers=admin_auth_header
        )

    # Update company waste amount
    client.patch(
        url="api/v1/companies/1/waste-types/1/",
        json={"amount": 10},
        headers=admin_auth_header
        )
    # Find path for one type and all types
    response = client.get(
        url="api/v1/companies/1/waste-types/1/optimal-route/",
        headers=admin_auth_header
        )
    assert response.status_code == 200
    assert response.json()["distance"] == 450  # S4
    response = client.get(
        url="api/v1/companies/1/waste-types/optimal-route/",
        headers=admin_auth_header
        )
    assert response.status_code == 200
    assert response.json()["distance"] == 450  # S4

    # Update company waste amount
    client.patch(
        url="api/v1/companies/1/waste-types/2/",
        json={"amount": 10},
        headers=admin_auth_header
        )
    # Find path for one type and all types
    response = client.get(
        url="api/v1/companies/1/waste-types/1/optimal-route/",
        headers=admin_auth_header
        )
    assert response.status_code == 200
    assert response.json()["distance"] == 450  # S4
    response = client.get(
        url="api/v1/companies/1/waste-types/2/optimal-route/",
        headers=admin_auth_header
        )
    assert response.status_code == 200
    assert response.json()["distance"] == 500  # S7
    response = client.get(
        url="api/v1/companies/1/waste-types/optimal-route/",
        headers=admin_auth_header
        )
    assert response.status_code == 200
    assert response.json()["distance"] == 600  # S6

    # Test partial unload paths
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
    # Find path for one type (partial unload)
    response = client.get(
        url="api/v1/companies/1/waste-types/1/optimal-route/",
        headers=admin_auth_header
        )
    assert response.status_code == 200
    assert response.json()["distance"] == 400  # S8
    assert response.json()["route_history"][0]["name"] == "S2"
    assert response.json()["route_history"][1]["name"] == "S5"
    assert response.json()["route_history"][2]["name"] == "S8"
