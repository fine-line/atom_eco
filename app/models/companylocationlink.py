from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .company import Company
    from .location import Location


class CompanyLocationLinkBase(SQLModel):
    location_id: int | None = Field(
        default=None, foreign_key="location.id", primary_key=True, unique=True)


class CompanyLocationLink(CompanyLocationLinkBase, table=True):
    company_id: int | None = Field(
        default=None, foreign_key="company.id", primary_key=True, unique=True)

    company: "Company" = Relationship(back_populates="location_link")
    location: "Location" = Relationship(back_populates="company_link")


class CompanyLocationLinkPublic(CompanyLocationLinkBase):
    pass
