from sqlmodel import Field, Relationship, SQLModel

from .road import Road, RoadFromPublic, RoadToPublic
from .companylocationlink import CompanyLocationLink
from .storagelocationlink import StorageLocationLink


class LocationBase(SQLModel):
    name: str = Field(index=True)


class Location(LocationBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    roads_from: list["Road"] = Relationship(
        back_populates="location_from",
        cascade_delete=True,
        sa_relationship_kwargs={"foreign_keys": "Road.location_from_id"})
    roads_to: list["Road"] = Relationship(
        back_populates="location_to",
        cascade_delete=True,
        sa_relationship_kwargs={"foreign_keys": "Road.location_to_id"})
    company_link: "CompanyLocationLink" = Relationship(
        back_populates="location",
        cascade_delete=True)
    storage_link: "StorageLocationLink" = Relationship(
        back_populates="location",
        cascade_delete=True)

    def __hash__(self):
        return hash(self.id)


class LocationCreate(LocationBase):
    pass


class LocationPublic(LocationBase):
    id: int


class LocationPublicWithRoad(LocationBase):
    id: int
    roads_from: list["RoadFromPublic"]
    roads_to: list["RoadToPublic"]


class LocationUpdate(LocationBase):
    name: str | None = None
