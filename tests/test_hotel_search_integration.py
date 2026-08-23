"""
Integration tests: TravelIntent -> adapter -> HotelSearchQuery ->
MockHotelProvider -> Hotel[].

No Ollama here. This tests the wiring between already-tested pieces,
not the individual pieces themselves.
"""

import pytest

from app.models.hotel import Hotel
from app.models.intent import ExtractedSlots, IntentCategory, TravelIntent
from app.orchestration.hotel_search_flow import maybe_search_hotels
from app.providers.hotels.mock import MockHotelProvider


def _make_intent(
    category: IntentCategory, missing_slots: list[str] | None = None, **slot_values
) -> TravelIntent:
    return TravelIntent(
        raw_query="test query",
        primary_category=category,
        slots=ExtractedSlots(**slot_values),
        missing_slots=missing_slots or [],
    )


def test_ready_hotel_intent_returns_hotels():
    """A ready hotel_search intent flows all the way to Hotel[]."""
    intent = _make_intent(
        IntentCategory.HOTEL_SEARCH,
        destination="Whitefield",
        number_of_adults=2,
    )
    hotels = maybe_search_hotels(intent)

    assert hotels is not None
    assert isinstance(hotels, list)
    assert len(hotels) > 0
    for hotel in hotels:
        assert isinstance(hotel, Hotel)


def test_incomplete_hotel_intent_does_not_search():
    """A hotel_search intent with missing_slots must NOT reach the
    provider - the gate must block it, not just the CLI layer."""
    intent = _make_intent(
        IntentCategory.HOTEL_SEARCH,
        missing_slots=["destination"],
    )
    result = maybe_search_hotels(intent)
    assert result is None


def test_ride_intent_never_triggers_hotel_search():
    """A ride_search intent, even a fully ready one, must never call
    the hotel provider."""
    intent = _make_intent(
        IntentCategory.RIDE_SEARCH,
        origin="Bangalore Airport",
        destination="Whitefield",
    )
    result = maybe_search_hotels(intent)
    assert result is None


def test_explicit_provider_override_is_used():
    """Callers can supply a specific HotelProvider (e.g. a test
    double) instead of relying on the module-level default."""
    intent = _make_intent(
        IntentCategory.HOTEL_SEARCH,
        destination="Whitefield",
    )
    custom_provider = MockHotelProvider()
    hotels = maybe_search_hotels(intent, provider=custom_provider)

    assert hotels is not None
    assert len(hotels) > 0


def test_unknown_location_returns_empty_list_not_none():
    """A ready intent for a location with no mock hotels returns []
    (the search DID run), which is different from None (the search
    was skipped entirely)."""
    intent = _make_intent(
        IntentCategory.HOTEL_SEARCH,
        destination="SomeLocationWithNoMockHotels",
    )
    result = maybe_search_hotels(intent)
    assert result == []


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v"]))