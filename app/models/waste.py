from sqlmodel import Field, Relationship, SQLModel

from .companywastelink import CompanyWasteLink
from .storagewastelink import StorageWasteLink


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
