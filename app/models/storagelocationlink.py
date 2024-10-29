from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .storage import Storage
    from .location import Location


class StorageLocationLinkBase(SQLModel):
    location_id: int | None = Field(
        default=None, foreign_key="location.id", primary_key=True, unique=True)


class StorageLocationLink(StorageLocationLinkBase, table=True):
    storage_id: int | None = Field(
        default=None, foreign_key="storage.id", primary_key=True, unique=True)

    storage: "Storage" = Relationship(back_populates="location_link")
    location: "Location" = Relationship(back_populates="storage_link")


class StorageLocationLinkPublic(StorageLocationLinkBase):
    pass
