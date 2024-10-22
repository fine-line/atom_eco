from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ..dependencies import get_session
from ..models import (
    Storage, StoragePublic, StorageCreate, StorageUpdate,
    StoragePublicWithWaste, StorageWasteLinkCreate, StorageWasteLink,
    StorageWasteLinkUpdate, StorageWasteLinkPublic
    )
from .. import crud


router = APIRouter(prefix="/storages", tags=["storages"])


@router.get("/", response_model=list[StoragePublic])
async def get_storages(
        skip: int = 0, limit: int = 10,
        session: Session = Depends(get_session)):
    return crud.get_storages(session=session, skip=skip, limit=limit)


@router.get("/{storage_id}", response_model=StoragePublicWithWaste)
async def get_storage(
        storage_id: int, session: Session = Depends(get_session)):
    db_storage = crud.get_storage_by_id(session=session, storage_id=storage_id)
    if not db_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Storage not found")
    return db_storage


@router.post("/create-storage/", response_model=StoragePublic)
async def create_storage(
        storage: StorageCreate, session: Session = Depends(get_session)):
    # Map to Storage
    db_storage = Storage.model_validate(storage)
    # Check for duplicate email
    storage_in_db = crud.get_storage_by_email(
        session=session, storage_email=storage.email)
    if storage_in_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered")
    return crud.create_storage(session=session, storage=db_storage)


@router.post("/{storage_id}/assign-waste-types",
             response_model=StoragePublicWithWaste)
async def add_waste_type(
        storage_id: int, waste_links: list[StorageWasteLinkCreate],
        session: Session = Depends(get_session)):
    # Storage validation
    db_storage = crud.get_storage_by_id(session=session, storage_id=storage_id)
    if not db_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Storage not found")
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
        db_waste_link = StorageWasteLink.model_validate(waste_link)
        db_waste_link.storage_id = storage_id
        link_in_db = crud.get_storage_waste_link(
            session=session, storage_id=storage_id,
            waste_id=db_waste_link.waste_id
            )
        if link_in_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Waste type already assigned"
                )
        crud.create_storage_waste_link(
            session=session, waste_link=db_waste_link)
    return db_storage


@router.patch("/{storage_id}", response_model=StoragePublic)
async def update_storage(
        storage_id: int, storage: StorageUpdate,
        session: Session = Depends(get_session)):
    db_storage = crud.get_storage_by_id(
        session=session, storage_id=storage_id)
    if not db_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Storage not found")
    storage_data = storage.model_dump(exclude_unset=True)
    return crud.update_storage(
        session=session, storage=db_storage, storage_data=storage_data)


@router.patch("/{storage_id}/waste-type/",
              response_model=StorageWasteLinkPublic)
async def update_storage_waste_type(
        storage_id: int, storage_waste_link: StorageWasteLinkUpdate,
        session: Session = Depends(get_session)):
    db_storage = crud.get_storage_by_id(
        session=session, storage_id=storage_id)
    if not db_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Storage not found")
    db_waste_link = crud.get_storage_waste_link(
        session=session, storage_id=storage_id,
        waste_id=storage_waste_link.waste_id
        )
    if not db_waste_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waste not assigned to the storage"
            )
    waste_link_data = storage_waste_link.model_dump(exclude_unset=True)
    return crud.update_storage_waste_link(
        session=session, storage_waste_link=db_waste_link,
        waste_link_data=waste_link_data
        )


@router.delete("/{storage_id}/waste-type/{waste_id}")
async def delete_storage_waste_type(
        storage_id: int, waste_id: int,
        session: Session = Depends(get_session)):
    db_storage = crud.get_storage_by_id(
        session=session, storage_id=storage_id)
    if not db_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Storage not found")
    db_waste_link = crud.get_storage_waste_link(
        session=session, storage_id=storage_id, waste_id=waste_id)
    if not db_waste_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waste not assigned to the storage"
            )
    crud.delete_storage_waste_link(
        session=session, storage_waste_link=db_waste_link)
    return {"ok": True}


@router.delete("/{storage_id}")
async def delete_storage(
        storage_id: int, session: Session = Depends(get_session)):
    db_storage = crud.get_storage_by_id(
        session=session, storage_id=storage_id)
    if not db_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Storage not found")
    crud.delete_storage(session=session, storage=db_storage)
    return {"ok": True}
