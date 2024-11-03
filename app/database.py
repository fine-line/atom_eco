from sqlmodel import SQLModel, create_engine, Session, select
from .models.admin import Admin
from .security import hash_password
from .config import get_settings


settings = get_settings()
user = settings.db_user
password = settings.db_password
service = settings.db_service
db_url = f"postgresql+psycopg2://{user}:{password}@{service}:5432"
connect_args = {"check_same_thread": False}
engine = create_engine(db_url)


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    create_admin(engine)


def create_admin(engine):
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

settings = get_settings()
user = settings.fake_db_user
password = settings.fake_db_password
service = settings.fake_db_service
fake_db_url = f"postgresql+psycopg2://{user}:{password}@{service}:5432"
connect_args = {"check_same_thread": False}
fake_db_engine = create_engine(fake_db_url)


def get_fake_db_session():
    with Session(fake_db_engine) as session:
        yield session
