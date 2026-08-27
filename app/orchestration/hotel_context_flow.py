from __future__ import annotations

from app.models.hotel_context import HotelContext
from app.models.intent import TravelIntent
from app.services.location_resolver import LocationResolver
from app.services.routing.base import RoutingService
from app.services.routing.distance_calculator import (
    HaversineDistanceCalculator,
)
from app.models.hotel import Hotel
from app.orchestration.reference_location_resolver import resolve_reference_location


def build_hotel_contexts(
    intent: TravelIntent,
    hotels: list[Hotel],
    location_resolver: LocationResolver,
    routing_service: RoutingService,
) -> list[HotelContext]:
    """Enrich retrieved hotels with search-specific routing context.

    Flow:

        TravelIntent
            ↓
        meeting_location
            ↓
        LocationResolver
            ↓
        ResolvedLocation | None
            ↓
        RoutingService + Hotel[]
            ↓
        HotelContext[]

    This function does NOT:
    - perform hotel search
    - modify TravelIntent
    - modify Hotel objects
    - filter hotels
    - rank hotels
    - recommend hotels

    Those responsibilities belong to other stages.
    """
    reference_location = resolve_reference_location(intent, location_resolver)

    

    return routing_service.calculate(
        reference_location=reference_location,
        hotels=hotels,
    )