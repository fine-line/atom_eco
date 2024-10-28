from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlmodel import Session

from ..dependencies import get_session, get_fake_db_session
from ..models import Location, LocationPublic, LocationPublicWithRoad
from .. import crud
from .login import Role, authenticate_user_by_token, authorize


router = APIRouter(prefix="/locations", tags=["system"])


@router.get("/", response_model=list[LocationPublic])
@authorize(roles=[Role.ADMIN])
async def get_locations(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=10, le=100),
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)
        ):
    return crud.get_db_objects(
        session=session, db_class=Location, skip=skip, limit=limit)


@router.get("/{location_id}", response_model=LocationPublicWithRoad)
@authorize(roles=[Role.ADMIN])
async def get_location(
        location_id: int,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)
        ):
    db_location = crud.get_db_object_by_field(
        session=session, db_table=Location, field="id", value=location_id)
    if not db_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return db_location


@router.get("/available-location-names/", response_model=list[str])
@authorize(roles=[Role.ADMIN])
async def get_available_location_names(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=10, le=100),
        current_user: str = Depends(authenticate_user_by_token),
        fake_db_session: Session = Depends(get_fake_db_session)
        ):
    fake_db_locations = crud.get_db_objects(
        session=fake_db_session, db_class=Location, skip=skip, limit=limit)
    location_names = []
    for location in fake_db_locations:
        location_names.append(location.name)
    return location_names


@router.delete("/{location_id}")
@authorize(roles=[Role.ADMIN])
async def delete_location(
        location_id: int,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)
        ):
    db_location = crud.get_db_object_by_field(
        session=session, db_table=Location, field="id", value=location_id)
    if not db_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    crud.delete_db_object(session=session, db_object=db_location)
    return {"ok": True}
