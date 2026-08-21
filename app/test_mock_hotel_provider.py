"""
Deterministic tests for Stage 2A: HotelSearchQuery -> MockHotelProvider
-> List[Hotel]. No Ollama/LLM calls anywhere in this file.
"""

import pytest
from pydantic import ValidationError

from app.models.hotel import Hotel
from app.models import HotelSearchQuery
from app.providers.hotels.mock import MockHotelProvider


@pytest.fixture
def provider() -> MockHotelProvider:
    return MockHotelProvider()


def test_basic_location_search_whitefield(provider):
    """Searching 'Whitefield' returns a non-empty, valid, matching list."""
    query = HotelSearchQuery(location="Whitefield")
    results = provider.search(query)

    assert isinstance(results, list)
    assert len(results) > 0
    assert len(results) <= query.limit
    for hotel in results:
        assert isinstance(hotel, Hotel)
        assert "whitefield" in hotel.address.lower()


def test_limit_is_respected(provider):
    """A limit of 3 must never return more than 3 results."""
    query = HotelSearchQuery(location="Whitefield", limit=3)
    results = provider.search(query)
    assert len(results) <= 3


def test_empty_location_returns_empty_list(provider):
    """A location with no mock hotels must return [] - no fabrication,
    no fallback to another city."""
    query = HotelSearchQuery(location="SomeLocationWithNoMockHotels")
    results = provider.search(query)
    assert results == []


def test_hotel_schema_validity(provider):
    """Every returned hotel must satisfy its own field constraints."""
    query = HotelSearchQuery(location="Whitefield")
    results = provider.search(query)

    assert len(results) > 0
    for hotel in results:
        assert 1 <= hotel.star_rating <= 5
        assert 0 <= hotel.user_rating <= 5
        assert hotel.price_per_night >= 0
        assert hotel.id
        assert hotel.name


def test_search_is_deterministic(provider):
    """Running the same query twice must produce identical results."""
    query = HotelSearchQuery(location="Whitefield", limit=5)
    result1 = provider.search(query)
    result2 = provider.search(query)
    assert result1 == result2


def test_occupancy_fields_are_accepted(provider):
    """A query with adults/children/rooms is accepted and still
    returns valid candidates - no real availability logic required."""
    query = HotelSearchQuery(
        location="Whitefield",
        number_of_adults=2,
        number_of_children=1,
        number_of_rooms=1,
    )
    results = provider.search(query)
    assert isinstance(results, list)
    for hotel in results:
        assert isinstance(hotel, Hotel)


def test_dates_are_accepted(provider):
    """A query with check-in/check-out dates is accepted - no real
    calendar/availability engine required at this stage."""
    query = HotelSearchQuery(
        location="Whitefield",
        check_in_date="2026-09-01",
        check_out_date="2026-09-03",
    )
    results = provider.search(query)
    assert isinstance(results, list)


def test_limit_zero_is_rejected_by_model(provider):
    """limit must be >= 1 per the HotelSearchQuery contract itself -
    the provider does not silently reinterpret an invalid value."""
    with pytest.raises(ValidationError):
        HotelSearchQuery(location="Whitefield", limit=0)


def test_malformed_hotel_is_rejected_by_pydantic():
    """A hotel with an out-of-range star_rating must be rejected by
    Pydantic, not silently accepted."""
    with pytest.raises(ValidationError):
        Hotel(
            id="bad_hotel",
            name="Invalid Hotel",
            city="Bengaluru",
            address="Nowhere",
            star_rating=9,  # invalid: must be 1-5
            user_rating=4.0,
            price_per_night=1000.0,
        )


def test_stage_boundary_hotel_search_query_to_hotel_list(provider):
    """Demonstrates the exact Stage 2A boundary:
    HotelSearchQuery -> MockHotelProvider.search() -> List[Hotel].
    No Ollama, no IntentAgent involved.
    """
    query = HotelSearchQuery(location="Whitefield", limit=5)
    results = provider.search(query)

    assert isinstance(query, HotelSearchQuery)
    assert isinstance(results, list)
    assert all(isinstance(h, Hotel) for h in results)


def test_other_location_koramangala_is_isolated(provider):
    """A different valid location returns only its own hotels, not
    Whitefield's - confirms matching isn't accidentally global."""
    query = HotelSearchQuery(location="Koramangala")
    results = provider.search(query)

    assert len(results) > 0
    for hotel in results:
        assert "koramangala" in hotel.address.lower()


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v"]))