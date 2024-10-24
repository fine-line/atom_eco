from sqlmodel import Session, SQLModel, select


def create_db_object(session: Session, db_object: SQLModel):
    session.add(db_object)
    session.commit()
    session.refresh(db_object)
    return db_object


def get_db_objects(
        session: Session, db_class: type[SQLModel], skip: int, limit: int):
    db_objects = session.exec(select(db_class).offset(skip).limit(limit)).all()
    return db_objects


def get_db_object_by_field(
        session: Session, db_table: type[SQLModel], field: str, value):
    db_object = session.exec(
        select(db_table).where(getattr(db_table, field) == value)).first()
    return db_object


def update_db_object(session: Session, db_object: SQLModel, update_data: dict):
    db_object.sqlmodel_update(update_data)
    session.add(db_object)
    session.commit()
    session.refresh(db_object)
    return db_object


def delete_db_object(session: Session, db_object: SQLModel):
    session.delete(db_object)
    session.commit()


def get_db_link(
        session: Session, db_table: type[SQLModel],
        id_field_1: str, value_1: int, id_field_2: str, value_2: int
        ):
    db_link = session.exec(
        select(db_table)
        .where(getattr(db_table, id_field_1) == value_1)
        .where(getattr(db_table, id_field_2) == value_2)
        ).first()
    return db_link
