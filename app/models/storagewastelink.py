from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .storage import Storage
    from .waste import Waste


class StorageWasteLinkBase(SQLModel):
    waste_id: int | None = Field(
        default=None, foreign_key="waste.id", primary_key=True)
    max_amount: int = Field(default=0, ge=0)


class StorageWasteLink(StorageWasteLinkBase, table=True):
    storage_id: int | None = Field(
        default=None, foreign_key="storage.id", primary_key=True)
    amount: int = Field(default=0)
    # Relationships
    storage: "Storage" = Relationship(back_populates="waste_links")
    waste: "Waste" = Relationship(back_populates="storage_links")


class StorageWasteLinkPublic(StorageWasteLinkBase):
    amount: int


class StorageWasteLinkCreate(StorageWasteLinkBase):
    pass
