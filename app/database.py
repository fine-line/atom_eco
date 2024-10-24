from sqlmodel import SQLModel, create_engine


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# Fake db connection

fake_locations_db_file = "fake_locations_database.db"
fake_db_url = f"sqlite:///{fake_locations_db_file}"

# connect_args = {"check_same_thread": False}
fake_db_engine = create_engine(
    fake_db_url, echo=True, connect_args=connect_args)
