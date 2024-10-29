from typing import Annotated
from enum import StrEnum
from functools import wraps

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session

from ..database import get_session
from ..models.company import Company
from ..models.storage import Storage
from ..models.admin import Admin
from .. import crud
from ..security import (
    Token, valid_password, create_access_token, verify_access_token)
from ..config import Settings, get_settings


router = APIRouter(prefix="/system")


class Role(StrEnum):
    ADMIN = Admin.__name__
    COMPANY = Company.__name__
    STORAGE = Storage.__name__


def authenticate_user_by_password(
        session: Session, username: str, password: str):
    db_tables = [Company, Storage, Admin]
    for db_table in db_tables:
        db_object = crud.get_db_object_by_field(
            session=session, db_table=db_table, field="email", value=username)
        if db_object and valid_password(
                password=password, hashed_password=db_object.hashed_password):
            break
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
            )
    return db_object


def authenticate_user_by_token(
        access_token: Annotated[str, Depends(
            OAuth2PasswordBearer(tokenUrl="api/v1/system/token"))],
        settings: Settings = Depends(get_settings)
        ):
    subject = verify_access_token(access_token=access_token, settings=settings)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
            )
    return subject


def authorize(roles: list):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get("current_user")
            user_role, _ = user.split(":")
            if user_role not in roles:
                raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized",
                        headers={"WWW-Authenticate": "Bearer"}
                        )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


@router.post("/token", response_model=Token,
             tags=["companies", "storages", "system"])
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: Session = Depends(get_session),
        settings: Settings = Depends(get_settings)
        ):
    username, password = form_data.username, form_data.password
    db_object = authenticate_user_by_password(
        session=session, username=username, password=password)
    role = db_object.__class__.__name__
    id = str(db_object.id)
    subject = ":".join([role, id])
    access_token = create_access_token(subject=subject, settings=settings)
    return access_token


@router.get("/self-id", tags=["companies", "storages"], response_model=int)
@authorize(roles=[Role.COMPANY, Role.STORAGE])
async def get_self_id(
        current_user: str = Depends(authenticate_user_by_token)):
    _, user_id = current_user.split(":")
    return user_id
