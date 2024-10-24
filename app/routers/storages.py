from typing import Annotated

from fastapi import APIRouter, Depends, Body, Query, HTTPException, status
from sqlmodel import Session

from .waste import get_db_waste_by_id
from ..dependencies import get_session, get_fake_db_session
from ..models import (
    Storage, StoragePublic, StoragePublicDetailed,
    StorageCreate, StorageUpdate,
    StorageWasteLink, StorageWasteLinkPublic, StorageWasteLinkCreate,
    StorageLocationLink, Location, LocationCreate, Road
    )
from .. import crud


router = APIRouter(prefix="/storages", tags=["storages"])


@router.post("/create/", response_model=StoragePublicDetailed)
async def create_storage(
        storage: StorageCreate, session: Session = Depends(get_session)):
    # Map to Storage
    db_storage = Storage.model_validate(storage)
    validate_email(session=session, email=db_storage.email)
    return crud.create_db_object(session=session, db_object=db_storage)


@router.get("/", response_model=list[StoragePublic])
async def get_storages(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=10, le=100),
        session: Session = Depends(get_session)
        ):
    return crud.get_db_objects(
        session=session, db_class=Storage, skip=skip, limit=limit)


@router.get("/{storage_id}", response_model=StoragePublicDetailed)
async def get_storage(
        storage_id: int, session: Session = Depends(get_session)):
    db_storage = get_db_storage_by_id(session=session, storage_id=storage_id)
    return db_storage


@router.patch("/{storage_id}", response_model=StoragePublic)
async def update_storage(
        storage_id: int, storage: StorageUpdate,
        session: Session = Depends(get_session)
        ):
    db_storage = get_db_storage_by_id(session=session, storage_id=storage_id)
    update_data = storage.model_dump(exclude_unset=True)
    if update_data.get("email"):
        validate_email(session=session, email=update_data.get("email"))
    return crud.update_db_object(
        session=session, db_object=db_storage, update_data=update_data)


@router.delete("/{storage_id}")
async def delete_storage(
        storage_id: int, session: Session = Depends(get_session)):
    db_storage = get_db_storage_by_id(session=session, storage_id=storage_id)
    crud.delete_db_object(session=session, db_object=db_storage)
    return {"ok": True}


@router.post("/{storage_id}/waste-types/assign/",
             response_model=StoragePublicDetailed)
async def assign_storage_waste_type(
        storage_id: int, waste_link: StorageWasteLinkCreate,
        session: Session = Depends(get_session)
        ):
    db_storage = get_db_storage_by_id(session=session, storage_id=storage_id)
    # Waste validation
    get_db_waste_by_id(session=session, waste_id=waste_link.waste_id)
    # Waste link validation
    db_waste_link = StorageWasteLink.model_validate(waste_link)
    db_waste_link.storage_id = storage_id
    link_in_db = crud.get_db_link(
        session=session, db_table=StorageWasteLink,
        id_field_1="storage_id", value_1=storage_id,
        id_field_2="waste_id", value_2=db_waste_link.waste_id
        )
    if link_in_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Waste type already assigned"
            )
    crud.create_db_object(
        session=session, db_object=db_waste_link)
    return db_storage


@router.patch("/{storage_id}/waste-types/{waste_id}/amount/",
              response_model=StorageWasteLinkPublic)
async def update_storage_waste_amount(
        storage_id: int, waste_id: int,
        amount: Annotated[int, Body(embed=True, ge=0)],
        session: Session = Depends(get_session)
        ):
    # Storage validation
    get_db_storage_by_id(session=session, storage_id=storage_id)
    db_waste_link = get_db_storage_waste_link(
        session=session, storage_id=storage_id, waste_id=waste_id)
    if amount > db_waste_link.max_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount can not be bigger than max amount"
            )
    update_data = {"amount": amount}
    return crud.update_db_object(
        session=session, db_object=db_waste_link, update_data=update_data)


@router.patch("/{storage_id}/waste-types/{waste_id}/max-amount/",
              response_model=StorageWasteLinkPublic)
async def update_storage_waste_max_amount(
        storage_id: int, waste_id: int,
        max_amount: Annotated[int, Body(embed=True, ge=0)],
        session: Session = Depends(get_session)
        ):
    # Storage validation
    get_db_storage_by_id(session=session, storage_id=storage_id)
    db_waste_link = get_db_storage_waste_link(
        session=session, storage_id=storage_id, waste_id=waste_id)
    if max_amount < db_waste_link.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Max amount can not be smaller than amount"
            )
    update_data = {"max_amount": max_amount}
    return crud.update_db_object(
        session=session, db_object=db_waste_link, update_data=update_data)


@router.delete("/{storage_id}/waste-types/{waste_id}")
async def delete_storage_waste_type(
        storage_id: int, waste_id: int,
        session: Session = Depends(get_session)
        ):
    # Storage validation
    get_db_storage_by_id(session=session, storage_id=storage_id)
    db_waste_link = get_db_storage_waste_link(
        session=session, storage_id=storage_id, waste_id=waste_id)
    crud.delete_db_object(
        session=session, db_object=db_waste_link)
    return {"ok": True}


@router.post("/{storage_id}/location/assign/",
             response_model=StoragePublicDetailed)
async def assign_storage_location(
        storage_id: int, location: LocationCreate,
        session: Session = Depends(get_session),
        fake_db_session: Session = Depends(get_fake_db_session)
        ):
    db_storage = get_db_storage_by_id(session=session, storage_id=storage_id)
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
    # Check if location already assigned
    if db_storage.location_link:
        crud.delete_db_object(
            session=session, db_object=db_storage.location_link.location)
    # Create location link
    db_location = crud.create_db_object(session=session, db_object=db_location)
    db_location_link = StorageLocationLink(
        storage=db_storage, location=db_location)
    crud.create_db_object(session=session, db_object=db_location_link)
    # Get all roads for that location from fake db
    roads_from = location_in_fake_db.roads_from
    roads_to = location_in_fake_db.roads_to
    # Add only roads to locations that exist in db (assigned to objects)
    for road in roads_from:
        db_connected_location = crud.get_db_object_by_field(
            session=session, db_table=Location,
            field="name", value=road.location_to.name
        )
        if db_connected_location:
            db_road = Road(location_from=db_location,
                           location_to=db_connected_location,
                           distance=road.distance
                           )
            crud.create_db_object(session=session, db_object=db_road)
    for road in roads_to:
        db_connected_location = crud.get_db_object_by_field(
            session=session, db_table=Location,
            field="name", value=road.location_from.name
        )
        if db_connected_location:
            db_road = Road(location_from=db_connected_location,
                           location_to=db_location,
                           distance=road.distance
                           )
            crud.create_db_object(session=session, db_object=db_road)
    return db_storage


# Helper functions

def get_db_storage_by_id(session: Session, storage_id: int) -> Storage:
    db_storage = crud.get_db_object_by_field(
        session=session, db_table=Storage, field="id", value=storage_id)
    if not db_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Storage not found")
    return db_storage


def validate_email(session: Session, email: str):
    storage_in_db = crud.get_db_object_by_field(
        session=session, db_table=Storage, field="email", value=email)
    if storage_in_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
            )


def get_db_storage_waste_link(
        session: Session, storage_id: int, waste_id: int) -> StorageWasteLink:
    db_storage_waste_link = crud.get_db_link(
        session=session, db_table=StorageWasteLink,
        id_field_1="storage_id", value_1=storage_id,
        id_field_2="waste_id", value_2=waste_id
        )
    if not db_storage_waste_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waste not assigned to the storage"
            )
    return db_storage_waste_link
