from typing import Optional

from sqlmodel import Field, Relationship, SQLModel, AutoString
from pydantic import EmailStr

from .storagewastelink import StorageWasteLink, StorageWasteLinkPublic
from .storagelocationlink import (
    StorageLocationLink, StorageLocationLinkPublic)


class StorageBase(SQLModel):
    name: str = Field(index=True)


class Storage(StorageBase,  table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr = Field(sa_type=AutoString, unique=True, index=True)
    hashed_password: str = Field()

    waste_links: list["StorageWasteLink"] = Relationship(
        back_populates="storage",
        cascade_delete=True)
    location_link: "StorageLocationLink" = Relationship(
        back_populates="storage",
        cascade_delete=True)


class StorageCreate(StorageBase):
    email: EmailStr
    password: str


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
    password: str | None = None
