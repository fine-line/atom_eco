from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .company import Company
    from .waste import Waste


class CompanyWasteLinkBase(SQLModel):
    waste_id: int | None = Field(
        default=None, foreign_key="waste.id", primary_key=True)
    max_amount: int = Field(default=0, ge=0)


class CompanyWasteLink(CompanyWasteLinkBase, table=True):
    company_id: int | None = Field(
        default=None, foreign_key="company.id", primary_key=True)
    amount: int = Field(default=0, ge=0)
    # Relationships
    company: "Company" = Relationship(back_populates="waste_links")
    waste: "Waste" = Relationship(back_populates="company_links")


class CompanyWasteLinkPublic(CompanyWasteLinkBase):
    amount: int


class CompanyWasteLinkCreate(CompanyWasteLinkBase):
    pass
