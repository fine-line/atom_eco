from typing import Optional

from sqlmodel import Field, Relationship, SQLModel, AutoString
from pydantic import EmailStr

from .companywastelink import CompanyWasteLink, CompanyWasteLinkPublic
from .companylocationlink import (
    CompanyLocationLink, CompanyLocationLinkPublic)


class CompanyBase(SQLModel):
    name: str = Field(index=True)


class Company(CompanyBase,  table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr = Field(sa_type=AutoString, unique=True, index=True)
    hashed_password: str = Field()

    waste_links: list["CompanyWasteLink"] = Relationship(
        back_populates="company",
        cascade_delete=True)
    location_link: "CompanyLocationLink" = Relationship(
        back_populates="company",
        cascade_delete=True)


class CompanyCreate(CompanyBase):
    email: EmailStr
    password: str


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
    password: str | None = None
