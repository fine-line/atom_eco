from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlmodel import Session

from ..database import get_session
from ..models.waste import Waste, WasteCreate, WastePublic, WasteUpdate
from .. import crud
from .login import Role, authenticate_user_by_token, authorize


router = APIRouter(prefix="/wastes", tags=["system"])


@router.post("/create/", response_model=WastePublic)
@authorize(roles=[Role.ADMIN])
def create_waste(
        waste: WasteCreate,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)
        ):
    # Map to Waste
    db_waste = Waste.model_validate(waste)
    # Check for duplicate name
    waste_in_db = crud.get_db_object_by_field(
        session=session, db_table=Waste, field="name", value=waste.name)
    if waste_in_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Waste with that name already exists"
            )
    return crud.create_db_object(session=session, db_object=db_waste)


@router.get("/", response_model=list[WastePublic],
            tags=["companies", "storages"])
@authorize(roles=[Role.ADMIN, Role.COMPANY, Role.STORAGE])
def get_wastes(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=10, le=100),
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)
        ):
    return crud.get_db_objects(
        session=session, db_class=Waste, skip=skip, limit=limit)


@router.get("/{waste_id}", response_model=WastePublic)
@authorize(roles=[Role.ADMIN])
def get_waste(
        waste_id:  int,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)
        ):
    db_waste = crud.get_db_object_by_field(
        session=session, db_table=Waste, field="id", value=waste_id)
    if not db_waste:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Waste not found")
    return db_waste


@router.patch("/{waste_id}", response_model=WastePublic)
@authorize(roles=[Role.ADMIN])
def update_waste(
        waste_id: int, waste: WasteUpdate,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)
        ):
    db_waste = crud.get_db_object_by_field(
        session=session, db_table=Waste, field="id", value=waste_id)
    if not db_waste:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Waste not found")
    # TODO validation of waste name
    update_data = waste.model_dump(exclude_unset=True)
    return crud.update_db_object(
        session=session, db_object=db_waste, update_data=update_data)


@router.delete("/{waste_id}")
@authorize(roles=[Role.ADMIN])
def delete_waste(
        waste_id: int,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)
        ):
    db_waste = crud.get_db_object_by_field(
        session=session, db_table=Waste, field="id", value=waste_id)
    if not db_waste:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Waste not found")
    crud.delete_db_object(session=session, db_object=db_waste)
    return {"ok": True}


# Helper functions

def get_db_waste_by_id(session: Session, waste_id: int):
    db_waste = crud.get_db_object_by_field(
        session=session, db_table=Waste, field="id", value=waste_id)
    if not db_waste:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waste not found"
            )
    return db_waste
