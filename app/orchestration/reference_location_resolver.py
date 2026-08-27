from __future__ import annotations

from typing import Optional

from app.models.intent import TravelIntent
from app.recommendation.user_profile import USER_PROFILE_A
from app.services.location_resolver import LocationResolver


def resolve_distance_threshold(intent: TravelIntent) -> float:
    """Return the distance threshold for the current hotel search.

    Uses the user's explicit hard distance constraint when provided.
    Otherwise falls back to the user's profile preference.
    """
    if intent.slots.max_hotel_distance_km is not None:
        return intent.slots.max_hotel_distance_km

    return USER_PROFILE_A.preferred_distance


def resolve_reference_location(
    intent: TravelIntent,
    location_resolver: LocationResolver,
) -> Optional[object]:
    """Resolve the location from which hotel distances should be calculated.

    Priority:
        1. Meeting location
        2. Origin
        3. No reference location
    """
    if intent.slots.meeting_location:
        return location_resolver.resolve(
            intent.slots.meeting_location
        )

    if intent.slots.origin:
        return location_resolver.resolve(
            intent.slots.origin
        )

    return None