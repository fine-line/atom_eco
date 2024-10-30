from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..database import get_session
from ..models.admin import Admin, AdminPublic, AdminUpdate
from .. import crud
from ..security import hash_password
from .login import Role, authorize, authenticate_user_by_token


router = APIRouter(prefix="/system", tags=["system"])


@router.patch("/admin", response_model=AdminPublic)
@authorize(roles=[Role.ADMIN])
async def update_admin(
        admin: AdminUpdate,
        current_user: str = Depends(authenticate_user_by_token),
        session: Session = Depends(get_session)
        ):
    db_admin = crud.get_db_object_by_field(
        session=session, db_table=Admin, field="id", value=1)
    update_data = admin.model_dump(exclude_unset=True)
    if "password" in update_data:
        hashed_password = hash_password(password=update_data["password"])
        update_data.update({"hashed_password": hashed_password})
    return crud.update_db_object(
        session=session, db_object=db_admin, update_data=update_data)
