from sqlmodel import SQLModel

from .storage import Storage, StoragePublic
from .location import Location
from .companywastelink import CompanyWasteLink


# class RouteBase(SQLModel):
#     waste: "Waste"
#     route_history: list["Storage"]
#     distance: int


# class Route(RouteBase):
#     next_location: "Location"
#     total_empty_space: int

#     def __lt__(self, other: "Route"):
#         return self.distance < other.distance

#     def __hash__(self):
#         return hash(self.next_location.id)

#     # def __repr__(self):
#     #     return f"route: {self.route_history}\ndistance: {self.distance}"


# class RoutePublic(RouteBase):
#     waste: "WastePublic"
#     route_history: list["StoragePublic"]


class SpaceCounter(SQLModel):
    company_waste_link: CompanyWasteLink
    total_empty_space: int


class RouteBase(SQLModel):
    route_history: list["Storage"]
    distance: int


class Route(RouteBase):
    next_location: "Location"
    space_counters: list[SpaceCounter] | None = None

    def __lt__(self, other: "Route"):
        return self.distance < other.distance

    def __hash__(self):
        return hash(self.next_location.id)

    def __repr__(self):
        return f"route: {self.route_history}\ndistance: {self.distance}"


class RoutePublic(RouteBase):
    route_history: list["StoragePublic"]
