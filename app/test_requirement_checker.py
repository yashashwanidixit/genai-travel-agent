"""
Deterministic unit tests for app/orchestration/requirement_checker.py.

No Ollama/LLM calls here.
"""

from app.models.intent import ExtractedSlots, IntentCategory, TravelIntent
from app.orchestration.requirement_checker import check_requirements, is_ready


def _make_intent(category: IntentCategory, **slot_values) -> TravelIntent:
    return TravelIntent(
        raw_query="test query",
        primary_category=category,
        slots=ExtractedSlots(**slot_values),
        missing_slots=["this-should-be-overwritten"],
    )


def test_hotel_with_destination_has_no_missing_fields():
    """A hotel search with a destination present is ready - no hard
    requirement is missing."""
    intent = _make_intent(IntentCategory.HOTEL_SEARCH, destination="Whitefield")
    checked = check_requirements(intent)
    assert checked.missing_slots == []
    assert is_ready(checked)


def test_hotel_without_destination_flags_destination():
    """A hotel search with no destination and no meeting_location
    flags 'destination' as missing."""
    intent = _make_intent(IntentCategory.HOTEL_SEARCH)
    checked = check_requirements(intent)
    assert checked.missing_slots == ["destination"]
    assert not is_ready(checked)


def test_hotel_meeting_location_satisfies_requirement():
    """A meeting_location can stand in for a destination for the hard
    requirement check."""
    intent = _make_intent(IntentCategory.HOTEL_SEARCH, meeting_location="Whitefield")
    checked = check_requirements(intent)
    assert checked.missing_slots == []


def test_ride_with_origin_and_destination_has_no_missing_fields():
    """A ride search with both origin and destination is ready."""
    intent = _make_intent(
        IntentCategory.RIDE_SEARCH, origin="Bangalore Airport", destination="Whitefield"
    )
    checked = check_requirements(intent)
    assert checked.missing_slots == []
    assert is_ready(checked)


def test_ride_without_origin_flags_origin():
    """A ride search missing origin flags 'origin' as missing."""
    intent = _make_intent(IntentCategory.RIDE_SEARCH, destination="Whitefield")
    checked = check_requirements(intent)
    assert "origin" in checked.missing_slots


def test_ride_without_destination_flags_destination():
    """A ride search missing destination flags 'destination' as missing."""
    intent = _make_intent(IntentCategory.RIDE_SEARCH, origin="Bangalore Airport")
    checked = check_requirements(intent)
    assert "destination" in checked.missing_slots


def test_ride_missing_both_flags_both_in_order():
    """When both are missing, origin is listed first, driving the
    clarification order (pickup asked before drop-off)."""
    intent = _make_intent(IntentCategory.RIDE_SEARCH)
    checked = check_requirements(intent)
    assert checked.missing_slots == ["origin", "destination"]


def test_optional_hotel_fields_do_not_block_readiness():
    """Optional fields (adults, rooms, rating) being None must NOT be
    treated as missing hard requirements."""
    intent = _make_intent(
        IntentCategory.HOTEL_SEARCH,
        destination="Whitefield",
        number_of_adults=None,
        number_of_rooms=None,
        minimum_hotel_rating=None,
    )
    checked = check_requirements(intent)
    assert checked.missing_slots == []
    assert is_ready(checked)


def test_llm_provided_missing_slots_are_overwritten():
    """The requirement checker is the single source of truth: any
    incoming missing_slots value is fully overwritten."""
    intent = _make_intent(IntentCategory.HOTEL_SEARCH, destination="Whitefield")
    assert intent.missing_slots == ["this-should-be-overwritten"]
    checked = check_requirements(intent)
    assert checked.missing_slots == []


if __name__ == "__main__":
    import sys
    import pytest

    sys.exit(pytest.main([__file__, "-v"]))