from typing import Annotated

from fastapi import APIRouter, Depends, Body, HTTPException, status
from sqlmodel import Session

from .system import get_db_waste_by_id
from ..dependencies import get_session
from ..models import (
    Company, CompanyPublic, CompanyPublicWithWaste,
    CompanyCreate, CompanyUpdate,
    CompanyWasteLink, CompanyWasteLinkPublic, CompanyWasteLinkCreate
    )
from .. import crud


router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("/create/", response_model=CompanyPublic)
async def create_company(
        company: CompanyCreate, session: Session = Depends(get_session)):
    # Map to Company
    db_company = Company.model_validate(company)
    validate_email(session=session, email=db_company.email)
    return crud.create_db_object(session=session, db_object=db_company)


@router.get("/", response_model=list[CompanyPublic])
async def get_companies(
        skip: int = 0, limit: int = 10,
        session: Session = Depends(get_session)
        ):
    return crud.get_db_objects(
        session=session, db_class=Company, skip=skip, limit=limit)


@router.get("/{company_id}", response_model=CompanyPublicWithWaste)
async def get_company(
        company_id: int, session: Session = Depends(get_session)):
    db_company = get_db_company_by_id(session=session, company_id=company_id)
    return db_company


@router.patch("/{company_id}", response_model=CompanyPublic)
async def update_company(
        company_id: int, company: CompanyUpdate,
        session: Session = Depends(get_session)
        ):
    db_company = get_db_company_by_id(session=session, company_id=company_id)
    update_data = company.model_dump(exclude_unset=True)
    if update_data.get("email"):
        validate_email(session=session, email=update_data.get("email"))
    return crud.update_db_object(
        session=session, db_object=db_company, update_data=update_data)


@router.delete("/{company_id}")
async def delete_company(
        company_id: int, session: Session = Depends(get_session)):
    db_company = get_db_company_by_id(session=session, company_id=company_id)
    crud.delete_db_object(session=session, db_object=db_company)
    return {"ok": True}


@router.post("/{company_id}/waste-types/assign/",
             response_model=CompanyPublicWithWaste)
async def assign_company_waste_type(
        company_id: int, waste_link: CompanyWasteLinkCreate,
        session: Session = Depends(get_session)
        ):
    db_company = get_db_company_by_id(session=session, company_id=company_id)
    # Waste validation
    get_db_waste_by_id(session=session, waste_id=waste_link.waste_id)
    # Waste link validation
    db_waste_link = CompanyWasteLink.model_validate(waste_link)
    db_waste_link.company_id = company_id
    link_in_db = crud.get_db_link(
        session=session, db_table=CompanyWasteLink,
        id_field_1="company_id", value_1=company_id,
        id_field_2="waste_id", value_2=db_waste_link.waste_id
        )
    if link_in_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Waste type already assigned"
            )
    crud.create_db_object(
        session=session, db_object=db_waste_link)
    return db_company


@router.patch("/{company_id}/waste-types/{waste_id}/amount/",
              response_model=CompanyWasteLinkPublic)
async def update_company_waste_amount(
        company_id: int, waste_id: int,
        amount: Annotated[int, Body(embed=True, ge=0)],
        session: Session = Depends(get_session)
        ):
    # Company validation
    get_db_company_by_id(session=session, company_id=company_id)
    db_waste_link = get_db_company_waste_link(
        session=session, company_id=company_id, waste_id=waste_id)
    if amount > db_waste_link.max_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount can not be bigger than max amount"
            )
    update_data = {"amount": amount}
    return crud.update_db_object(
        session=session, db_object=db_waste_link, update_data=update_data)


@router.patch("/{company_id}/waste-types/{waste_id}/max-amount/",
              response_model=CompanyWasteLinkPublic)
async def update_company_waste_max_amount(
        company_id: int, waste_id: int,
        max_amount: Annotated[int, Body(embed=True, ge=0)],
        session: Session = Depends(get_session)
        ):
    # Company validation
    get_db_company_by_id(session=session, company_id=company_id)
    db_waste_link = get_db_company_waste_link(
        session=session, company_id=company_id, waste_id=waste_id)
    if max_amount < db_waste_link.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Max amount can not be smaller than amount"
            )
    update_data = {"max_amount": max_amount}
    return crud.update_db_object(
        session=session, db_object=db_waste_link, update_data=update_data)


@router.delete("/{company_id}/waste-types/{waste_id}")
async def delete_company_waste_type(
        company_id: int, waste_id: int,
        session: Session = Depends(get_session)
        ):
    # Company validation
    get_db_company_by_id(session=session, company_id=company_id)
    db_waste_link = get_db_company_waste_link(
        session=session, company_id=company_id, waste_id=waste_id)
    crud.delete_db_object(
        session=session, db_object=db_waste_link)
    return {"ok": True}


# Helper functions

def get_db_company_by_id(session: Session, company_id: int):
    db_company = crud.get_db_object_by_field(
        session=session, db_table=Company, field="id", value=company_id)
    if not db_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return db_company


def validate_email(session: Session, email: str):
    company_in_db = crud.get_db_object_by_field(
        session=session, db_table=Company, field="email", value=email)
    if company_in_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
            )


def get_db_company_waste_link(
        session: Session, company_id: int, waste_id: int):
    db_company_waste_link = crud.get_db_link(
        session=session, db_table=CompanyWasteLink,
        id_field_1="company_id", value_1=company_id,
        id_field_2="waste_id", value_2=waste_id
        )
    if not db_company_waste_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waste not assigned to the company"
            )
    return db_company_waste_link
