from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ..dependencies import get_session
from ..models import (
    Company, CompanyPublic, CompanyCreate, CompanyUpdate,
    CompanyPublicWithWaste, CompanyWasteLinkCreate, CompanyWasteLink,
    CompanyWasteLinkUpdate, CompanyWasteLinkPublic
    )
from .. import crud


router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/", response_model=list[CompanyPublic])
async def get_companies(
        skip: int = 0, limit: int = 10,
        session: Session = Depends(get_session)):
    return crud.get_companies(session=session, skip=skip, limit=limit)


@router.get("/{company_id}", response_model=CompanyPublicWithWaste)
async def get_company(
        company_id: int, session: Session = Depends(get_session)):
    db_company = crud.get_company_by_id(session=session, company_id=company_id)
    if not db_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return db_company


@router.post("/create-company/", response_model=CompanyPublic)
async def create_company(
        company: CompanyCreate, session: Session = Depends(get_session)):
    # Map to Company
    db_company = Company.model_validate(company)
    # Check for duplicate email
    company_in_db = crud.get_company_by_email(
        session=session, company_email=company.email)
    if company_in_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered")
    return crud.create_company(session=session, company=db_company)


@router.post("/{company_id}/assign-waste-types",
             response_model=CompanyPublicWithWaste)
async def add_waste_type(
        company_id: int, waste_links: list[CompanyWasteLinkCreate],
        session: Session = Depends(get_session)):
    # Company validation
    db_company = crud.get_company_by_id(session=session, company_id=company_id)
    if not db_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    for waste_link in waste_links:
        # Waste validation
        db_waste = crud.get_waste_by_id(
            session=session, waste_id=waste_link.waste_id)
        if not db_waste:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Waste not found"
                )
        # Waste link validation
        db_waste_link = CompanyWasteLink.model_validate(waste_link)
        db_waste_link.company_id = company_id
        link_in_db = crud.get_company_waste_link(
            session=session, company_id=company_id,
            waste_id=db_waste_link.waste_id
            )
        if link_in_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Waste type already assigned"
                )
        crud.create_company_waste_link(
            session=session, waste_link=db_waste_link)
    return db_company


@router.patch("/{company_id}", response_model=CompanyPublic)
async def update_company(
        company_id: int, company: CompanyUpdate,
        session: Session = Depends(get_session)):
    db_company = crud.get_company_by_id(
        session=session, company_id=company_id)
    if not db_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    company_data = company.model_dump(exclude_unset=True)
    return crud.update_company(
        session=session, company=db_company, company_data=company_data)


@router.patch("/{company_id}/waste-type/",
              response_model=CompanyWasteLinkPublic)
async def update_company_waste_type(
        company_id: int, company_waste_link: CompanyWasteLinkUpdate,
        session: Session = Depends(get_session)):
    db_company = crud.get_company_by_id(
        session=session, company_id=company_id)
    if not db_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    db_waste_link = crud.get_company_waste_link(
        session=session, company_id=company_id,
        waste_id=company_waste_link.waste_id
        )
    if not db_waste_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waste not assigned to the company"
            )
    waste_link_data = company_waste_link.model_dump(exclude_unset=True)
    return crud.update_company_waste_link(
        session=session, company_waste_link=db_waste_link,
        waste_link_data=waste_link_data
        )


@router.delete("/{company_id}/waste-type/{waste_id}")
async def delete_company_waste_type(
        company_id: int, waste_id: int,
        session: Session = Depends(get_session)):
    db_company = crud.get_company_by_id(
        session=session, company_id=company_id)
    if not db_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    db_waste_link = crud.get_company_waste_link(
        session=session, company_id=company_id, waste_id=waste_id)
    if not db_waste_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waste not assigned to the company"
            )
    crud.delete_company_waste_link(
        session=session, company_waste_link=db_waste_link)
    return {"ok": True}


@router.delete("/{company_id}")
async def delete_company(
        company_id: int, session: Session = Depends(get_session)):
    db_company = crud.get_company_by_id(
        session=session, company_id=company_id)
    if not db_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    crud.delete_company(session=session, company=db_company)
    return {"ok": True}
