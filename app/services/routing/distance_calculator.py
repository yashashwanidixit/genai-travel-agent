"""
Haversine-based routing implementation.

This is currently a deterministic local implementation used for development
and testing.

IMPORTANT:
- It does NOT use GraphHopper.
- It does NOT calculate road distance.
- It calculates great-circle/geographic distance.
- It does NOT modify Hotel objects.
- It returns new HotelContext objects.

A future GraphHopper implementation will implement the same RoutingService
interface and can replace this implementation without changing downstream
code.
"""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from app.models.hotel import Hotel
from app.models.hotel_context import HotelContext
from app.models.location import ResolvedLocation
from app.services.routing.base import RoutingError, RoutingService


class DistanceCalculationError(RoutingError):
    """Raised when Haversine distance cannot be calculated."""

    pass


class HaversineDistanceCalculator(RoutingService):
    """Calculate geographic distance using the Haversine formula.

    This implementation satisfies the RoutingService contract.

    Input:
        ResolvedLocation
        list[Hotel]

    Output:
        list[HotelContext]

    The original Hotel objects are never modified.
    """

    EARTH_RADIUS_KM = 6371.0

    def calculate(
        self,
        reference_location: ResolvedLocation | None,
        hotels: list[Hotel],
    ) -> list[HotelContext]:
        """Calculate distance from the reference location to every hotel.

        If reference_location is None, the hotels are still wrapped in
        HotelContext objects, but distance_km is None.

        This is important because a user may request:

            "I want a hotel in Whitefield."

        without specifying a meeting/reference location.

        In that case we must NOT use the destination as the reference point.
        """

        contexts: list[HotelContext] = []

        for hotel in hotels:
            distance_km = self._calculate_hotel_distance(
                reference_location=reference_location,
                hotel=hotel,
            )

            contexts.append(
                HotelContext(
                    hotel=hotel,
                    distance_km=distance_km,
                )
            )

        return contexts

    def _calculate_hotel_distance(
        self,
        reference_location: ResolvedLocation | None,
        hotel: Hotel,
    ) -> float | None:
        """Calculate one hotel's geographic distance."""

        # No reference location means there is no meaningful distance.
        if reference_location is None:
            return None

        # Both hotel coordinates are required.
        if hotel.latitude is None or hotel.longitude is None:
            raise DistanceCalculationError(
                f"Cannot calculate distance for hotel '{hotel.id}': "
                "hotel latitude/longitude is missing."
            )

        # Validate reference coordinates.
        self._validate_coordinates(
            latitude=reference_location.latitude,
            longitude=reference_location.longitude,
            location_description=(
                f"reference location '{reference_location.name}'"
            ),
        )

        # Validate hotel coordinates.
        self._validate_coordinates(
            latitude=hotel.latitude,
            longitude=hotel.longitude,
            location_description=f"hotel '{hotel.id}'",
        )

        return self._haversine_distance(
            reference_latitude=reference_location.latitude,
            reference_longitude=reference_location.longitude,
            hotel_latitude=hotel.latitude,
            hotel_longitude=hotel.longitude,
        )

    @classmethod
    def _haversine_distance(
        cls,
        reference_latitude: float,
        reference_longitude: float,
        hotel_latitude: float,
        hotel_longitude: float,
    ) -> float:
        """Return great-circle distance between two coordinates in km."""

        lat1 = radians(reference_latitude)
        lat2 = radians(hotel_latitude)

        delta_lat = radians(
            hotel_latitude - reference_latitude
        )
        delta_lon = radians(
            hotel_longitude - reference_longitude
        )

        a = (
            sin(delta_lat / 2) ** 2
            + cos(lat1)
            * cos(lat2)
            * sin(delta_lon / 2) ** 2
        )

        c = 2 * asin(sqrt(a))

        return cls.EARTH_RADIUS_KM * c

    @staticmethod
    def _validate_coordinates(
        latitude: float,
        longitude: float,
        location_description: str,
    ) -> None:
        """Validate latitude and longitude."""

        if not -90 <= latitude <= 90:
            raise DistanceCalculationError(
                f"Invalid latitude for "
                f"{location_description}: {latitude}"
            )

        if not -180 <= longitude <= 180:
            raise DistanceCalculationError(
                f"Invalid longitude for "
                f"{location_description}: {longitude}"
            )