import os
import string
from random import randint

from sqlmodel import Session, Field, Relationship, SQLModel, create_engine


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
    road_2 = Road(location_from=location_to, location_to=location_from,
                  distance=distance
                  )
    create_db_object(session=session, db_object=road_1)
    create_db_object(session=session, db_object=road_2)


def main():
    os.remove("fake_locations_database.db")
    sqlite_file_name = "fake_locations_database.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"

    connect_args = {"check_same_thread": False}
    engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)

    SQLModel.metadata.create_all(engine)

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

    with Session(engine) as session:
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


if __name__ == "__main__":
    main()
