"""Adapter: TravelIntent (what the user said) -> HotelSearchQuery
(what a HotelProvider needs).

This conversion intentionally lives outside IntentAgent and outside
MockHotelProvider - IntentAgent must never know about hotel search
mechanics, and providers must never see raw TravelIntent objects.


"""

from __future__ import annotations

from app.models import HotelSearchQuery
from app.models.intent import TravelIntent


def travel_intent_to_hotel_search_query(
    intent: TravelIntent, limit: int = 10
) -> HotelSearchQuery:
    """Builds a HotelSearchQuery from a normalized, requirement-checked
    TravelIntent. Callers should only invoke this once the intent is
    confirmed READY FOR HOTEL SEARCH (missing_slots == []) - this
    function does not itself validate readiness.
    """
    slots = intent.slots

    # destination is the primary required field for hotel search; a
    # meeting_location is an acceptable stand-in per the existing
    # requirement-checker logic, so the same fallback applies here.
    location = slots.destination or slots.meeting_location
    if not location:
        raise ValueError(
            "Cannot build a HotelSearchQuery without a destination or "
            "meeting_location. Caller should verify the intent is "
            "READY FOR HOTEL SEARCH before calling this adapter."
        )

    return HotelSearchQuery(
        location=location,
        check_in_date=slots.check_in,
        check_out_date=slots.check_out,
        number_of_rooms=slots.number_of_rooms or 1,
        number_of_adults=slots.number_of_adults or 1,
        number_of_children=slots.number_of_children or 0,
        children_ages=slots.children_ages or [],

        min_stars=None,
        max_budget_per_night=None,
        required_amenities=[],
        limit=limit,
    )