from ..models.company import Company
from ..models.location import Location
from ..models.companywastelink import CompanyWasteLink
from ..models.route import Route


def find_optimal_route(
        company: Company, company_waste_link: CompanyWasteLink
        ) -> Route | None:
    routes_to_explore = set()
    visited_locations = []

    company_location = company.location_link.location
    waste_amount_to_unload = company_waste_link.amount

    route = Route(
        waste=company_waste_link.waste,
        next_location=company_location, route_history=[],
        distance=0, total_empty_space=0
        )
    routes = find_routes(
        route=route, visited_locations=visited_locations,
        )
    if not routes:
        return None
    routes_to_explore.update(routes)

    while routes_to_explore:
        shortest_route = min(routes_to_explore)
        if shortest_route.total_empty_space > waste_amount_to_unload:
            return shortest_route

        routes_to_explore.discard(shortest_route)
        location = shortest_route.next_location
        visited_locations.append(location)

        new_routes = find_routes(
            route=shortest_route, visited_locations=visited_locations,
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
        route: Route, visited_locations: list[Location]) -> set[Route] | None:
    location = route.next_location
    waste = route.waste
    routes = set()

    roads = location.roads_from
    for road in roads:
        next_location = road.location_to
        is_occupied_by_storage = next_location.storage_link is not None

        if is_occupied_by_storage and next_location not in visited_locations:
            storage = next_location.storage_link.storage
            distance = route.distance + road.distance
            route_history = route.route_history.copy()
            route_history.append(storage)

            empty_storage_space = 0
            for waste_link in storage.waste_links:
                if waste_link.waste == waste:
                    empty_storage_space = (waste_link.max_amount
                                           - waste_link.amount)
            total_empty_space = route.total_empty_space + empty_storage_space

            new_route = Route(
                waste=waste, next_location=next_location,
                route_history=route_history, distance=distance,
                total_empty_space=total_empty_space
                )
            routes.add(new_route)
    return routes
