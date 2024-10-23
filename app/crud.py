from sqlmodel import Session, SQLModel, select


"""
#################### General CRUDs ####################
"""


def create_db_object(session: Session, db_object: SQLModel):
    session.add(db_object)
    session.commit()
    session.refresh(db_object)
    return db_object


def get_db_objects(
        session: Session, db_class: type[SQLModel],
        skip: int, limit: int = 10
        ):
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


"""
#################### Location CRUDs ####################
"""
# def create_location(name: str):
#     with Session(engine) as session:
#         location = Location(name=name)
#         session.add(location)
#         session.commit()


# def update_location(name: str, new_name: str):
#     with Session(engine) as session:
#         location = session.exec(
#             select(Location).where(Location.name == name)).one()
#         location.name = new_name
#         session.add(location)
#         session.commit()


# def delete_location(name: str):
#     with Session(engine) as session:
#         location = session.exec(
#             select(Location).where(Location.name == name)).one()
#         session.delete(location)
#         session.commit()


"""
#################### Road CRUDs ####################
"""
# def create_one_way_road(from_: str, to: str, distance: int):
#     with Session(engine) as session:
#         location_from = session.exec(
#             select(Location).where(Location.name == from_)).one()
#         location_to = session.exec(
#             select(Location).where(Location.name == to)).one()
#         road = Road(location_from=location_from, location_to=location_to,
#                     distance=distance)
#         session.add(road)
#         session.commit()


# def create_two_way_road(from_: str, to: str, distance: int):
#     with Session(engine) as session:
#         location_from = session.exec(
#             select(Location).where(Location.name == from_)).one()
#         location_to = session.exec(
#             select(Location).where(Location.name == to)).one()
#         road1 = Road(location_from=location_from, location_to=location_to,
#                      distance=distance)
#         road2 = Road(location_from=location_to, location_to=location_from,
#                      distance=distance)
#         session.add(road1)
#         session.add(road2)
#         session.commit()


# def update_road(from_: str, to: str, new_distance: int):
#     with Session(engine) as session:
#         location_from = session.exec(
#             select(Location).where(Location.name == from_)).one()
#         location_to = session.exec(
#             select(Location).where(Location.name == to)).one()
#         roads = session.exec(select(Road).where(
#             Road.location_from_id.in_([location_from.id, location_to.id]),
#             Road.location_to_id.in_([location_from.id, location_to.id]))).all()
#         for road in roads:
#             road.distance = new_distance
#             session.add(road)
#         session.commit()


# def delete_road(from_: str, to: str):
#     with Session(engine) as session:
#         location_from = session.exec(
#             select(Location).where(Location.name == from_)).one()
#         location_to = session.exec(
#             select(Location).where(Location.name == to)).one()
#         roads = session.exec(select(Road).where(
#             Road.location_from_id.in_([location_from.id, location_to.id]),
#             Road.location_to_id.in_([location_from.id, location_to.id]))).all()
#         for road in roads:
#             session.delete(road)
#         session.commit()


"""
#################### Waste CRUDs ####################
"""


"""
#################### Storage CRUDs ####################
"""


"""
#################### Storage Waste Link CRUDs ####################
"""


"""
#################### Company CRUDs ####################
"""


"""
#################### Company Waste Link CRUDs ####################
"""
