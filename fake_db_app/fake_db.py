# import os
import os
import string
from random import randint

from sqlmodel import (
    Session, Field, Relationship, SQLModel, create_engine, select)


class Location(SQLModel, table=True):
    # DB columns
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    # Relationships
    roads_from: list["Road"] = Relationship(
        back_populates="location_from",
        cascade_delete=True,
        sa_relationship_kwargs={"foreign_keys": "Road.location_from_id"})
    roads_to: list["Road"] = Relationship(
        back_populates="location_to",
        cascade_delete=True,
        sa_relationship_kwargs={"foreign_keys": "Road.location_to_id"})


class Road(SQLModel, table=True):
    # DB columns
    location_from_id: int | None = Field(
        default=None, foreign_key="location.id", primary_key=True)
    location_to_id: int | None = Field(
        default=None, foreign_key="location.id", primary_key=True)
    distance: int
    # Relationships
    location_from: Location = Relationship(
        back_populates="roads_from",
        sa_relationship_kwargs={"foreign_keys": "Road.location_from_id"})
    location_to: Location = Relationship(
        back_populates="roads_to",
        sa_relationship_kwargs={"foreign_keys": "Road.location_to_id"})


def create_db_object(session: Session, db_object: SQLModel):
    session.add(db_object)
    session.commit()
    session.refresh(db_object)
    return db_object


def get_db_object_by_field(
        session: Session, db_table: type[SQLModel], field: str, value):
    db_object = session.exec(
        select(db_table).where(getattr(db_table, field) == value)).first()
    return db_object


def generate_random_fake_db(session: Session):

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

    def create_one_way_road(
            session: Session, location_from: Location, location_to: Location):
        road = Road(location_from=location_from, location_to=location_to,
                    distance=randint(1, 300)
                    )
        create_db_object(session=session, db_object=road)

    def create_two_way_road(
            session: Session, location_from: Location, location_to: Location):
        distance = randint(1, 300)
        road_1 = Road(location_from=location_from, location_to=location_to,
                      distance=distance
                      )
        create_db_object(session=session, db_object=road_1)
        road_2 = Road(location_from=location_to, location_to=location_from,
                      distance=distance
                      )
        create_db_object(session=session, db_object=road_2)

    locations = []
    for i in range(5):
        locations.append([])
        for j in range(5):
            location = Location(name=f"{string.ascii_uppercase[j]}{i+1}")
            create_db_object(session=session, db_object=location)
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


def generate_fake_db(session: Session):
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

    """

    def create_one_way_road(
            session: Session, from_: str, to: str, distance: int):
        location_from = get_db_object_by_field(
            session=session, db_table=Location, field="name", value=from_)
        location_to = get_db_object_by_field(
            session=session, db_table=Location, field="name", value=to)
        road = Road(
            location_from=location_from, location_to=location_to,
            distance=distance
            )
        create_db_object(session=session, db_object=road)

    def create_two_way_road(
            session: Session, from_: str, to: str, distance: int):
        location_from = get_db_object_by_field(
            session=session, db_table=Location, field="name", value=from_)
        location_to = get_db_object_by_field(
            session=session, db_table=Location, field="name", value=to)
        road_1 = Road(
            location_from=location_from, location_to=location_to,
            distance=distance
            )
        create_db_object(session=session, db_object=road_1)
        road_2 = Road(
            location_from=location_to, location_to=location_from,
            distance=distance
            )
        create_db_object(session=session, db_object=road_2)

    # Generating locations
    for i in range(5):
        for j in range(5):
            location = Location(name=f"{string.ascii_uppercase[j]}{i+1}")
            create_db_object(session=session, db_object=location)
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


def main():
    db_user = os.environ["DB_USER"]
    db_password = os.environ["DB_PASSWORD"]
    db_service = os.environ["DB_SERVICE"]

    db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_service}:5432"
    engine = create_engine(db_url)

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        locations_in_db = session.exec(select(Location)).first()
        if not locations_in_db:
            generate_fake_db(session=session)


if __name__ == "__main__":
    main()
