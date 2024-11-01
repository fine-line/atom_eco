import string
from random import randint

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from ..main import app
from ..config import get_settings
from ..database import get_session, create_admin, get_fake_db_session
from .. import crud
from ..models.location import Location
from ..models.road import Road


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


def create_one_way_road(
        session: Session, location_from: Location, location_to: Location):
    road = Road(location_from=location_from, location_to=location_to,
                distance=randint(1, 300)
                )
    crud.create_db_object(session=session, db_object=road)


def create_two_way_road(
        session: Session, location_from: Location, location_to: Location):
    distance = randint(1, 300)
    road_1 = Road(location_from=location_from, location_to=location_to,
                  distance=distance
                  )
    crud.create_db_object(session=session, db_object=road_1)
    road_2 = Road(location_from=location_to, location_to=location_from,
                  distance=distance
                  )
    crud.create_db_object(session=session, db_object=road_2)


def generate_fake_db(session: Session):

    """
    Location layout

    A1--B1--C1--D1--E1
    |   |   |   |   |
    A2--B2--C2--D2--E2
    |   |   |   |   |
    A3--B3--C3--D3--E3
    |   |   |   |   |
    A4--B4--C4--D4--E4
    |   |   |   |   |
    A5--B5--C5--D5--E5
    """

    locations = []
    for i in range(5):
        locations.append([])
        for j in range(5):
            location = Location(name=f"{string.ascii_uppercase[j]}{i+1}")
            crud.create_db_object(session=session, db_object=location)
            locations[i].append(location)
            if j > 0:
                create_two_way_road(session=session,
                                    location_from=locations[i][j-1],
                                    location_to=locations[i][j]
                                    )
            if i > 0:
                create_two_way_road(session=session,
                                    location_from=locations[i-1][j],
                                    location_to=locations[i][j]
                                    )


def test_assign_locations(session, fake_db_session, client, admin_auth_header):
    # Generate fake db locations
    generate_fake_db(session=fake_db_session)
    locations = crud.get_db_objects(
        session=fake_db_session, db_class=Location, skip=0, limit=100)
    assert len(locations) == 25
    roads = crud.get_db_objects(
        session=fake_db_session, db_class=Road, skip=0, limit=100)
    assert len(roads) == 80
    # Create storages and companies
    for i in range(1, 5 + 1):
        name = f"storage{i}"
        email = f"storage{i}@example.com"
        password = f"storage{i}"
        client.post(
            url="api/v1/storages/create/",
            json={"name": name, "email": email, "password": password},
            headers=admin_auth_header
            )
    for i in range(1, 5 + 1):
        name = f"company{i}"
        email = f"company{i}@example.com"
        password = f"company{i}"
        client.post(
            url="api/v1/companies/create/",
            json={"name": name, "email": email, "password": password},
            headers=admin_auth_header
            )
    # Assign location to company
    response = client.post(
        url="api/v1/companies/1/location/assign",
        json={"name": "A1"},
        headers=admin_auth_header
        )
    assert response.status_code == 200
    """
    Location layout
    A1
    """
    data = response.json()
    assert data["id"] == 1
    assert data["location_link"]["location_id"] == 1
    # Assign location to storage
    response = client.post(
        url="api/v1/storages/1/location/assign",
        json={"name": "B1"},
        headers=admin_auth_header
        )
    assert response.status_code == 200
    """
    Location layout
    A1--B1
    """
    # Assign location to storage
    response = client.post(
        url="api/v1/storages/2/location/assign",
        json={"name": "A2"},
        headers=admin_auth_header
        )
    assert response.status_code == 200
    """
    Location layout
    A1--B1
    |
    A2
    """
    data = response.json()
    assert data["id"] == 2
    assert data["location_link"]["location_id"] == 3
    # Assign location to storage
    response = client.post(
        url="api/v1/storages/3/location/assign",
        json={"name": "C2"},
        headers=admin_auth_header
        )
    assert response.status_code == 200
    """
    Location layout
    A1--B1
    |
    A2      C2
    """
    # Check locations and roads
    response = client.get(url="api/v1/locations", headers=admin_auth_header)
    assert response.status_code == 200
    assert len(response.json()) == 4
    response = client.get(url="api/v1/locations/1", headers=admin_auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "A1"
    assert len(data["roads_from"]) == 2
    assert len(data["roads_to"]) == 2
    response = client.get(url="api/v1/locations/4", headers=admin_auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "C2"
    assert len(data["roads_from"]) == 0
    assert len(data["roads_to"]) == 0
    # Assign location to storage
    response = client.post(
        url="api/v1/storages/4/location/assign",
        json={"name": "B2"},
        headers=admin_auth_header
        )
    assert response.status_code == 200
    """
    Location layout
    A1--B1
    |   |
    A2--B2--C2
    """
    # Check locations and roads
    response = client.get(url="api/v1/locations", headers=admin_auth_header)
    assert response.status_code == 200
    assert len(response.json()) == 5
    response = client.get(url="api/v1/locations/5", headers=admin_auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "B2"
    assert len(data["roads_from"]) == 3
    assert len(data["roads_to"]) == 3
    response = client.get(url="api/v1/locations/4", headers=admin_auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "C2"
    assert len(data["roads_from"]) == 1
    assert len(data["roads_to"]) == 1
    # Delete location
    response = client.delete(
        url="api/v1/locations/1",
        headers=admin_auth_header
        )
    assert response.status_code == 200
    """
    Location layout
        B1
        |
    A2--B2--C2
    """
    # Check locations and roads
    response = client.get(url="api/v1/locations", headers=admin_auth_header)
    assert response.status_code == 200
    assert len(response.json()) == 4
    response = client.get(url="api/v1/locations/3", headers=admin_auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "A2"
    assert len(data["roads_from"]) == 1
    assert len(data["roads_to"]) == 1
    # Reassign location
    response = client.post(
        url="api/v1/storages/2/location/assign",
        json={"name": "C3"},
        headers=admin_auth_header
        )
    assert response.status_code == 200
    """
    Location layout
        B1
        |
        B2--C2--C3
    """
    data = response.json()
    assert data["id"] == 2
    assert data["location_link"]["location_id"] == 6
    # Check locations and roads
    response = client.get(url="api/v1/locations", headers=admin_auth_header)
    assert response.status_code == 200
    assert len(response.json()) == 4
    response = client.get(url="api/v1/locations/5", headers=admin_auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "B2"
    assert len(data["roads_from"]) == 2
    assert len(data["roads_to"]) == 2
    response = client.get(url="api/v1/locations/4", headers=admin_auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "C2"
    assert len(data["roads_from"]) == 2
    assert len(data["roads_to"]) == 2
    # Try to assign to occupied location
    response = client.post(
        url="api/v1/companies/1/location/assign",
        json={"name": "C3"},
        headers=admin_auth_header
        )
    assert response.status_code == 400
    response = client.post(
        url="api/v1/storages/1/location/assign",
        json={"name": "C3"},
        headers=admin_auth_header
        )
    assert response.status_code == 400
