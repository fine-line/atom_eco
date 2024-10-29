from sqlmodel import SQLModel, create_engine, Session, select
from .models.admin import Admin
from .security import hash_password
from .config import get_settings


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    create_admin()


# ! move to .env
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "adminpassword"


def create_admin():
    with Session(engine) as session:
        settings = get_settings()
        db_admin = session.exec(select(Admin)).first()
        if not db_admin:
            hashed_password = hash_password(settings.admin_password)
            email = settings.admin_email
            admin = Admin(email=email, hashed_password=hashed_password)
            session.add(admin)
            session.commit()


# Fake db connection


fake_locations_db_file = "fake_locations_database.db"
fake_db_url = f"sqlite:///{fake_locations_db_file}"

# connect_args = {"check_same_thread": False}
fake_db_engine = create_engine(
    fake_db_url, echo=False, connect_args=connect_args)


def get_fake_db_session():
    with Session(fake_db_engine) as session:
        yield session
