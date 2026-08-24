"""
Unit tests for DistanceCalculator.

These tests test ONLY the deterministic distance-calculation service.

They do NOT test:
- LocationResolver
- IntentAgent
- Ollama
- HotelProvider
- GraphHopper
- recommendation scoring

The current implementation uses Haversine distance.
"""

import pytest

from app.models.hotel import Hotel
from app.models.hotel_context import HotelContext
from app.models.location import ResolvedLocation
from app.services.distance_calculator import (
    DistanceCalculationError,
    DistanceCalculator,
)


@pytest.fixture
def calculator() -> DistanceCalculator:
    return DistanceCalculator()


def _hotel(
    hotel_id: str = "hotel-1",
    latitude: float | None = 12.9716,
    longitude: float | None = 77.5946,
) -> Hotel:
    """Create a minimal valid Hotel for distance tests."""

    return Hotel(
        id=hotel_id,
        name="Test Hotel",
        city="Bangalore",
        address="Test Address",
        star_rating=4,
        user_rating=4.5,
        price_per_night=3000,
        latitude=latitude,
        longitude=longitude,
    )


def _location(
    name: str = "Test Meeting Location",
    latitude: float = 12.9716,
    longitude: float = 77.5946,
) -> ResolvedLocation:
    """Create a test reference location."""

    return ResolvedLocation(
        name=name,
        latitude=latitude,
        longitude=longitude,
    )


# ============================================================================
# 1. NO REFERENCE LOCATION
# ============================================================================


def test_no_reference_location_returns_none_distance(
    calculator: DistanceCalculator,
):
    """
    If the user did not provide a meeting/reference location, distance
    cannot be calculated.

    The hotel should still be returned inside HotelContext.
    """

    hotel = _hotel()

    contexts = calculator.calculate(
        reference_location=None,
        hotels=[hotel],
    )

    assert len(contexts) == 1
    assert isinstance(contexts[0], HotelContext)

    assert contexts[0].hotel is hotel
    assert contexts[0].distance_km is None


# ============================================================================
# 2. SAME LOCATION
# ============================================================================


def test_same_coordinates_have_zero_distance(
    calculator: DistanceCalculator,
):
    """
    A hotel at exactly the same coordinates as the reference location
    should have distance 0 km.
    """

    location = _location(
        latitude=12.9716,
        longitude=77.5946,
    )

    hotel = _hotel(
        latitude=12.9716,
        longitude=77.5946,
    )

    contexts = calculator.calculate(
        reference_location=location,
        hotels=[hotel],
    )

    assert len(contexts) == 1
    assert contexts[0].distance_km == pytest.approx(0.0)


# ============================================================================
# 3. KNOWN DISTANCE
# ============================================================================


def test_known_coordinates_produce_expected_distance(
    calculator: DistanceCalculator,
):
    """
    Two known coordinates should produce approximately the expected
    great-circle distance.

    This is a Haversine distance test, not a road-distance test.
    """

    # Bangalore city center-ish
    location = _location(
        latitude=12.9716,
        longitude=77.5946,
    )

    # Another nearby point.
    hotel = _hotel(
        latitude=12.9352,
        longitude=77.6245,
    )

    contexts = calculator.calculate(
        reference_location=location,
        hotels=[hotel],
    )

    assert contexts[0].distance_km == pytest.approx(
        5.0,
        abs=0.5,
    )


# ============================================================================
# 4. MULTIPLE HOTELS
# ============================================================================


def test_multiple_hotels_produce_multiple_contexts(
    calculator: DistanceCalculator,
):
    """
    Every input hotel should produce exactly one HotelContext.
    """

    location = _location()

    hotels = [
        _hotel(
            hotel_id="hotel-1",
            latitude=12.9716,
            longitude=77.5946,
        ),
        _hotel(
            hotel_id="hotel-2",
            latitude=12.9750,
            longitude=77.6000,
        ),
        _hotel(
            hotel_id="hotel-3",
            latitude=12.9600,
            longitude=77.5800,
        ),
    ]

    contexts = calculator.calculate(
        reference_location=location,
        hotels=hotels,
    )

    assert len(contexts) == 3

    assert [context.hotel.id for context in contexts] == [
        "hotel-1",
        "hotel-2",
        "hotel-3",
    ]


# ============================================================================
# 5. DISTANCE ORDER
# ============================================================================


def test_closer_hotel_has_smaller_distance(
    calculator: DistanceCalculator,
):
    """
    If one hotel is geographically closer to the reference point than
    another, its Haversine distance should be smaller.
    """

    location = _location(
        latitude=12.9716,
        longitude=77.5946,
    )

    close_hotel = _hotel(
        hotel_id="close",
        latitude=12.9720,
        longitude=77.5950,
    )

    far_hotel = _hotel(
        hotel_id="far",
        latitude=13.0000,
        longitude=77.6500,
    )

    contexts = calculator.calculate(
        reference_location=location,
        hotels=[close_hotel, far_hotel],
    )

    close_distance = contexts[0].distance_km
    far_distance = contexts[1].distance_km

    assert close_distance is not None
    assert far_distance is not None

    assert close_distance < far_distance


# ============================================================================
# 6. MISSING HOTEL LATITUDE
# ============================================================================


def test_missing_hotel_latitude_raises_error(
    calculator: DistanceCalculator,
):
    """
    A hotel without latitude cannot have its distance calculated.

    The calculator must fail explicitly rather than inventing a coordinate.
    """

    hotel = _hotel(
        latitude=None,
        longitude=77.5946,
    )

    with pytest.raises(DistanceCalculationError):
        calculator.calculate(
            reference_location=_location(),
            hotels=[hotel],
        )


# ============================================================================
# 7. MISSING HOTEL LONGITUDE
# ============================================================================


def test_missing_hotel_longitude_raises_error(
    calculator: DistanceCalculator,
):
    """
    A hotel without longitude cannot have its distance calculated.
    """

    hotel = _hotel(
        latitude=12.9716,
        longitude=None,
    )

    with pytest.raises(DistanceCalculationError):
        calculator.calculate(
            reference_location=_location(),
            hotels=[hotel],
        )


# ============================================================================
# 8. INVALID REFERENCE LATITUDE
# ============================================================================


def test_invalid_reference_latitude_raises_error(
    calculator: DistanceCalculator,
):
    """
    Latitude must be between -90 and +90 degrees.
    """

    location = _location(
        latitude=100.0,
        longitude=77.5946,
    )

    hotel = _hotel()

    with pytest.raises(DistanceCalculationError):
        calculator.calculate(
            reference_location=location,
            hotels=[hotel],
        )


# ============================================================================
# 9. INVALID REFERENCE LONGITUDE
# ============================================================================


def test_invalid_reference_longitude_raises_error(
    calculator: DistanceCalculator,
):
    """
    Longitude must be between -180 and +180 degrees.
    """

    location = _location(
        latitude=12.9716,
        longitude=200.0,
    )

    hotel = _hotel()

    with pytest.raises(DistanceCalculationError):
        calculator.calculate(
            reference_location=location,
            hotels=[hotel],
        )


# ============================================================================
# 10. INVALID HOTEL LATITUDE
# ============================================================================


def test_invalid_hotel_latitude_raises_error(
    calculator: DistanceCalculator,
):
    """
    Invalid hotel coordinates must not be silently accepted.
    """

    hotel = _hotel(
        latitude=100.0,
        longitude=77.5946,
    )

    with pytest.raises(DistanceCalculationError):
        calculator.calculate(
            reference_location=_location(),
            hotels=[hotel],
        )


# ============================================================================
# 11. INVALID HOTEL LONGITUDE
# ============================================================================


def test_invalid_hotel_longitude_raises_error(
    calculator: DistanceCalculator,
):
    """
    Invalid hotel longitude must not be silently accepted.
    """

    hotel = _hotel(
        latitude=12.9716,
        longitude=200.0,
    )

    with pytest.raises(DistanceCalculationError):
        calculator.calculate(
            reference_location=_location(),
            hotels=[hotel],
        )


# ============================================================================
# 12. ORIGINAL HOTEL IS NOT MUTATED
# ============================================================================


def test_original_hotel_is_not_mutated(
    calculator: DistanceCalculator,
):
    """
    Distance calculation must not add or modify fields on the original
    Hotel object.
    """

    hotel = _hotel()

    original_latitude = hotel.latitude
    original_longitude = hotel.longitude
    original_price = hotel.price_per_night
    original_rating = hotel.user_rating

    contexts = calculator.calculate(
        reference_location=_location(),
        hotels=[hotel],
    )

    assert hotel.latitude == original_latitude
    assert hotel.longitude == original_longitude
    assert hotel.price_per_night == original_price
    assert hotel.user_rating == original_rating

    assert contexts[0].hotel is hotel


# ============================================================================
# 13. OUTPUT ORDER IS PRESERVED
# ============================================================================


def test_output_order_matches_input_order(
    calculator: DistanceCalculator,
):
    """
    DistanceCalculator calculates distances but does NOT rank or sort hotels.

    Recommendation/ranking belongs to a later stage.
    """

    hotels = [
        _hotel(
            hotel_id="hotel-A",
            latitude=12.9800,
            longitude=77.6000,
        ),
        _hotel(
            hotel_id="hotel-B",
            latitude=12.9700,
            longitude=77.5900,
        ),
        _hotel(
            hotel_id="hotel-C",
            latitude=12.9600,
            longitude=77.5800,
        ),
    ]

    contexts = calculator.calculate(
        reference_location=_location(),
        hotels=hotels,
    )

    assert [context.hotel.id for context in contexts] == [
        "hotel-A",
        "hotel-B",
        "hotel-C",
    ]


# ============================================================================
# 14. EMPTY HOTEL LIST
# ============================================================================


def test_empty_hotel_list_returns_empty_list(
    calculator: DistanceCalculator,
):
    """
    No hotels means there is nothing to calculate.
    """

    contexts = calculator.calculate(
        reference_location=_location(),
        hotels=[],
    )

    assert contexts == []