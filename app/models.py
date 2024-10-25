from sqlmodel import Field, Relationship, SQLModel, AutoString
from pydantic import EmailStr
from typing import Optional

"""
#################### Company models ####################
"""


class CompanyBase(SQLModel):
    name: str = Field(index=True)


class Company(CompanyBase,  table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr = Field(sa_type=AutoString, unique=True, index=True)

    waste_links: list["CompanyWasteLink"] = Relationship(
        back_populates="company",
        cascade_delete=True)
    location_link: "CompanyLocationLink" = Relationship(
        back_populates="company",
        cascade_delete=True)


class CompanyCreate(CompanyBase):
    email: EmailStr


class CompanyPublic(CompanyBase):
    id: int


class CompanyPublicDetailed(CompanyPublic):
    id: int
    email: EmailStr
    waste_links: list["CompanyWasteLinkPublic"]
    location_link: Optional["CompanyLocationLinkPublic"]


class CompanyUpdate(SQLModel):
    name: str | None = None
    email: EmailStr | None = None


"""
#################### Storage models ####################
"""


class StorageBase(SQLModel):
    name: str = Field(index=True)


class Storage(StorageBase,  table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr = Field(sa_type=AutoString, unique=True, index=True)

    waste_links: list["StorageWasteLink"] = Relationship(
        back_populates="storage",
        cascade_delete=True)
    location_link: "StorageLocationLink" = Relationship(
        back_populates="storage",
        cascade_delete=True)


class StorageCreate(StorageBase):
    email: EmailStr


class StoragePublic(StorageBase):
    id: int


class StoragePublicDetailed(StoragePublic):
    id: int
    email: EmailStr
    waste_links: list["StorageWasteLinkPublic"]
    location_link: Optional["StorageLocationLinkPublic"]


class StorageUpdate(SQLModel):
    name: str | None = None
    email: EmailStr | None = None


"""
#################### Waste models ####################
"""


class WasteBase(SQLModel):
    name: str = Field(index=True, unique=True)


class Waste(WasteBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    company_links: list["CompanyWasteLink"] = Relationship(
        back_populates="waste",
        cascade_delete=True)
    storage_links: list["StorageWasteLink"] = Relationship(
        back_populates="waste",
        cascade_delete=True)


class WasteCreate(WasteBase):
    pass


class WastePublic(WasteBase):
    id: int


class WasteUpdate(WasteBase):
    name: str | None = None


"""
#################### Company Waste Link models ####################
"""


class CompanyWasteLinkBase(SQLModel):
    waste_id: int | None = Field(
        default=None, foreign_key="waste.id", primary_key=True)
    max_amount: int = Field(default=0, ge=0)


class CompanyWasteLink(CompanyWasteLinkBase, table=True):
    company_id: int | None = Field(
        default=None, foreign_key="company.id", primary_key=True)
    amount: int = Field(default=0, ge=0)
    # Relationships
    company: Company = Relationship(back_populates="waste_links")
    waste: Waste = Relationship(back_populates="company_links")


class CompanyWasteLinkPublic(CompanyWasteLinkBase):
    amount: int


class CompanyWasteLinkCreate(CompanyWasteLinkBase):
    pass


"""
#################### Storage Waste Link models ####################
"""


class StorageWasteLinkBase(SQLModel):
    waste_id: int | None = Field(
        default=None, foreign_key="waste.id", primary_key=True)
    max_amount: int = Field(default=0, ge=0)


class StorageWasteLink(StorageWasteLinkBase, table=True):
    storage_id: int | None = Field(
        default=None, foreign_key="storage.id", primary_key=True)
    amount: int = Field(default=0)
    # Relationships
    storage: Storage = Relationship(back_populates="waste_links")
    waste: Waste = Relationship(back_populates="storage_links")


class StorageWasteLinkPublic(StorageWasteLinkBase):
    amount: int


class StorageWasteLinkCreate(StorageWasteLinkBase):
    pass


"""
#################### Location models ####################
"""


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


"""
#################### Road models ####################
"""


class RoadBase(SQLModel):
    distance: int


class Road(RoadBase, table=True):
    location_from_id: int | None = Field(
        default=None, foreign_key="location.id", primary_key=True)
    location_to_id: int | None = Field(
        default=None, foreign_key="location.id", primary_key=True)

    location_from: Location = Relationship(
        back_populates="roads_from",
        sa_relationship_kwargs={"foreign_keys": "Road.location_from_id"})
    location_to: Location = Relationship(
        back_populates="roads_to",
        sa_relationship_kwargs={"foreign_keys": "Road.location_to_id"})


class RoadFromPublic(RoadBase):
    location_to: LocationPublic


class RoadToPublic(RoadBase):
    location_from: LocationPublic


class RoadUpdate(SQLModel):
    pass


"""
#################### Company Location Link models ####################
"""


class CompanyLocationLinkBase(SQLModel):
    location_id: int | None = Field(
        default=None, foreign_key="location.id", primary_key=True, unique=True)


class CompanyLocationLink(CompanyLocationLinkBase, table=True):
    company_id: int | None = Field(
        default=None, foreign_key="company.id", primary_key=True, unique=True)

    company: Company = Relationship(back_populates="location_link")
    location: Location = Relationship(back_populates="company_link")


class CompanyLocationLinkPublic(CompanyLocationLinkBase):
    pass


"""
#################### Storage Location Link models ####################
"""


class StorageLocationLinkBase(SQLModel):
    location_id: int | None = Field(
        default=None, foreign_key="location.id", primary_key=True, unique=True)


class StorageLocationLink(StorageLocationLinkBase, table=True):
    storage_id: int | None = Field(
        default=None, foreign_key="storage.id", primary_key=True, unique=True)

    storage: Storage = Relationship(back_populates="location_link")
    location: Location = Relationship(back_populates="storage_link")


class StorageLocationLinkPublic(StorageLocationLinkBase):
    pass


"""
#################### Route models ####################
"""


class RouteBase(SQLModel):
    waste: Waste
    route_history: list[Storage]
    distance: int


class Route(RouteBase):
    next_location: Location
    total_empty_space: int

    def __lt__(self, other: "Route"):
        return self.distance < other.distance

    def __hash__(self):
        return hash(self.next_location.id)

    # def __repr__(self):
    #     return f"route: {self.route_history}\ndistance: {self.distance}"


class RoutePublic(RouteBase):
    waste: WastePublic
    route_history: list[StoragePublic]
