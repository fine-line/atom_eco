from sqlmodel import SQLModel, create_engine, Session, select
from .models import Admin
from .security import hash_password

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    create_admin()


# ! move to .env
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "adminpassword"


def create_admin():
    with Session(engine) as session:
        db_admin = session.exec(select(Admin)).first()
        if not db_admin:
            hashed_password = hash_password(ADMIN_PASSWORD)
            admin = Admin(email=ADMIN_EMAIL, hashed_password=hashed_password)
            session.add(admin)
            session.commit()


# Fake db connection


fake_locations_db_file = "fake_locations_database.db"
fake_db_url = f"sqlite:///{fake_locations_db_file}"

# connect_args = {"check_same_thread": False}
fake_db_engine = create_engine(
    fake_db_url, echo=False, connect_args=connect_args)
