from typing import Annotated
from functools import wraps

from fastapi import APIRouter, Depends, Body, Query, HTTPException, status
from sqlmodel import Session

from .waste import get_db_waste_by_id
from .locations import create_roads
from ..business_logic.optimal_route import find_optimal_route
from ..database import get_session, get_fake_db_session
from ..models.company import (
    Company, CompanyPublic, CompanyPublicDetailed, CompanyCreate,
    CompanyUpdate
    )
from ..models.companywastelink import (
    CompanyWasteLink, CompanyWasteLinkPublic, CompanyWasteLinkCreate)
from ..models.companylocationlink import CompanyLocationLink
from ..models.location import Location, LocationCreate
from ..models.route import RoutePublic
from .. import crud
from ..security import hash_password
from .login import Role, authenticate_user_by_token


router = APIRouter(prefix="/companies", tags=["system"])


def authorize(roles: list):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            http_authorization_exception = HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized",
                        headers={"WWW-Authenticate": "Bearer"}
                        )
            user = kwargs.get("current_user")
            user_role, user_id = user.split(":")
            if user_role not in roles:
                raise http_authorization_exception
            if user_role == Role.COMPANY:
                company_id = str(kwargs.get("company_id"))
                if user_id != company_id:
                    raise http_authorization_exception
            return await func(*args, **kwargs)
        return wrapper
    return decorator


@router.post("/create/", response_model=CompanyPublicDetailed)
@authorize(roles=[Role.ADMIN])
async def create_company(
        company: CompanyCreate,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)):
    hashed_password = hash_password(password=company.password)
    extra_data = {"hashed_password": hashed_password}
    # Map to Company
    db_company = Company.model_validate(company, update=extra_data)
    validate_email(session=session, email=db_company.email)
    return crud.create_db_object(session=session, db_object=db_company)


@router.get("/", response_model=list[CompanyPublic])
@authorize(roles=[Role.ADMIN])
async def get_companies(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=10, le=100),
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)
        ):
    return crud.get_db_objects(
        session=session, db_class=Company, skip=skip, limit=limit)


@router.get("/{company_id}", response_model=CompanyPublicDetailed,
            tags=["companies"])
@authorize(roles=[Role.ADMIN, Role.COMPANY])
async def get_company(
        company_id: int,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)):
    db_company = get_db_company_by_id(session=session, company_id=company_id)
    return db_company


@router.patch("/{company_id}", response_model=CompanyPublic,
              tags=["companies"])
@authorize(roles=[Role.ADMIN, Role.COMPANY])
async def update_company(
        company_id: int, company: CompanyUpdate,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)
        ):
    db_company = get_db_company_by_id(session=session, company_id=company_id)
    update_data = company.model_dump(exclude_unset=True)
    if "email" in update_data:
        validate_email(session=session, email=update_data["email"])
    if "password" in update_data:
        hashed_password = hash_password(password=update_data["password"])
        update_data.update({"hashed_password": hashed_password})
    return crud.update_db_object(
        session=session, db_object=db_company, update_data=update_data)


@router.delete("/{company_id}")
@authorize(roles=[Role.ADMIN])
async def delete_company(
        company_id: int,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)):
    db_company = get_db_company_by_id(session=session, company_id=company_id)
    crud.delete_db_object(session=session, db_object=db_company)
    return {"ok": True}


@router.post("/{company_id}/waste-types/assign/",
             response_model=CompanyPublicDetailed)
@authorize(roles=[Role.ADMIN])
async def assign_company_waste_type(
        company_id: int, waste_link: CompanyWasteLinkCreate,
        current_user: str = Depends(authenticate_user_by_token),
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
              response_model=CompanyWasteLinkPublic, tags=["companies"])
@authorize(roles=[Role.ADMIN, Role.COMPANY])
async def update_company_waste_amount(
        company_id: int, waste_id: int,
        amount: Annotated[int, Body(embed=True, ge=0)],
        current_user: str = Depends(authenticate_user_by_token),
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
    if amount < db_waste_link.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can not decrease amount without unloading"
            )
    update_data = {"amount": amount}
    return crud.update_db_object(
        session=session, db_object=db_waste_link, update_data=update_data)


@router.patch("/{company_id}/waste-types/{waste_id}/max-amount/",
              response_model=CompanyWasteLinkPublic, tags=["companies"])
@authorize(roles=[Role.ADMIN, Role.COMPANY])
async def update_company_waste_max_amount(
        company_id: int, waste_id: int,
        max_amount: Annotated[int, Body(embed=True, ge=0)],
        current_user: str = Depends(authenticate_user_by_token),
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
@authorize(roles=[Role.ADMIN])
async def delete_company_waste_type(
        company_id: int, waste_id: int,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)
        ):
    # Company validation
    get_db_company_by_id(session=session, company_id=company_id)
    db_waste_link = get_db_company_waste_link(
        session=session, company_id=company_id, waste_id=waste_id)
    if db_waste_link.amount != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can not delete waste type if amount not 0"
            )
    crud.delete_db_object(
        session=session, db_object=db_waste_link)
    return {"ok": True}


@router.post("/{company_id}/location/assign/",
             response_model=CompanyPublicDetailed)
@authorize(roles=[Role.ADMIN])
async def assign_company_location(
        company_id: int, location: LocationCreate,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session),
        fake_db_session: Session = Depends(get_fake_db_session)
        ):
    db_company = get_db_company_by_id(session=session, company_id=company_id)
    # Map to Location
    db_location = Location.model_validate(location)
    # Check for duplicate name
    location_in_db = crud.get_db_object_by_field(
        session=session, db_table=Location, field="name", value=location.name)
    if location_in_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Location with that name already occupied")
    # Check if location exist in fake db
    location_in_fake_db = crud.get_db_object_by_field(
        session=fake_db_session, db_table=Location,
        field="name", value=location.name
        )
    if not location_in_fake_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Location with that name does not exist")
    # Check if another location already assigned to the company
    if db_company.location_link:
        crud.delete_db_object(
            session=session, db_object=db_company.location_link.location)
    # Create location and location link
    db_location = crud.create_db_object(session=session, db_object=db_location)
    db_location_link = CompanyLocationLink(
        company=db_company, location=db_location)
    crud.create_db_object(session=session, db_object=db_location_link)
    # Create roads, that connects only locations in db
    create_roads(
        session=session, location_in_fake_db=location_in_fake_db,
        db_location=db_location
        )
    return db_company


@router.get("/{company_id}/optimal-route/", response_model=list[RoutePublic],
            tags=["companies"])
@authorize(roles=[Role.ADMIN, Role.COMPANY])
async def get_optimal_route(
        company_id: int,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)
        ):
    db_company = get_db_company_by_id(session=session, company_id=company_id)
    if not db_company.location_link:
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Location is not assigned to the company")
    routes = []
    for company_waste_link in db_company.waste_links:
        route = find_optimal_route(
            company=db_company, company_waste_link=company_waste_link)
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found")
        routes.append(route)
    return routes


# Helper functions

def get_db_company_by_id(session: Session, company_id: int) -> Company:
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
        session: Session, company_id: int, waste_id: int) -> CompanyWasteLink:
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
