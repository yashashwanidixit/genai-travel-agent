"""
Integration test proving the full Stage 2A -> Stage 2B wiring:

HotelSearchQuery -> MockHotelProvider -> Hotel[]
                                              ↓
                                     ConstraintEngine
                                              ↓
                                     Eligible Hotel[]

Uses the REAL MockHotelProvider (no re-implementation of its logic).
No Ollama involved.
"""

import pytest

from app.constraints.hotel import filter_hotels
from app.models.hotel_search_query import HotelSearchQuery
from app.models.intent import ExtractedSlots, IntentCategory, TravelIntent
from app.providers.hotels.mock import MockHotelProvider


def _intent(minimum_hotel_rating=None, max_hotel_price=None) -> TravelIntent:
    return TravelIntent(
        raw_query="test query",
        primary_category=IntentCategory.HOTEL_SEARCH,
        slots=ExtractedSlots(
            destination="Whitefield",
            minimum_hotel_rating=minimum_hotel_rating,
            max_hotel_price=max_hotel_price,
        ),
        missing_slots=[],
    )


def test_real_provider_results_get_filtered_by_constraints():
    """Retrieves real Whitefield mock hotels, then applies a rating +
    price constraint and confirms only qualifying hotels remain."""
    provider = MockHotelProvider()
    query = HotelSearchQuery(location="Whitefield", limit=20)
    retrieved = provider.search(query)

    assert len(retrieved) > 0  # sanity check on the real dataset

    intent = _intent(minimum_hotel_rating=4.5, max_hotel_price=3000)
    eligible = filter_hotels(retrieved, intent)

    # Every survivor must genuinely satisfy both constraints.
    for hotel in eligible:
        assert hotel.user_rating >= 4.5
        assert hotel.price_per_night <= 3000

    # Every removed hotel must have genuinely failed at least one constraint.
    removed = [h for h in retrieved if h not in eligible]
    for hotel in removed:
        assert hotel.user_rating < 4.5 or hotel.price_per_night > 3000


def test_real_provider_results_unfiltered_without_constraints():
    """With no rating/price constraints in the intent, every hotel
    the real provider retrieves for Whitefield remains eligible."""
    provider = MockHotelProvider()
    query = HotelSearchQuery(location="Whitefield", limit=20)
    retrieved = provider.search(query)

    intent = _intent()  # no constraints
    eligible = filter_hotels(retrieved, intent)

    assert eligible == retrieved


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v"]))