"""
Unit tests for the hotel search adapter (TravelIntent -> HotelSearchQuery).
No Ollama, no provider calls - pure deterministic conversion logic.
"""

import pytest

from app.models.intent import ExtractedSlots, IntentCategory, TravelIntent
from app.orchestration.hotel_query_adapter import travel_intent_to_hotel_search_query


def _make_intent(**slot_values) -> TravelIntent:
    return TravelIntent(
        raw_query="test query",
        primary_category=IntentCategory.HOTEL_SEARCH,
        slots=ExtractedSlots(**slot_values),
        missing_slots=[],
    )


def test_basic_destination_and_adults():
    """destination and number_of_adults map through directly."""
    intent = _make_intent(destination="Whitefield", number_of_adults=2)
    query = travel_intent_to_hotel_search_query(intent)

    assert query.location == "Whitefield"
    assert query.number_of_adults == 2


def test_rooms():
    """number_of_rooms maps through directly."""
    intent = _make_intent(destination="Whitefield", number_of_rooms=2)
    query = travel_intent_to_hotel_search_query(intent)
    assert query.number_of_rooms == 2


def test_children_and_ages():
    """number_of_children and children_ages both map through."""
    intent = _make_intent(
        destination="Whitefield",
        number_of_children=2,
        children_ages=[5, 8],
    )
    query = travel_intent_to_hotel_search_query(intent)
    assert query.number_of_children == 2
    assert query.children_ages == [5, 8]


def test_dates():
    """check_in/check_out map to check_in_date/check_out_date."""
    intent = _make_intent(
        destination="Whitefield",
        check_in="2026-09-10",
        check_out="2026-09-12",
    )
    query = travel_intent_to_hotel_search_query(intent)
    assert query.check_in_date == "2026-09-10"
    assert query.check_out_date == "2026-09-12"


def test_missing_destination_and_meeting_location_raises():
    """No destination and no meeting_location must raise ValueError -
    the adapter must not silently fabricate a location."""
    intent = _make_intent()
    with pytest.raises(ValueError):
        travel_intent_to_hotel_search_query(intent)


def test_explicit_rating_is_not_applied_by_adapter():
    """minimum_hotel_rating must NOT cause the adapter to filter or
    otherwise change query construction - that belongs to a future
    ConstraintEngine, not this stage."""
    intent = _make_intent(destination="Whitefield", minimum_hotel_rating=4.5)
    query = travel_intent_to_hotel_search_query(intent)

    # The adapter builds a normal query regardless of the rating value
    # being present - it must not raise, filter, or branch on it.
    assert query.location == "Whitefield"


def test_meeting_location_used_when_destination_missing():
    """meeting_location is an acceptable stand-in for destination."""
    intent = _make_intent(meeting_location="ITPL")
    query = travel_intent_to_hotel_search_query(intent)
    assert query.location == "ITPL"


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v"]))