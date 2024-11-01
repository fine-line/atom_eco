import string

from sqlmodel import Session

from .. import crud
from ..models.location import Location
from ..models.road import Road


"""
Location layout

   [A1]--50--[B1]-100--[C1]--50--[D1]--50--[E1]
    |         |         |         |         ↓
    50        50        50        50        50
    |         |         |         |         ↓
   [A2]--50--[B2]-300--[C2]-150--[D2]←←50←←[E2]
    |         |         |         |         |
    50       150       250       500        50
    |         |         |         |         |
   [A3]--50--[B3]-150--[C3]-350--[D3]--50--[E3]
    |         |         |         |         |
    50       100       100        50        50
    |         |         |         |         |
   [A4]--50--[B4]-100--[C4]-150--[D4]--50--[E4]
    |         |         |         |         |
    50        50        50        50        50
    |         |         |         |         |
   [A5]--50--[B5]--50--[C5]--50--[D5]--50--[E5]


Company | Storage layout

            [C2]-100--[C1]                [C3]
             |         |                   ↓
             50        50                  50
             |         |                   ↓
            [S1]-300--[S2]-150--[S3]←-50←-[S10]
             |         |         |
             150       250       500
             |         |         |
            [S4]-150--[S5]-350--[S6]
             |         |         |
             100       100       50
             |         |         |
            [S7]-100--[S8]-150--[S9]



[S11]                                   [C4]


Company | Storage shortest paths (cumulative)
    For C1

                      [C1]
                       ↓
                       50
                       ↓
            [S1]←350←-[S2]→200-→[S3]
                       ↓
                      300
                       ↓
            [S4]←450←-[S5]      [S6]
                       ↓         ↑
                      400       600
                       ↓         ↑
            [S7]←500←-[S8]→550-→[S9]


Company | Storage shortest paths (cumulative)
    For C2

            [C2]
             ↓
             50
             ↓
            [S1]→350-→[S2]→500-→[S3]
             ↓
            200
             ↓
            [S4]→350-→[S5]      [S6]
             ↓                   ↑
            300                 600
             ↓                   ↑
            [S7]→400-→[S8]→550-→[S9]


"""


def create_one_way_road(
        session: Session, from_: str, to: str, distance: int):
    location_from = crud.get_db_object_by_field(
        session=session, db_table=Location, field="name", value=from_)
    location_to = crud.get_db_object_by_field(
        session=session, db_table=Location, field="name", value=to)
    road = Road(
        location_from=location_from, location_to=location_to,
        distance=distance
        )
    crud.create_db_object(session=session, db_object=road)


def create_two_way_road(
        session: Session, from_: str, to: str, distance: int):
    location_from = crud.get_db_object_by_field(
        session=session, db_table=Location, field="name", value=from_)
    location_to = crud.get_db_object_by_field(
        session=session, db_table=Location, field="name", value=to)
    road_1 = Road(
        location_from=location_from, location_to=location_to,
        distance=distance
        )
    crud.create_db_object(session=session, db_object=road_1)
    road_2 = Road(
        location_from=location_to, location_to=location_from,
        distance=distance
        )
    crud.create_db_object(session=session, db_object=road_2)


def generate_fake_db(session: Session):
    # Generating locations
    for i in range(5):
        for j in range(5):
            location = Location(name=f"{string.ascii_uppercase[j]}{i+1}")
            crud.create_db_object(session=session, db_object=location)
    # Generating roads
    create_two_way_road(session=session, from_="A1", to="B1", distance=50)
    create_two_way_road(session=session, from_="B1", to="C1", distance=50)
    create_two_way_road(session=session, from_="C1", to="D1", distance=50)
    create_two_way_road(session=session, from_="D1", to="E1", distance=50)

    create_two_way_road(session=session, from_="A2", to="B2", distance=50)
    create_two_way_road(session=session, from_="B2", to="C2", distance=300)
    create_two_way_road(session=session, from_="C2", to="D2", distance=150)
    create_one_way_road(session=session, from_="E2", to="D2", distance=50)  # !

    create_two_way_road(session=session, from_="A3", to="B3", distance=50)
    create_two_way_road(session=session, from_="B3", to="C3", distance=150)
    create_two_way_road(session=session, from_="C3", to="D3", distance=350)
    create_two_way_road(session=session, from_="D3", to="E3", distance=50)

    create_two_way_road(session=session, from_="A4", to="B4", distance=50)
    create_two_way_road(session=session, from_="B4", to="C4", distance=100)
    create_two_way_road(session=session, from_="C4", to="D4", distance=150)
    create_two_way_road(session=session, from_="D4", to="E4", distance=50)

    create_two_way_road(session=session, from_="A5", to="B5", distance=50)
    create_two_way_road(session=session, from_="B5", to="C5", distance=50)
    create_two_way_road(session=session, from_="C5", to="D5", distance=50)
    create_two_way_road(session=session, from_="D5", to="E5", distance=50)

    create_two_way_road(session=session, from_="A1", to="A2", distance=50)
    create_two_way_road(session=session, from_="B1", to="B2", distance=50)
    create_two_way_road(session=session, from_="C1", to="C2", distance=50)
    create_two_way_road(session=session, from_="D1", to="D2", distance=50)
    create_one_way_road(session=session, from_="E1", to="E2", distance=50)  # !

    create_two_way_road(session=session, from_="A2", to="A3", distance=50)
    create_two_way_road(session=session, from_="B2", to="B3", distance=150)
    create_two_way_road(session=session, from_="C2", to="C3", distance=250)
    create_two_way_road(session=session, from_="D2", to="D3", distance=500)
    create_two_way_road(session=session, from_="E2", to="E3", distance=50)

    create_two_way_road(session=session, from_="A3", to="A4", distance=50)
    create_two_way_road(session=session, from_="B3", to="B4", distance=100)
    create_two_way_road(session=session, from_="C3", to="C4", distance=100)
    create_two_way_road(session=session, from_="D3", to="D4", distance=50)
    create_two_way_road(session=session, from_="E3", to="E4", distance=50)

    create_two_way_road(session=session, from_="A4", to="A5", distance=50)
    create_two_way_road(session=session, from_="B4", to="B5", distance=50)
    create_two_way_road(session=session, from_="C4", to="C5", distance=50)
    create_two_way_road(session=session, from_="D4", to="D5", distance=50)
    create_two_way_road(session=session, from_="E4", to="E5", distance=50)


def generate_companies_and_storages(client, admin_auth_header):
    # Generating storages and companies
    for i in range(1, 11 + 1):
        name = f"S{i}"
        email = f"S{i}@example.com"
        password = f"S{i}"
        client.post(
            url="api/v1/storages/create/",
            json={"name": name, "email": email, "password": password},
            headers=admin_auth_header
            )
    for i in range(1, 4 + 1):
        name = f"C{i}"
        email = f"C{i}@example.com"
        password = f"C{i}"
        client.post(
            url="api/v1/companies/create/",
            json={"name": name, "email": email, "password": password},
            headers=admin_auth_header
            )

    # Assign locations
    client.post(
        url="api/v1/companies/1/location/assign", json={"name": "C1"},
        headers=admin_auth_header
        )
    client.post(
        url="api/v1/companies/2/location/assign", json={"name": "B1"},
        headers=admin_auth_header
        )
    client.post(
        url="api/v1/companies/3/location/assign", json={"name": "E1"},
        headers=admin_auth_header
        )
    client.post(
        url="api/v1/companies/4/location/assign", json={"name": "E5"},
        headers=admin_auth_header
        )

    client.post(
        url="api/v1/storages/1/location/assign", json={"name": "B2"},
        headers=admin_auth_header
        )
    client.post(
        url="api/v1/storages/2/location/assign", json={"name": "C2"},
        headers=admin_auth_header
        )
    client.post(
        url="api/v1/storages/3/location/assign", json={"name": "D2"},
        headers=admin_auth_header
        )
    client.post(
        url="api/v1/storages/4/location/assign", json={"name": "B3"},
        headers=admin_auth_header
        )
    client.post(
        url="api/v1/storages/5/location/assign", json={"name": "C3"},
        headers=admin_auth_header
        )
    client.post(
        url="api/v1/storages/6/location/assign", json={"name": "D3"},
        headers=admin_auth_header
        )
    client.post(
        url="api/v1/storages/7/location/assign", json={"name": "B4"},
        headers=admin_auth_header
        )
    client.post(
        url="api/v1/storages/8/location/assign", json={"name": "C4"},
        headers=admin_auth_header
        )
    client.post(
        url="api/v1/storages/9/location/assign", json={"name": "D4"},
        headers=admin_auth_header
        )
    client.post(
        url="api/v1/storages/10/location/assign", json={"name": "E2"},
        headers=admin_auth_header
        )
    client.post(
        url="api/v1/storages/11/location/assign", json={"name": "A5"},
        headers=admin_auth_header
        )
