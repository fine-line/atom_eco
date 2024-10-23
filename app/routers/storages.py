from typing import Annotated

from fastapi import APIRouter, Depends, Body, HTTPException, status
from sqlmodel import Session

from .system import get_db_waste_by_id
from ..dependencies import get_session
from ..models import (
    Storage, StoragePublic, StoragePublicWithWaste,
    StorageCreate, StorageUpdate,
    StorageWasteLink, StorageWasteLinkPublic, StorageWasteLinkCreate
    )
from .. import crud


router = APIRouter(prefix="/storages", tags=["storages"])


@router.post("/create/", response_model=StoragePublic)
async def create_storage(
        storage: StorageCreate, session: Session = Depends(get_session)):
    # Map to Storage
    db_storage = Storage.model_validate(storage)
    validate_email(session=session, email=db_storage.email)
    return crud.create_db_object(session=session, db_object=db_storage)


@router.get("/", response_model=list[StoragePublic])
async def get_storages(
        skip: int = 0, limit: int = 10,
        session: Session = Depends(get_session)
        ):
    return crud.get_db_objects(
        session=session, db_class=Storage, skip=skip, limit=limit)


@router.get("/{storage_id}", response_model=StoragePublicWithWaste)
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
             response_model=StoragePublicWithWaste)
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


# Helper functions

def get_db_storage_by_id(session: Session, storage_id: int):
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
        session: Session, storage_id: int, waste_id: int):
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
