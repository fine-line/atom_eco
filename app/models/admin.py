from sqlmodel import Field, SQLModel, AutoString
from pydantic import EmailStr


class AdminBase(SQLModel):
    email: EmailStr = Field(sa_type=AutoString, unique=True, index=True)


class Admin(AdminBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str = Field()


class AdminPublic(AdminBase):
    pass
