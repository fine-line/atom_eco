from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .location import Location, LocationPublic


class RoadBase(SQLModel):
    distance: int


class Road(RoadBase, table=True):
    location_from_id: int | None = Field(
        default=None, foreign_key="location.id", primary_key=True)
    location_to_id: int | None = Field(
        default=None, foreign_key="location.id", primary_key=True)

    location_from: "Location" = Relationship(
        back_populates="roads_from",
        sa_relationship_kwargs={"foreign_keys": "Road.location_from_id"})
    location_to: "Location" = Relationship(
        back_populates="roads_to",
        sa_relationship_kwargs={"foreign_keys": "Road.location_to_id"})


class RoadFromPublic(RoadBase):
    location_to: "LocationPublic"


class RoadToPublic(RoadBase):
    location_from: "LocationPublic"


class RoadUpdate(SQLModel):
    pass
