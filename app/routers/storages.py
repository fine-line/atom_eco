from functools import wraps

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlmodel import Session

from .wastes import get_db_waste_by_id
from .locations import create_roads
from ..database import get_session, get_fake_db_session
from ..models.storage import (
    Storage, StoragePublic, StoragePublicDetailed, StorageCreate,
    StorageUpdate
    )
from ..models.storagewastelink import (
    StorageWasteLink, StorageWasteLinkPublic, StorageWasteLinkCreate,
    StorageWasteLinkUpdate
    )
from ..models.storagelocationlink import StorageLocationLink
from ..models.location import Location, LocationCreate
from .. import crud
from ..security import hash_password
from .login import Role, authenticate_user_by_token


router = APIRouter(prefix="/storages", tags=["system"])


def authorize(roles: list):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            http_authorization_exception = HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized",
                        headers={"WWW-Authenticate": "Bearer"}
                        )
            user = kwargs.get("current_user")
            user_role, user_id = user.split(":")
            if user_role not in roles:
                raise http_authorization_exception
            if user_role == Role.STORAGE:
                storage_id = str(kwargs.get("storage_id"))
                if user_id != storage_id:
                    raise http_authorization_exception
            return func(*args, **kwargs)
        return wrapper
    return decorator


@router.post("/create/", response_model=StoragePublicDetailed)
@authorize(roles=[Role.ADMIN])
def create_storage(
        storage: StorageCreate,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)):
    hashed_password = hash_password(password=storage.password)
    extra_data = {"hashed_password": hashed_password}
    # Map to Storage
    db_storage = Storage.model_validate(storage, update=extra_data)
    validate_email(session=session, email=db_storage.email)
    return crud.create_db_object(session=session, db_object=db_storage)


@router.get("/", response_model=list[StoragePublic])
@authorize(roles=[Role.ADMIN])
def get_storages(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=10, le=100),
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)
        ):
    return crud.get_db_objects(
        session=session, db_class=Storage, skip=skip, limit=limit)


@router.get("/{storage_id}", response_model=StoragePublicDetailed,
            tags=["storages"])
@authorize(roles=[Role.ADMIN, Role.STORAGE])
def get_storage(
        storage_id: int,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)):
    db_storage = get_db_storage_by_id(session=session, storage_id=storage_id)
    return db_storage


@router.patch("/{storage_id}", response_model=StoragePublicDetailed,
              tags=["storages"])
@authorize(roles=[Role.ADMIN, Role.STORAGE])
def update_storage(
        storage_id: int, storage: StorageUpdate,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)
        ):
    db_storage = get_db_storage_by_id(session=session, storage_id=storage_id)
    update_data = storage.model_dump(exclude_unset=True)
    if "email" in update_data:
        validate_email(session=session, email=update_data["email"])
    if "password" in update_data:
        hashed_password = hash_password(password=update_data["password"])
        update_data.update({"hashed_password": hashed_password})
    return crud.update_db_object(
        session=session, db_object=db_storage, update_data=update_data)


@router.delete("/{storage_id}")
@authorize(roles=[Role.ADMIN])
def delete_storage(
        storage_id: int,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)
        ):
    db_storage = get_db_storage_by_id(session=session, storage_id=storage_id)
    crud.delete_db_object(session=session, db_object=db_storage)
    return {"ok": True}


@router.post("/{storage_id}/waste-types/assign/",
             response_model=StoragePublicDetailed)
@authorize(roles=[Role.ADMIN])
def assign_storage_waste_type(
        storage_id: int, waste_link: StorageWasteLinkCreate,
        current_user: str = Depends(authenticate_user_by_token),
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


@router.patch("/{storage_id}/waste-types/{waste_id}",
              response_model=StorageWasteLinkPublic, tags=["storages"])
@authorize(roles=[Role.ADMIN, Role.STORAGE])
def update_storage_waste_link(
        storage_id: int, waste_id: int, waste_link: StorageWasteLinkUpdate,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)
        ):
    # Storage validation
    get_db_storage_by_id(session=session, storage_id=storage_id)
    db_waste_link = get_db_storage_waste_link(
        session=session, storage_id=storage_id, waste_id=waste_id)
    update_data = waste_link.model_dump(exclude_unset=True)
    amount = update_data.get("amount", db_waste_link.amount)
    max_amount = update_data.get("max_amount", db_waste_link.max_amount)
    if amount > db_waste_link.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can not increase amount without recieving from company"
            )
    if amount > max_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount can not be bigger than max amount"
            )
    return crud.update_db_object(
        session=session, db_object=db_waste_link, update_data=update_data)


@router.delete("/{storage_id}/waste-types/{waste_id}")
@authorize(roles=[Role.ADMIN])
def delete_storage_waste_type(
        storage_id: int, waste_id: int,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)
        ):
    # Storage validation
    get_db_storage_by_id(session=session, storage_id=storage_id)
    db_waste_link = get_db_storage_waste_link(
        session=session, storage_id=storage_id, waste_id=waste_id)
    if db_waste_link.amount != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can not delete waste type if amount not 0"
            )
    crud.delete_db_object(
        session=session, db_object=db_waste_link)
    return {"ok": True}


@router.post("/{storage_id}/location/assign/",
             response_model=StoragePublicDetailed)
@authorize(roles=[Role.ADMIN])
def assign_storage_location(
        storage_id: int, location: LocationCreate,
        current_user: str = Depends(authenticate_user_by_token),
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
            detail="Location with that name already occupied"
            )
    # Check if location exist in fake db
    location_in_fake_db = crud.get_db_object_by_field(
        session=fake_db_session, db_table=Location,
        field="name", value=location.name
        )
    if not location_in_fake_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Location with that name does not exist"
            )
    # Check if another location already assigned to the storage
    if db_storage.location_link:
        crud.delete_db_object(
            session=session, db_object=db_storage.location_link.location)
    # Create location and location link
    db_location = crud.create_db_object(session=session, db_object=db_location)
    db_location_link = StorageLocationLink(
        storage=db_storage, location=db_location)
    crud.create_db_object(session=session, db_object=db_location_link)
    # Create roads, that connects only locations in db
    create_roads(
        session=session, location_in_fake_db=location_in_fake_db,
        db_location=db_location
        )
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
