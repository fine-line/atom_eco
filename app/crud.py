from sqlmodel import Session, select

from .models import (
    Company, Storage, Waste, Location, Road,
    CompanyLocationLink, CompanyWasteLink,
    StorageLocationLink, StorageWasteLink)
from .database import engine


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


def create_waste(session: Session, waste: Waste):
    session.add(waste)
    session.commit()
    session.refresh(waste)
    return waste


def get_wastes(session: Session, skip: int, limit: int = 10):
    wastes = session.exec(select(Waste).offset(skip).limit(limit)).all()
    return wastes


def get_waste_by_id(session: Session, waste_id: int):
    waste = session.exec(select(Waste).where(Waste.id == waste_id)).first()
    return waste


def get_waste_by_name(session: Session, waste_name: str):
    waste = session.exec(select(Waste).where(Waste.name == waste_name)).first()
    return waste


def update_waste(session: Session, waste: Waste, waste_data: dict):
    waste.sqlmodel_update(waste_data)
    session.add(waste)
    session.commit()
    session.refresh(waste)
    return waste


def delete_waste(session: Session, waste: Waste):
    session.delete(waste)
    session.commit()


"""
#################### Storage CRUDs ####################
"""


def create_storage(session: Session, storage: Storage):
    session.add(storage)
    session.commit()
    session.refresh(storage)
    return storage


def get_storages(session: Session, skip: int, limit: int = 10):
    storages = session.exec(select(Storage).offset(skip).limit(limit)).all()
    return storages


def get_storage_by_id(session: Session, storage_id: int):
    storage = session.exec(
        select(Storage).where(Storage.id == storage_id)).first()
    return storage


def get_storage_by_email(session: Session, storage_email: str):
    storage = session.exec(
        select(Storage).where(Storage.email == storage_email)).first()
    return storage


def update_storage(session: Session, storage: Storage, storage_data: dict):
    storage.sqlmodel_update(storage_data)
    session.add(storage)
    session.commit()
    session.refresh(storage)
    return storage


def delete_storage(session: Session, storage: Storage):
    session.delete(storage)
    session.commit()


"""
#################### Storage Waste Link CRUDs ####################
"""


def create_storage_waste_link(session: Session, waste_link: StorageWasteLink):
    session.add(waste_link)
    session.commit()
    session.refresh(waste_link)
    return waste_link


def get_storage_waste_link(session: Session, storage_id: int, waste_id: int):
    db_waste_link = session.exec(
        select(StorageWasteLink)
        .where(StorageWasteLink.storage_id == storage_id)
        .where(StorageWasteLink.waste_id == waste_id)).first()
    return db_waste_link


def update_storage_waste_link(
        session: Session, storage_waste_link: StorageWasteLink,
        waste_link_data: dict):
    storage_waste_link.sqlmodel_update(waste_link_data)
    if storage_waste_link.amount > storage_waste_link.max_amount:
        storage_waste_link.amount = storage_waste_link.max_amount
    session.add(storage_waste_link)
    session.commit()
    session.refresh(storage_waste_link)
    return storage_waste_link


def delete_storage_waste_link(
        session: Session, storage_waste_link: StorageWasteLink):
    session.delete(storage_waste_link)
    session.commit()


# def create_storage_location_link(storage_name: str, location_name: str):
#     with Session(engine) as session:
#         storage = session.exec(
#             select(Storage).where(Storage.name == storage_name)).one()
#         location = session.exec(
#             select(Location).where(Location.name == location_name)).one()
#         storage_location_link = StorageLocationLink(
#             storage=storage, location=location)
#         session.add(storage_location_link)
#         session.commit()


"""
#################### Company CRUDs ####################
"""


def create_company(session: Session, company: Company):
    session.add(company)
    session.commit()
    session.refresh(company)
    return company


def get_companies(session: Session, skip: int, limit: int = 10):
    companies = session.exec(select(Company).offset(skip).limit(limit)).all()
    return companies


def get_company_by_id(session: Session, company_id: int):
    company = session.exec(
        select(Company).where(Company.id == company_id)).first()
    return company


def get_company_by_email(session: Session, company_email: str):
    company = session.exec(
        select(Company).where(Company.email == company_email)).first()
    return company


def update_company(session: Session, company: Company, company_data: dict):
    company.sqlmodel_update(company_data)
    session.add(company)
    session.commit()
    session.refresh(company)
    return company


def delete_company(session: Session, company: Company):
    session.delete(company)
    session.commit()


"""
#################### Company Waste Link CRUDs ####################
"""


def create_company_waste_link(session: Session, waste_link: CompanyWasteLink):
    session.add(waste_link)
    session.commit()
    session.refresh(waste_link)
    return waste_link


def get_company_waste_link(session: Session, company_id: int, waste_id: int):
    db_waste_link = session.exec(
        select(CompanyWasteLink)
        .where(CompanyWasteLink.company_id == company_id)
        .where(CompanyWasteLink.waste_id == waste_id)).first()
    return db_waste_link


def update_company_waste_link(
        session: Session, company_waste_link: CompanyWasteLink,
        waste_link_data: dict):
    company_waste_link.sqlmodel_update(waste_link_data)
    if company_waste_link.amount > company_waste_link.max_amount:
        company_waste_link.amount = company_waste_link.max_amount
    session.add(company_waste_link)
    session.commit()
    session.refresh(company_waste_link)
    return company_waste_link


def delete_company_waste_link(
        session: Session, company_waste_link: CompanyWasteLink):
    session.delete(company_waste_link)
    session.commit()


# def create_company_location_link(company_name: str, location_name: str):
#     with Session(engine) as session:
#         company = session.exec(
#             select(Company).where(Company.name == company_name)).one()
#         location = session.exec(
#             select(Location).where(Location.name == location_name)).one()
#         company_location_link = CompanyLocationLink(
#             company=company, location=location)
#         session.add(company_location_link)
#         session.commit()
