from sqlmodel import Field, Relationship, SQLModel, AutoString
from pydantic import EmailStr

"""
#################### Company models ####################
"""
# class Company(SQLModel, table=True):
#     # DB columns
#     id: int | None = Field(default=None, primary_key=True)
#     name: str = Field(index=True)
#     email: EmailStr = Field(sa_type=AutoString, unique=True, index=True)
#     # Relationships
#     waste_links: list["CompanyWasteLink"] = Relationship(
#         back_populates="company",
#         cascade_delete=True)
#     location_link: "CompanyLocationLink" = Relationship(
#         back_populates="company",
#         cascade_delete=True)


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


class CompanyPublicWithWaste(CompanyPublic):
    id: int
    waste_links: list["CompanyWasteLinkPublic"]


class CompanyUpdate(SQLModel):
    name: str | None = None
    email: EmailStr | None = None


"""
#################### Storage models ####################
"""
# class Storage(SQLModel, table=True):
#     # DB columns
#     id: int | None = Field(default=None, primary_key=True)
#     name: str = Field(index=True)
#     email: EmailStr = Field(sa_type=AutoString, unique=True, index=True)
#     # Relationships
#     waste_links: list["StorageWasteLink"] = Relationship(
#         back_populates="storage",
#         cascade_delete=True)
#     location_link: "StorageLocationLink" = Relationship(
#         back_populates="storage",
#         cascade_delete=True)


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


class StoragePublicWithWaste(StoragePublic):
    id: int
    waste_links: list["StorageWasteLinkPublic"]


class StorageUpdate(SQLModel):
    name: str | None = None
    email: EmailStr | None = None


"""
#################### Waste models ####################
"""
# class Waste(SQLModel, table=True):
#     # DB columns
#     id: int | None = Field(default=None, primary_key=True)
#     name: str = Field(index=True)
#     # Relationships
#     company_links: list["CompanyWasteLink"] = Relationship(
#         back_populates="waste",
#         cascade_delete=True)
#     storage_links: list["StorageWasteLink"] = Relationship(
#         back_populates="waste",
#         cascade_delete=True)


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
# class CompanyWasteLink(SQLModel, table=True):
#     # DB columns
#     company_id: int | None = Field(
#         default=None, foreign_key="company.id", primary_key=True)
#     waste_id: int | None = Field(
#         default=None, foreign_key="waste.id", primary_key=True)
#     amount: int
#     max_amount: int
#     # Relationships
#     company: Company = Relationship(back_populates="waste_links")
#     waste: Waste = Relationship(back_populates="company_links")


class CompanyWasteLinkBase(SQLModel):
    waste_id: int | None = Field(
        default=None, foreign_key="waste.id", primary_key=True)
    max_amount: int


class CompanyWasteLink(CompanyWasteLinkBase, table=True):
    company_id: int | None = Field(
        default=None, foreign_key="company.id", primary_key=True)
    amount: int = Field(default=0)
    # Relationships
    company: Company = Relationship(back_populates="waste_links")
    waste: Waste = Relationship(back_populates="company_links")


class CompanyWasteLinkPublic(CompanyWasteLinkBase):
    amount: int


class CompanyWasteLinkCreate(CompanyWasteLinkBase):
    pass


class CompanyWasteLinkUpdate(SQLModel):
    waste_id: int
    amount: int | None = None
    max_amount: int | None = None


"""
#################### Storage Waste Link models ####################
"""


# class StorageWasteLink(SQLModel, table=True):
#     # DB columns
#     storage_id: int | None = Field(
#         default=None, foreign_key="storage.id", primary_key=True)
#     waste_id: int | None = Field(
#         default=None, foreign_key="waste.id", primary_key=True)
#     amount: int
#     max_amount: int
#     # Relationships
#     storage: Storage = Relationship(back_populates="waste_links")
#     waste: Waste = Relationship(back_populates="storage_links")


class StorageWasteLinkBase(SQLModel):
    waste_id: int | None = Field(
        default=None, foreign_key="waste.id", primary_key=True)
    max_amount: int


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


class StorageWasteLinkUpdate(SQLModel):
    waste_id: int
    amount: int | None = None
    max_amount: int | None = None


"""
#################### Location models ####################
"""


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
    company_links: "CompanyLocationLink" = Relationship(
        back_populates="location",
        cascade_delete=True)
    storage_links: "StorageLocationLink" = Relationship(
        back_populates="location",
        cascade_delete=True)


"""
#################### Road models ####################
"""


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


"""
#################### Company Location Link models ####################
"""


class CompanyLocationLink(SQLModel, table=True):
    # DB columns
    company_id: int | None = Field(
        default=None, foreign_key="company.id", primary_key=True, unique=True)
    location_id: int | None = Field(
        default=None, foreign_key="location.id", primary_key=True, unique=True)
    # Relationships
    company: Company = Relationship(back_populates="location_link")
    location: Location = Relationship(back_populates="company_links")


"""
#################### Storage Location Link models ####################
"""


class StorageLocationLink(SQLModel, table=True):
    # DB columns
    storage_id: int | None = Field(
        default=None, foreign_key="storage.id", primary_key=True, unique=True)
    location_id: int | None = Field(
        default=None, foreign_key="location.id", primary_key=True, unique=True)
    # Relationships
    storage: Storage = Relationship(back_populates="location_link")
    location: Location = Relationship(back_populates="storage_links")
