from sqlmodel import Session

from ..models.company import Company
from ..models.location import Location
from ..models.companywastelink import CompanyWasteLink
from ..models.storagewastelink import StorageWasteLink
from ..models.route import Route, SpaceCounter
from .. import crud


def find_optimal_route(
        company: Company, company_waste_links: list[CompanyWasteLink],
        partial_unload: bool
        ) -> Route | None:
    """ Find optimal (with distance minimized) route, for waste unloading
    allows for partial unloading along the way
    """
    routes_to_explore = set()
    visited_locations = []
    company_location = company.location_link.location

    space_counters = []
    for company_waste_link in company_waste_links:
        space_counter = SpaceCounter(
            company_waste_link=company_waste_link, total_empty_space=0)
        space_counters.append(space_counter)

    route = Route(
        next_location=company_location, route_history=[], distance=0,
        space_counters=space_counters
        )
    routes = find_routes(
        route=route, visited_locations=visited_locations,
        partial_unload=partial_unload
        )
    if not routes:
        return None
    routes_to_explore.update(routes)

    while routes_to_explore:
        shortest_route = min(routes_to_explore)
        for space_counter in shortest_route.space_counters:
            total_empty_space = space_counter.total_empty_space
            waste_amount = space_counter.company_waste_link.amount
            if total_empty_space < waste_amount:
                break
        else:
            return shortest_route

        routes_to_explore.discard(shortest_route)
        location = shortest_route.next_location
        visited_locations.append(location)

        new_routes = find_routes(
            route=shortest_route, visited_locations=visited_locations,
            partial_unload=partial_unload
            )
        # Filtering out routes by distance to the same location
        for new_route in list(new_routes):
            for route_to_explore in list(routes_to_explore):
                if new_route.next_location == route_to_explore.next_location:
                    if route_to_explore > new_route:
                        routes_to_explore.discard(route_to_explore)
                    elif new_route > route_to_explore:
                        new_routes.discard(new_route)
        routes_to_explore.update(new_routes)
    return None


def find_routes(
        route: Route, visited_locations: list[Location], partial_unload: bool
        ) -> set[Route] | None:
    """ Find new set of routes, that leads from "next_location" """
    location = route.next_location
    routes = set()

    roads = location.roads_from
    for road in roads:
        next_location = road.location_to
        is_occupied_by_storage = next_location.storage_link is not None
        # Travel only trough storages
        if is_occupied_by_storage and next_location not in visited_locations:
            storage = next_location.storage_link.storage
            distance = route.distance + road.distance
            route_history = route.route_history.copy()
            route_history.append(storage)
            # Update space counters
            new_space_counters = []
            for space_counter in route.space_counters:
                company_waste_link = space_counter.company_waste_link
                total_empty_space = space_counter.total_empty_space
                company_waste_type = company_waste_link.waste
                # Check if storage can recieve waste type and calculate
                # available space
                empty_storage_space = 0
                for storage_waste_link in storage.waste_links:
                    storage_waste_type = storage_waste_link.waste
                    if company_waste_type == storage_waste_type:
                        empty_storage_space = (storage_waste_link.max_amount
                                               - storage_waste_link.amount)
                        break
                # Increment counter only for partial unloading
                if partial_unload:
                    total_empty_space += empty_storage_space
                else:
                    total_empty_space = empty_storage_space
                new_space_counter = SpaceCounter(
                    company_waste_link=space_counter.company_waste_link,
                    total_empty_space=total_empty_space
                    )
                new_space_counters.append(new_space_counter)
            new_route = Route(
                next_location=next_location, route_history=route_history,
                distance=distance, space_counters=new_space_counters
                )
            routes.add(new_route)
    return routes


def unload_company(session: Session, route: Route, company: Company):
    storage = route.route_history[-1]
    for company_waste_link in company.waste_links:
        waste = company_waste_link.waste
        waste_amount = company_waste_link.amount
        storage_waste_link = crud.get_db_link(
            session=session, db_table=StorageWasteLink,
            id_field_1="storage_id", value_1=storage.id,
            id_field_2="waste_id", value_2=waste.id
            )
        crud.update_db_object(
            session=session, db_object=storage_waste_link,
            update_data={"amount": (storage_waste_link.amount + waste_amount)}
            )
        crud.update_db_object(
            session=session, db_object=company_waste_link,
            update_data={"amount": 0}
            )


def partially_unload_company(
        session: Session, route: Route, company: Company,
        company_waste_link: CompanyWasteLink
        ):
    waste = company_waste_link.waste
    waste_amount = company_waste_link.amount
    for storage in route.route_history:
        storage_waste_link = crud.get_db_link(
            session=session, db_table=StorageWasteLink,
            id_field_1="storage_id", value_1=storage.id,
            id_field_2="waste_id", value_2=waste.id
            )
        empty_storage_space = (storage_waste_link.max_amount
                               - storage_waste_link.amount)
        if waste_amount > empty_storage_space:
            update_data = {"amount": (storage_waste_link.max_amount)}
        else:
            update_data = {"amount": (storage_waste_link.amount+waste_amount)}
        crud.update_db_object(
            session=session, db_object=storage_waste_link,
            update_data=update_data
            )
        waste_amount -= empty_storage_space
    crud.update_db_object(
        session=session, db_object=company_waste_link,
        update_data={"amount": 0}
        )
