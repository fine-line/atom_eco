import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from ..main import app
from ..config import get_settings
from ..database import get_session, create_admin
from .. import crud
from ..models.storagewastelink import StorageWasteLink


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


def test_create_storage(client, admin_auth_header):
    name = "storage"
    email = "storage@example.com"
    password = "storage"
    response = client.post(
        url="api/v1/storages/create/",
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
        url="api/v1/storages/create/",
        json={"name": "storage2", "email": email, "password": "storage2"},
        headers=admin_auth_header
        )
    assert response.status_code == 400


def test_get_storage(client, admin_auth_header):
    # Create storage
    name = "storage"
    email = "storage@example.com"
    password = "storage"
    response = client.post(
        url="api/v1/storages/create/",
        json={"name": name, "email": email, "password": password},
        headers=admin_auth_header
        )
    storage_id = response.json()["id"]
    # Get storage
    response = client.get(
        url=f"api/v1/storages/{storage_id}/", headers=admin_auth_header)
    data = response.json()
    assert response.status_code == 200
    assert data["id"] == storage_id
    assert data["email"] == email
    # Get nonexisted storage
    response = client.get(
        url=f"api/v1/storages/{storage_id + 1}/", headers=admin_auth_header)
    assert response.status_code == 404


def test_get_storages(client, admin_auth_header):
    # Create storages
    for i in range(1, 5 + 1):
        name = f"storage{i}"
        email = f"storage{i}@example.com"
        password = f"storage{i}"
        client.post(
            url="api/v1/storages/create/",
            json={"name": name, "email": email, "password": password},
            headers=admin_auth_header
            )
    # Get storages
    response = client.get(
        url="api/v1/storages/", headers=admin_auth_header)
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 5


def test_delete_storage(client, admin_auth_header):
    # Create storage
    name = "storage"
    email = "storage@example.com"
    password = "storage"
    response = client.post(
        url="api/v1/storages/create/",
        json={"name": name, "email": email, "password": password},
        headers=admin_auth_header
        )
    storage_id = response.json()["id"]
    # Delete storage
    response = client.delete(
        url=f"api/v1/storages/{storage_id}/", headers=admin_auth_header)
    data = response.json()
    assert response.status_code == 200
    assert data["ok"] is True
    # Delete it again
    response = client.delete(
        url=f"api/v1/storages/{storage_id}/", headers=admin_auth_header)
    assert response.status_code == 404


def test_update_storage(client, admin_auth_header):
    # Create storages
    for i in range(1, 5 + 1):
        name = f"storage{i}"
        email = f"storage{i}@example.com"
        password = f"storage{i}"
        client.post(
            url="api/v1/storages/create/",
            json={"name": name, "email": email, "password": password},
            headers=admin_auth_header
            )
    # Update storage
    response = client.patch(
        url="api/v1/storages/1/",
        json={"email": "new_storage@example.com"},
        headers=admin_auth_header
        )
    data = response.json()
    assert response.status_code == 200
    assert data["email"] == "new_storage@example.com"
    # Try existing email
    response = client.patch(
        url="api/v1/storages/2/",
        json={"email": "new_storage@example.com"},
        headers=admin_auth_header
        )
    data = response.json()
    assert response.status_code == 400


def test_assign_waste_to_storage(client, admin_auth_header):
    # Create waste
    response = client.post(
        "api/v1/wastes/create/", headers=admin_auth_header,
        json={"name": "Bio"}
        )
    waste_id = response.json()["id"]
    # Create storage
    name = "storage"
    email = "storage@example.com"
    password = "storage"
    response = client.post(
        url="api/v1/storages/create/",
        json={"name": name, "email": email, "password": password},
        headers=admin_auth_header
        )
    storage_id = response.json()["id"]
    # Assign waste to storage
    response = client.post(
        url=f"api/v1/storages/{storage_id}/waste-types/assign/",
        json={"waste_id": waste_id, "max_amount": 100},
        headers=admin_auth_header
        )
    data = response.json()
    assert response.status_code == 200
    assert data["waste_links"][0]["waste_id"] == waste_id
    assert data["waste_links"][0]["amount"] == 0
    assert data["waste_links"][0]["max_amount"] == 100


def test_update_storage_waste_link(session, client, admin_auth_header):
    # Create waste
    response = client.post(
        "api/v1/wastes/create/", headers=admin_auth_header,
        json={"name": "Bio"}
        )
    waste_id = response.json()["id"]
    # Create storage
    name = "storage"
    email = "storage@example.com"
    password = "storage"
    response = client.post(
        url="api/v1/storages/create/",
        json={"name": name, "email": email, "password": password},
        headers=admin_auth_header
        )
    storage_id = response.json()["id"]
    # Assign waste to storage
    response = client.post(
        url=f"api/v1/storages/{storage_id}/waste-types/assign/",
        json={"waste_id": waste_id, "max_amount": 100},
        headers=admin_auth_header
        )
    # Try to increase waste amount without recieving from company
    response = client.patch(
        url=f"api/v1/storages/{storage_id}/waste-types/{waste_id}/",
        json={"amount": 50},
        headers=admin_auth_header
        )
    assert response.status_code == 400
    # Try to make max_amount lower than amount
    storage_waste_link = crud.get_db_link(
        session=session, db_table=StorageWasteLink,
        id_field_1="storage_id", value_1=storage_id,
        id_field_2="waste_id", value_2=waste_id
        )
    crud.update_db_object(
        session=session, db_object=storage_waste_link,
        update_data={"amount": 50}
        )
    response = client.patch(
        url=f"api/v1/storages/{storage_id}/waste-types/{waste_id}/",
        json={"max_amount": 49},
        headers=admin_auth_header
        )
    assert response.status_code == 400
