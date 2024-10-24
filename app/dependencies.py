from sqlmodel import Session
from .database import engine, fake_db_engine


def get_session():
    with Session(engine) as session:
        yield session


def get_fake_db_session():
    with Session(fake_db_engine) as session:
        yield session
