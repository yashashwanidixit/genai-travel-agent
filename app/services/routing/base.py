"""
Base routing interface.

This module defines the contract that every routing/distance implementation
must follow.

Current implementation:
    HaversineDistanceCalculator

Future implementation:
    GraphHopperRoutingService

The rest of the application should depend on this interface rather than
depending directly on Haversine or GraphHopper.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.hotel import Hotel
from app.models.hotel_context import HotelContext
from app.models.location import ResolvedLocation


class RoutingError(Exception):
    """Base exception for routing-related failures."""

    pass


class RoutingService(ABC):
    """Abstract interface for calculating hotel routing information.

    Implementations receive:
        - an optional resolved reference location
        - a list of hotels

    and return:
        - one HotelContext for each hotel.

    The implementation is responsible for determining how the distance
    is calculated.

    Examples:
        HaversineDistanceCalculator
        GraphHopperRoutingService
    """

    @abstractmethod
    def calculate(
        self,
        reference_location: ResolvedLocation | None,
        hotels: list[Hotel],
    ) -> list[HotelContext]:
        """Calculate routing information for the supplied hotels.

        Args:
            reference_location:
                The resolved meeting/reference location.

                If None, implementations should return HotelContext
                objects with no distance information rather than inventing
                a reference point.

            hotels:
                Hotels for which routing information is required.

        Returns:
            A list of HotelContext objects corresponding to the input hotels.

        Raises:
            RoutingError:
                If routing information cannot be calculated.
        """

        raise NotImplementedError