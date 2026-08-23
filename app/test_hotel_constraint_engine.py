"""
Deterministic unit tests for the Stage 2B hotel ConstraintEngine.
No Ollama, no MockHotelProvider - Hotel objects are constructed
directly so these tests are fast and fully isolated.
"""

import pytest

from app.constraints.hotel import filter_hotels
from app.models.hotel import Hotel
from app.models.intent import ExtractedSlots, IntentCategory, TravelIntent


def _hotel(id_: str, rating: float, price: float) -> Hotel:
    return Hotel(
        id=id_,
        name=f"Hotel {id_}",
        city="Bengaluru",
        address="Whitefield",
        star_rating=3,
        user_rating=rating,
        price_per_night=price,
    )


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


def test_no_constraints_keeps_all_hotels():
    """With both constraints None, every retrieved hotel remains eligible."""
    hotels = [_hotel("A", 4.8, 5000), _hotel("B", 3.0, 500), _hotel("C", 2.1, 100)]
    intent = _intent()
    result = filter_hotels(hotels, intent)
    assert result == hotels


def test_minimum_rating_filters_out_lower_rated_hotels():
    """Only hotels at/above the rating floor survive."""
    a = _hotel("A", 4.8, 1000)
    b = _hotel("B", 4.5, 1000)
    c = _hotel("C", 4.2, 1000)
    intent = _intent(minimum_hotel_rating=4.5)

    result = filter_hotels([a, b, c], intent)
    assert result == [a, b]


def test_maximum_price_filters_out_more_expensive_hotels():
    """Only hotels at/under the price ceiling survive."""
    a = _hotel("A", 4.0, 2000)
    b = _hotel("B", 4.0, 3000)
    c = _hotel("C", 4.0, 3500)
    intent = _intent(max_hotel_price=3000)

    result = filter_hotels([a, b, c], intent)
    assert result == [a, b]


def test_both_constraints_must_pass_together():
    """A hotel must satisfy BOTH active constraints, not just one."""
    a = _hotel("A", 4.7, 2800)  # passes both
    b = _hotel("B", 4.2, 2000)  # fails rating
    c = _hotel("C", 4.8, 5000)  # fails price
    d = _hotel("D", 3.9, 1000)  # fails rating

    intent = _intent(minimum_hotel_rating=4.5, max_hotel_price=3000)
    result = filter_hotels([a, b, c, d], intent)
    assert result == [a]


def test_exact_rating_boundary_passes():
    """A hotel rated exactly at the minimum must pass (inclusive)."""
    hotel = _hotel("A", 4.5, 1000)
    intent = _intent(minimum_hotel_rating=4.5)
    result = filter_hotels([hotel], intent)
    assert result == [hotel]


def test_exact_price_boundary_passes():
    """A hotel priced exactly at the maximum must pass (inclusive)."""
    hotel = _hotel("A", 4.0, 3000)
    intent = _intent(max_hotel_price=3000)
    result = filter_hotels([hotel], intent)
    assert result == [hotel]


def test_no_hotel_satisfies_constraint_returns_empty_list():
    """When nothing qualifies, return [] - never relax the constraint
    or substitute a close match."""
    hotels = [_hotel("A", 4.8, 1000), _hotel("B", 4.6, 1000), _hotel("C", 4.4, 1000)]
    intent = _intent(minimum_hotel_rating=5.0)
    result = filter_hotels(hotels, intent)
    assert result == []


def test_only_rating_constraint_active():
    """With max_hotel_price None, price must never be checked."""
    a = _hotel("A", 4.6, 100000)  # would fail any sane price cap, but none is set
    b = _hotel("B", 4.2, 100)
    intent = _intent(minimum_hotel_rating=4.5, max_hotel_price=None)
    result = filter_hotels([a, b], intent)
    assert result == [a]


def test_only_price_constraint_active():
    """With minimum_hotel_rating None, rating must never be checked."""
    a = _hotel("A", 1.0, 1000)  # very low rating, but no rating constraint set
    b = _hotel("B", 1.0, 5000)
    intent = _intent(minimum_hotel_rating=None, max_hotel_price=3000)
    result = filter_hotels([a, b], intent)
    assert result == [a]


def test_original_hotel_objects_are_not_mutated():
    """filter_hotels must not modify hotel fields - only select which
    hotels are included in the output list."""
    hotel = _hotel("A", 4.5, 3000)
    intent = _intent(minimum_hotel_rating=4.5, max_hotel_price=3000)

    filter_hotels([hotel], intent)

    assert hotel.user_rating == 4.5
    assert hotel.price_per_night == 3000
    


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v"]))