"""
Distance calculation between a resolved reference location and hotels.

Current implementation:
    Haversine / great-circle distance.

This is intentionally a temporary deterministic implementation.

IMPORTANT:
- It does NOT use GraphHopper yet.
- It does NOT modify Hotel objects.
- It returns new HotelContext objects.
- It uses the latitude/longitude already available on Hotel.
- It calculates straight-line geographic distance, NOT road distance.

A future GraphHopper implementation can replace this service while keeping
the HotelContext contract unchanged.
"""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from app.models.hotel import Hotel
from app.models.hotel_context import HotelContext
from app.models.location import ResolvedLocation


class DistanceCalculationError(Exception):
    """Raised when distance cannot be calculated for a hotel."""

    pass


class DistanceCalculator:
    """Calculate search-context distance for hotels.

    Current implementation uses Haversine distance.

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

        Args:
            reference_location:
                The user's resolved meeting/reference location.

                If None, no distance can be calculated. In that case,
                HotelContext objects are returned with distance_km=None.

            hotels:
                Hotels for which contextual distance should be calculated.

        Returns:
            A new list of HotelContext objects.

        Raises:
            DistanceCalculationError:
                If a hotel has only one coordinate or has invalid
                coordinates.
        """

        contexts: list[HotelContext] = []

        for hotel in hotels:
            distance_km = self._calculate_hotel_distance(
                reference_location,
                hotel,
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
        """Calculate one hotel's distance from the reference location."""

        # No reference location means there is no meaningful distance.
        if reference_location is None:
            return None

        # Hotel coordinates are required to calculate distance.
        #
        # We deliberately do not guess or geocode them here.
        if hotel.latitude is None or hotel.longitude is None:
            raise DistanceCalculationError(
                f"Cannot calculate distance for hotel '{hotel.id}': "
                "hotel latitude/longitude is missing."
            )

        self._validate_coordinates(
            reference_location.latitude,
            reference_location.longitude,
            f"reference location '{reference_location.name}'",
        )

        self._validate_coordinates(
            hotel.latitude,
            hotel.longitude,
            f"hotel '{hotel.id}'",
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

        delta_lat = radians(hotel_latitude - reference_latitude)
        delta_lon = radians(hotel_longitude - reference_longitude)

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
        """Validate latitude/longitude before performing calculations."""

        if not -90 <= latitude <= 90:
            raise DistanceCalculationError(
                f"Invalid latitude for {location_description}: {latitude}"
            )

        if not -180 <= longitude <= 180:
            raise DistanceCalculationError(
                f"Invalid longitude for {location_description}: {longitude}"
            )